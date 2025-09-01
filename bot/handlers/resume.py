import logging
import json
from telegram import Update
from telegram.ext import (
    ContextTypes,
    MessageHandler,
    filters,
)

from db.database import get_db
from db import crud
from bot import messages, keyboards
from ai.client import get_ai_client
from scraper.hh_scraper import scrape_hh_url
from bot.file_utils import save_text_to_file
from bot.handlers.states import AWAITING_RESUME_UPLOAD, MAIN_MENU
from bot.handlers.main_menu_helpers import show_main_menu


logger = logging.getLogger(__name__)


# --- Вспомогательная функция для обработки текста резюме ---
async def process_resume_text(update: Update, context: ContextTypes.DEFAULT_TYPE, text: str, source: str) -> int:
    """
    Общая логика для обработки и валидации текста резюме.
    """
    chat_id = update.effective_chat.id
    message = update.effective_message

    await message.reply_text(messages.RESUME_PROCESSING)

    db_session_gen = get_db()
    db = next(db_session_gen)
    try:
        user = crud.get_or_create_user(db, chat_id=chat_id)

        # 1. Валидация текста с помощью AI
        ai_client = get_ai_client()
        response_data = ai_client.verify_resume(text)

        # 2. Логирование использования AI
        usage = response_data.get("usage", {})
        crud.create_ai_usage_log(
            db=db,
            user_id=user.id,
            prompt_tokens=usage.get("prompt_tokens", 0),
            completion_tokens=usage.get("completion_tokens", 0),
            total_tokens=usage.get("total_tokens", 0),
            cost=usage.get("cost", 0.0),
            action="verify_resume",
        )

        # 3. Обработка и парсинг ответа
        response_text = response_data.get("text", "{}")
        if not response_text or "error" in response_data:
            logger.error(f"AI verification failed for user {chat_id}. Response: {response_data}")
            await message.reply_text(messages.RESUME_VERIFICATION_FAILED)
            await message.reply_text(messages.ASK_FOR_RESUME, reply_markup=keyboards.cancel_keyboard())
            return AWAITING_RESUME_UPLOAD
        try:
            # Проверяем, является ли ответ строкой, которую нужно парсить, или уже объектом
            if isinstance(response_text, str):
                # Очистка от markdown-блоков
                response_text = response_text.strip()
                if response_text.startswith("```json"):
                    response_text = response_text[7:-4].strip()
                elif response_text.startswith("```"):
                    response_text = response_text[3:-3].strip()
                response_json = json.loads(response_text)
            else:
                # Если это не строка, предполагаем, что это уже готовый dict
                response_json = response_text

            is_resume = response_json.get("is_resume", False)
            resume_title = response_json.get("title")
        except (json.JSONDecodeError, AttributeError, KeyError, IndexError, TypeError) as e:
            is_resume = False
            resume_title = None
            logger.error(f"Failed to parse AI response: {response_data}. Error: {e}")


        if not is_resume:
            await message.reply_text(messages.RESUME_VERIFICATION_FAILED)
            await message.reply_text(messages.ASK_FOR_RESUME, reply_markup=keyboards.cancel_keyboard())
            return AWAITING_RESUME_UPLOAD

        # 4. Сохранение файла
        file_path = save_text_to_file(text, "resumes")
        if not file_path:
            await message.reply_text(messages.ERROR_MESSAGE)
            return AWAITING_RESUME_UPLOAD

        # 5. Сохранение резюме в БД
        crud.create_resume(db, user_id=user.id, file_path=file_path, source=source, title=resume_title)
        await message.reply_text(messages.RESUME_UPLOADED_SUCCESS)

        # 6. Переход в главное меню
        await show_main_menu(update, context)
        return MAIN_MENU
    finally:
        db.close()


# --- Обработчики состояния AWAITING_RESUME_UPLOAD ---
async def handle_resume_file(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Обрабатывает резюме, загруженное как .txt файл."""
    document = update.message.document
    if not document or not document.file_name.endswith(".txt"):
        await update.message.reply_text(messages.RESUME_INVALID_FORMAT, reply_markup=keyboards.cancel_keyboard())
        return AWAITING_RESUME_UPLOAD

    try:
        file = await document.get_file()
        file_content_bytes = await file.download_as_bytearray()
    except Exception as e:
        logger.error(f"Ошибка при загрузке файла резюме: {e}", exc_info=True)
        await update.message.reply_text(messages.FILE_DOWNLOAD_ERROR, reply_markup=keyboards.cancel_keyboard())
        return AWAITING_RESUME_UPLOAD

    try:
        resume_text = file_content_bytes.decode("utf-8")
    except UnicodeDecodeError:
        await update.message.reply_text(messages.FILE_DECODE_ERROR, reply_markup=keyboards.cancel_keyboard())
        return AWAITING_RESUME_UPLOAD

    return await process_resume_text(update, context, resume_text, source=document.file_name)


async def handle_resume_url(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Обрабатывает ссылку на резюме."""
    url = update.message.text
    # Простая проверка на наличие домена hh.ru в тексте
    if "hh.ru" not in url:
        await update.message.reply_text(messages.RESUME_INVALID_FORMAT, reply_markup=keyboards.cancel_keyboard())
        return AWAITING_RESUME_UPLOAD

    resume_text = scrape_hh_url(url)
    if not resume_text:
        await update.message.reply_text(messages.ERROR_MESSAGE, reply_markup=keyboards.cancel_keyboard())
        return AWAITING_RESUME_UPLOAD

    return await process_resume_text(update, context, resume_text, source=url)


async def handle_invalid_resume_input(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Обрабатывает некорректный ввод в состоянии ожидания резюме."""
    await update.message.reply_text(messages.RESUME_INVALID_FORMAT, reply_markup=keyboards.cancel_keyboard())
    return AWAITING_RESUME_UPLOAD


# Фильтры для обработчиков
resume_file_handler = MessageHandler(filters.Document.TXT, handle_resume_file)
resume_url_handler = MessageHandler(filters.TEXT & ~filters.COMMAND & filters.Entity("url"), handle_resume_url)
fallback_resume_handler = MessageHandler(filters.TEXT & ~filters.COMMAND, handle_invalid_resume_input)

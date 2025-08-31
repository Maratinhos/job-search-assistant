import logging
import re
import json
from telegram import Update
from telegram.ext import (
    ContextTypes,
    MessageHandler,
    filters,
)

from .resume import MAIN_MENU, AWAITING_VACANCY_UPLOAD
from .main_menu_helpers import show_main_menu
from bot import messages, keyboards
from db import crud
from db.database import get_db
from ai.client import get_ai_client
from scraper.hh_scraper import scrape_hh_url
from bot.file_utils import save_text_to_file

logger = logging.getLogger(__name__)


async def process_vacancy_text(update: Update, context: ContextTypes.DEFAULT_TYPE, text: str, source: str) -> int:
    """
    Общая логика для обработки и валидации текста вакансии.
    """
    chat_id = update.effective_chat.id
    message = update.effective_message

    await message.reply_text(messages.VACANCY_PROCESSING)

    db_session_gen = get_db()
    db = next(db_session_gen)
    try:
        user = crud.get_or_create_user(db, chat_id=chat_id)

        # 1. Валидация текста с помощью AI
        ai_client = get_ai_client()
        response = ai_client.verify_vacancy(text)

        # 2. Логирование использования AI
        usage = response.get("usage", {})
        crud.create_ai_usage_log(
            db,
            user_id=user.id,
            prompt_tokens=usage.get("prompt_tokens", 0),
            completion_tokens=usage.get("completion_tokens", 0),
            total_tokens=usage.get("total_tokens", 0),
        )

        try:
            # Извлекаем основной контент, который может быть строкой или уже dict
            content = response.get("text", "{}")

            # Проверяем, является ли ответ строкой, которую нужно парсить
            if isinstance(content, str):
                # Очистка от markdown-блоков
                content = content.strip()
                if content.startswith("```json"):
                    content = content[7:-4].strip()
                elif content.startswith("```"):
                    content = content[3:-3].strip()
                response_json = json.loads(content)
            else:
                # Если это не строка, предполагаем, что это уже готовый dict
                response_json = content

            is_vacancy = response_json.get("is_vacancy", False)
            title = response_json.get("title")

        except (json.JSONDecodeError, AttributeError, TypeError) as e:
            logger.error(f"Failed to parse AI response for vacancy: {response}. Error: {e}")
            is_vacancy = False
            title = None

        if not is_vacancy:
            await message.reply_text(messages.VACANCY_VERIFICATION_FAILED)
            await message.reply_text(messages.ASK_FOR_VACANCY, reply_markup=keyboards.cancel_keyboard())
            return AWAITING_VACANCY_UPLOAD

        # 3. Сохранение файла
        file_path = save_text_to_file(text, "vacancies")
        if not file_path:
            await message.reply_text(messages.ERROR_MESSAGE)
            return AWAITING_VACANCY_UPLOAD

        # 4. Сохранение вакансии в БД
        vacancy = crud.create_vacancy(db, user_id=user.id, title=title, file_path=file_path, source=source)

        # Сохраняем ID новой вакансии как выбранной по умолчанию
        context.user_data['selected_vacancy_id'] = vacancy.id

        await message.reply_text(messages.VACANCY_UPLOADED_SUCCESS)

        # 5. Переход в главное меню
        await show_main_menu(update, context)
        return MAIN_MENU
    finally:
        db.close()

async def handle_vacancy_file(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Обрабатывает вакансию, загруженную как .txt файл."""
    document = update.message.document
    if not document or not document.file_name.endswith(".txt"):
        await update.message.reply_text(messages.VACANCY_INVALID_FORMAT, reply_markup=keyboards.cancel_keyboard())
        return AWAITING_VACANCY_UPLOAD

    file = await document.get_file()
    file_content_bytes = await file.download_as_bytearray()

    try:
        vacancy_text = file_content_bytes.decode("utf-8")
    except UnicodeDecodeError:
        await update.message.reply_text("Ошибка кодировки файла. Пожалуйста, используйте UTF-8.", reply_markup=keyboards.cancel_keyboard())
        return AWAITING_VACANCY_UPLOAD

    return await process_vacancy_text(update, context, vacancy_text, source=document.file_name)


async def handle_vacancy_url(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Обрабатывает ссылку на вакансию."""
    url = update.message.text
    if "hh.ru" not in url:
        await update.message.reply_text(messages.VACANCY_INVALID_FORMAT, reply_markup=keyboards.cancel_keyboard())
        return AWAITING_VACANCY_UPLOAD

    vacancy_text = scrape_hh_url(url)
    if not vacancy_text:
        await update.message.reply_text(messages.ERROR_MESSAGE, reply_markup=keyboards.cancel_keyboard())
        return AWAITING_VACANCY_UPLOAD

    return await process_vacancy_text(update, context, vacancy_text, source=url)


async def handle_invalid_vacancy_input(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Обрабатывает некорректный ввод в состоянии ожидания вакансии."""
    await update.message.reply_text(messages.VACANCY_INVALID_FORMAT, reply_markup=keyboards.cancel_keyboard())
    return AWAITING_VACANCY_UPLOAD

# --- Экспортируемые обработчики ---
vacancy_file_handler = MessageHandler(filters.Document.TXT, handle_vacancy_file)
vacancy_url_handler = MessageHandler(filters.TEXT & ~filters.COMMAND & filters.Entity("url"), handle_vacancy_url)
fallback_vacancy_handler = MessageHandler(filters.TEXT & ~filters.COMMAND, handle_invalid_vacancy_input)

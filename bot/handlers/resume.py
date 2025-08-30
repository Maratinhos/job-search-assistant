import logging
from telegram import Update
from telegram.ext import (
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    filters,
)

from db.database import get_db
from db import crud
from bot import messages, keyboards
from ai.client import ai_client
from scraper.hh_scraper import scrape_hh_url

logger = logging.getLogger(__name__)

# Определяем состояния для ConversationHandler
(
    AWAITING_RESUME_UPLOAD,
    AWAITING_VACANCY_UPLOAD,
    MAIN_MENU
) = range(3)

# --- Вспомогательная функция для обработки текста резюме ---
async def process_resume_text(update: Update, context: ContextTypes.DEFAULT_TYPE, text: str, source: str) -> int:
    """
    Общая логика для обработки и валидации текста резюме.
    """
    chat_id = update.effective_chat.id
    message = update.effective_message

    await message.reply_text(messages.RESUME_PROCESSING)

    # 1. Валидация текста с помощью AI
    if not ai_client.verify_resume(text):
        await message.reply_text(messages.RESUME_VERIFICATION_FAILED)
        await message.reply_text(messages.ASK_FOR_RESUME, reply_markup=keyboards.cancel_keyboard())
        return AWAITING_RESUME_UPLOAD  # Остаемся в том же состоянии

    # 2. Сохранение резюме в БД
    db_session_gen = get_db()
    db = next(db_session_gen)
    try:
        user = crud.get_or_create_user(db, chat_id=chat_id)
        crud.create_resume(db, user_id=user.id, text=text, source=source)
        await message.reply_text(messages.RESUME_UPLOADED_SUCCESS)

        # 3. Переход к следующему шагу - загрузке вакансии
        await message.reply_text(messages.ASK_FOR_VACANCY, reply_markup=keyboards.cancel_keyboard())
        return AWAITING_VACANCY_UPLOAD
    finally:
        db.close()


# --- Обработчики состояния AWAITING_RESUME_UPLOAD ---
async def handle_resume_file(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Обрабатывает резюме, загруженное как .txt файл."""
    document = update.message.document
    if not document or not document.file_name.endswith(".txt"):
        await update.message.reply_text(messages.RESUME_INVALID_FORMAT, reply_markup=keyboards.cancel_keyboard())
        return AWAITING_RESUME_UPLOAD

    file = await document.get_file()
    file_content_bytes = await file.download_as_bytearray()

    try:
        resume_text = file_content_bytes.decode("utf-8")
    except UnicodeDecodeError:
        await update.message.reply_text("Ошибка кодировки файла. Пожалуйста, используйте UTF-8.", reply_markup=keyboards.cancel_keyboard())
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

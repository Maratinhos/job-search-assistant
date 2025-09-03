import logging
from telegram import Update
from telegram.ext import (
    ContextTypes,
    MessageHandler,
    filters,
)

from bot.handlers.states import MAIN_MENU, AWAITING_VACANCY_UPLOAD
from .main_menu_helpers import show_main_menu
from bot import messages, keyboards
from db import crud
from db.database import get_db
from scraper.hh_scraper import scrape_hh_url
from services.document_service import process_document

logger = logging.getLogger(__name__)


async def _process_and_reply(update: Update, context: ContextTypes.DEFAULT_TYPE, text: str, source: str) -> int:
    """
    Внутренняя функция для вызова сервиса обработки и отправки ответа пользователю.
    """
    chat_id = update.effective_chat.id
    message = update.effective_message
    await message.reply_text(messages.VACANCY_PROCESSING)

    db_session_gen = get_db()
    db = next(db_session_gen)
    try:
        user = crud.get_or_create_user(db, chat_id=chat_id)
        success, _ = await process_document(
            update=update,
            context=context,
            db=db,
            user_id=user.id,
            text=text,
            source=source,
            doc_type="vacancy",
        )

        if success:
            await message.reply_text(messages.VACANCY_UPLOADED_SUCCESS)
            await show_main_menu(update, context)
            return MAIN_MENU
        else:
            await message.reply_text(messages.VACANCY_VERIFICATION_FAILED)
            await message.reply_text(
                messages.ASK_FOR_VACANCY,
                reply_markup=keyboards.cancel_keyboard(),
            )
            return AWAITING_VACANCY_UPLOAD
    finally:
        db.close()


async def handle_vacancy_file(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Обрабатывает вакансию, загруженную как .txt файл."""
    document = update.message.document
    if not document or not document.file_name.endswith(".txt"):
        await update.message.reply_text(
            messages.VACANCY_INVALID_FORMAT,
            reply_markup=keyboards.cancel_keyboard(),
        )
        return AWAITING_VACANCY_UPLOAD

    try:
        file = await document.get_file()
        file_content_bytes = await file.download_as_bytearray()
    except Exception as e:
        logger.error(f"Ошибка при загрузке файла вакансии: {e}", exc_info=True)
        await update.message.reply_text(
            messages.FILE_DOWNLOAD_ERROR,
            reply_markup=keyboards.cancel_keyboard(),
        )
        return AWAITING_VACANCY_UPLOAD

    try:
        vacancy_text = file_content_bytes.decode("utf-8")
    except UnicodeDecodeError:
        await update.message.reply_text(
            messages.FILE_DECODE_ERROR,
            reply_markup=keyboards.cancel_keyboard(),
        )
        return AWAITING_VACANCY_UPLOAD

    return await _process_and_reply(update, context, vacancy_text, source=document.file_name)


async def handle_vacancy_url(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Обрабатывает ссылку на вакансию."""
    url = update.message.text
    if "hh.ru" not in url:
        await update.message.reply_text(
            messages.VACANCY_INVALID_FORMAT,
            reply_markup=keyboards.cancel_keyboard(),
        )
        return AWAITING_VACANCY_UPLOAD

    vacancy_text = scrape_hh_url(url)
    if not vacancy_text:
        await update.message.reply_text(
            messages.ERROR_MESSAGE,
            reply_markup=keyboards.cancel_keyboard(),
        )
        return AWAITING_VACANCY_UPLOAD

    return await _process_and_reply(update, context, vacancy_text, source=url)


async def handle_invalid_vacancy_input(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Обрабатывает некорректный ввод в состоянии ожидания вакансии."""
    await update.message.reply_text(
        messages.VACANCY_INVALID_FORMAT,
        reply_markup=keyboards.cancel_keyboard(),
    )
    return AWAITING_VACANCY_UPLOAD

# --- Экспортируемые обработчики ---
vacancy_file_handler = MessageHandler(filters.Document.TXT, handle_vacancy_file)
vacancy_url_handler = MessageHandler(filters.TEXT & ~filters.COMMAND & filters.Entity("url"), handle_vacancy_url)
fallback_vacancy_handler = MessageHandler(filters.TEXT & ~filters.COMMAND, handle_invalid_vacancy_input)

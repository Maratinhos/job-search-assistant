import logging
from telegram import Update
from telegram.ext import (
    ContextTypes,
    MessageHandler,
    filters,
)

from db.database import get_db
from db import crud
from bot import messages, keyboards
from scraper.hh_scraper import scrape_hh_url
from bot.handlers.states import AWAITING_RESUME_UPLOAD, MAIN_MENU, AWAITING_VACANCY_UPLOAD
from bot.handlers.main_menu_helpers import show_main_menu
from services.document_service import process_document

logger = logging.getLogger(__name__)


async def _process_and_reply(update: Update, context: ContextTypes.DEFAULT_TYPE, text: str, source: str) -> int:
    """
    Внутренняя функция для вызова сервиса обработки и отправки ответа пользователю.
    """
    chat_id = update.effective_chat.id
    message = update.effective_message
    await message.reply_text(messages.RESUME_PROCESSING)

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
            doc_type="resume",
        )

        if success:
            await message.reply_text(messages.RESUME_UPLOADED_SUCCESS)

            # После успешной загрузки резюме, проверяем наличие вакансий
            vacancies = crud.get_user_vacancies(db, user_id=user.id)
            if not vacancies:
                await message.reply_text(
                    messages.ASK_FOR_VACANCY,
                    reply_markup=keyboards.cancel_keyboard(),
                )
                return AWAITING_VACANCY_UPLOAD
            else:
                await show_main_menu(update, context)
                return MAIN_MENU
        else:
            await message.reply_text(messages.RESUME_VERIFICATION_FAILED)
            await message.reply_text(
                messages.ASK_FOR_RESUME,
                reply_markup=keyboards.cancel_keyboard(),
            )
            return AWAITING_RESUME_UPLOAD
    finally:
        db.close()


# --- Обработчики состояния AWAITING_RESUME_UPLOAD ---
async def handle_resume_file(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Обрабатывает резюме, загруженное как .txt файл."""
    document = update.message.document
    if not document or not document.file_name.endswith(".txt"):
        await update.message.reply_text(
            messages.RESUME_INVALID_FORMAT,
            reply_markup=keyboards.cancel_keyboard(),
        )
        return AWAITING_RESUME_UPLOAD

    try:
        file = await document.get_file()
        file_content_bytes = await file.download_as_bytearray()
    except Exception as e:
        logger.error(f"Ошибка при загрузке файла резюме: {e}", exc_info=True)
        await update.message.reply_text(
            messages.FILE_DOWNLOAD_ERROR,
            reply_markup=keyboards.cancel_keyboard(),
        )
        return AWAITING_RESUME_UPLOAD

    try:
        resume_text = file_content_bytes.decode("utf-8")
    except UnicodeDecodeError:
        await update.message.reply_text(
            messages.FILE_DECODE_ERROR,
            reply_markup=keyboards.cancel_keyboard(),
        )
        return AWAITING_RESUME_UPLOAD

    return await _process_and_reply(update, context, resume_text, source=document.file_name)


async def handle_resume_url(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Обрабатывает ссылку на резюме."""
    url = update.message.text
    # Простая проверка на наличие домена hh.ru в тексте
    if "hh.ru" not in url:
        await update.message.reply_text(
            messages.RESUME_INVALID_FORMAT,
            reply_markup=keyboards.cancel_keyboard(),
        )
        return AWAITING_RESUME_UPLOAD

    resume_text = scrape_hh_url(url)
    if not resume_text:
        await update.message.reply_text(
            messages.ERROR_MESSAGE,
            reply_markup=keyboards.cancel_keyboard(),
        )
        return AWAITING_RESUME_UPLOAD

    return await _process_and_reply(update, context, resume_text, source=url)


async def handle_invalid_resume_input(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Обрабатывает некорректный ввод в состоянии ожидания резюме."""
    await update.message.reply_text(
        messages.RESUME_INVALID_FORMAT,
        reply_markup=keyboards.cancel_keyboard(),
    )
    return AWAITING_RESUME_UPLOAD


# Фильтры для обработчиков
resume_file_handler = MessageHandler(filters.Document.TXT, handle_resume_file)
resume_url_handler = MessageHandler(filters.TEXT & ~filters.COMMAND & filters.Entity("url"), handle_resume_url)
fallback_resume_handler = MessageHandler(filters.TEXT & ~filters.COMMAND, handle_invalid_resume_input)

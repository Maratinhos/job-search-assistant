import logging
from telegram import Update
from telegram.ext import ContextTypes, ConversationHandler

from bot import messages, keyboards
from db import crud
from db.database import get_db
from .resume import MAIN_MENU

logger = logging.getLogger(__name__)


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Отменяет текущий диалог.
    Удаляет клавиатуру и отправляет сообщение об отмене.
    """
    query = update.callback_query
    if query:
        await query.answer()
        try:
            await query.edit_message_text(text=messages.ACTION_CANCELED)
        except Exception:
            # Message might have been deleted or is not editable, just log it
            logger.warning("Could not edit message on cancel, probably already gone.")
    else:
        await update.message.reply_text(text=messages.ACTION_CANCELED, reply_markup=None)

    # Очищаем user_data, чтобы не оставлять мусор от прерванного диалога
    context.user_data.clear()

    logger.info(f"User {update.effective_chat.id} cancelled the conversation.")
    return ConversationHandler.END


async def global_fallback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Обрабатывает любые сообщения, не попавшие в другие обработчики.
    Возвращает пользователя в главное меню.
    """
    chat_id = update.effective_chat.id
    logger.warning(f"User {chat_id} sent an unhandled message: {update.message.text}")

    db_session_gen = get_db()
    db = next(db_session_gen)
    try:
        user = crud.get_or_create_user(db, chat_id=chat_id)
        resumes = crud.get_user_resumes(db, user_id=user.id)
        vacancies = crud.get_user_vacancies(db, user_id=user.id)

        # Для простоты предполагаем, что у пользователя одно резюме
        resume = resumes[0] if resumes else None

        if resume:
            await update.message.reply_text(
                text=messages.GLOBAL_FALLBACK_MESSAGE,
                reply_markup=keyboards.main_menu_keyboard(
                    vacancy_count=len(vacancies),
                    has_resume=bool(resume)
                )
            )
            return MAIN_MENU
        else:
            # Если резюме нет, то и главного меню быть не может.
            # Отправляем приветственное сообщение и просим загрузить резюме.
            await update.message.reply_text(messages.WELCOME_MESSAGE)
            await update.message.reply_text(messages.ASK_FOR_RESUME, reply_markup=keyboards.cancel_keyboard())
            # Возвращаем состояние ожидания резюме
            from .resume import AWAITING_RESUME_UPLOAD
            return AWAITING_RESUME_UPLOAD

    finally:
        db.close()

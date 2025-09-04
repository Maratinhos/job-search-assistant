import logging
from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import (
    ContextTypes,
    ConversationHandler,
    CallbackQueryHandler,
    MessageHandler,
    filters,
)

from bot.handlers.states import AWAITING_SURVEY_ANSWER, MAIN_MENU
from bot.handlers.main_menu_helpers import show_main_menu
from db import crud
from db.database import get_db

logger = logging.getLogger(__name__)


async def start_survey(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Начинает опрос, отправляя вопрос и варианты ответов."""
    query = update.callback_query
    await query.answer()

    db_gen = get_db()
    db = next(db_gen)
    try:
        active_survey = crud.get_active_survey(db)
        if not active_survey:
            await query.edit_message_text("Спасибо, но сейчас нет активных опросов.")
            await show_main_menu(update, context)
            return MAIN_MENU

        context.user_data["active_survey_id"] = active_survey.id
        options = active_survey.options.split(',')
        reply_keyboard = [options]

        await query.message.reply_text(
            f"Опрос: {active_survey.question}",
            reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True, resize_keyboard=True),
        )
        return AWAITING_SURVEY_ANSWER
    finally:
        db.close()


async def handle_survey_answer(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Обрабатывает ответ пользователя на опрос."""
    user_answer = update.message.text
    chat_id = update.effective_chat.id
    survey_id = context.user_data.get("active_survey_id")

    if not survey_id:
        await update.message.reply_text("Произошла ошибка. Попробуйте снова.", reply_markup=ReplyKeyboardRemove())
        await show_main_menu(update, context)
        return MAIN_MENU

    db_gen = get_db()
    db = next(db_gen)
    try:
        user = crud.get_or_create_user(db, chat_id)
        crud.create_survey_answer(db, user_id=user.id, survey_id=survey_id, answer=user_answer)

        await update.message.reply_text("Спасибо за ваш ответ!", reply_markup=ReplyKeyboardRemove())
    finally:
        db.close()

    context.user_data.pop("active_survey_id", None)
    await show_main_menu(update, context)
    return MAIN_MENU


async def cancel_survey(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Отменяет процесс опроса."""
    await update.message.reply_text("Опрос отменен.", reply_markup=ReplyKeyboardRemove())
    context.user_data.pop("active_survey_id", None)
    await show_main_menu(update, context)
    return MAIN_MENU


def survey_conversation_handler() -> ConversationHandler:
    """Создает ConversationHandler для опроса."""
    return ConversationHandler(
        entry_points=[CallbackQueryHandler(start_survey, pattern="^start_survey$")],
        states={
            AWAITING_SURVEY_ANSWER: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_survey_answer)
            ],
        },
        fallbacks=[MessageHandler(filters.COMMAND, cancel_survey)],
        map_to_parent={
            MAIN_MENU: MAIN_MENU,
        },
    )

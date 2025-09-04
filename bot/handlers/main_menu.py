import logging

from telegram.ext import (
    CallbackQueryHandler,
    ConversationHandler,
    MessageHandler,
    filters,
)

from bot.handlers.analysis import (
    analyze_match_handler,
    generate_hr_plan_handler,
    generate_letter_handler,
    generate_tech_plan_handler,
)
from bot.handlers.common import cancel, global_fallback_handler
from bot.handlers.states import MAIN_MENU, UPDATE_RESUME
from bot.handlers.menu import select_vacancy_handler, update_resume_handler
from bot.handlers.vacancy_management import vacancy_upload_handler
from bot.handlers.survey import survey_conversation_handler

logger = logging.getLogger(__name__)


def main_menu_handlers() -> list:
    """
    Возвращает список обработчиков для главного меню.
    """
    return [
        analyze_match_handler,
        generate_letter_handler,
        generate_hr_plan_handler,
        generate_tech_plan_handler,
        update_resume_handler,
        select_vacancy_handler,
        vacancy_upload_handler(),
        survey_conversation_handler(),
    ]

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
from bot.handlers.menu import update_resume_handler
from bot.handlers.vacancy_management import vacancy_handler

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
        vacancy_handler(),
    ]

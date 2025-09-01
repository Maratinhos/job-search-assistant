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


def main_menu_handler() -> ConversationHandler:
    """
    Обработчик для главного меню.
    """
    return ConversationHandler(
        entry_points=[
            # Этот обработчик не имеет своей точки входа,
            # так как в него попадают из других обработчиков
        ],
        states={
            MAIN_MENU: [
                analyze_match_handler,
                generate_letter_handler,
                generate_hr_plan_handler,
                generate_tech_plan_handler,
                update_resume_handler,
                vacancy_handler(),
            ]
        },
        fallbacks=[
            CallbackQueryHandler(cancel, pattern="^cancel_action$"),
            MessageHandler(filters.TEXT & ~filters.COMMAND, global_fallback_handler),
        ],
        per_user=True,
        per_chat=True,
        allow_reentry=True,
        map_to_parent={
            # Позволяет вернуться к этому состоянию из дочерних обработчиков
            MAIN_MENU: MAIN_MENU,
            # Переход в состояние обновления резюме
            UPDATE_RESUME: UPDATE_RESUME,
            # При отмене из дочерних, возвращаемся в главное меню
            ConversationHandler.END: MAIN_MENU,
        },
    )

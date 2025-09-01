import logging
from telegram.ext import (
    CallbackQueryHandler,
    ConversationHandler,
    MessageHandler,
    filters,
)

from bot.handlers.common import cancel, global_fallback_handler
from bot.handlers.states import AWAITING_VACANCY_UPLOAD, MAIN_MENU
from bot.handlers.menu import (
    upload_vacancy_handler,
)
from bot.handlers.vacancy import (
    fallback_vacancy_handler,
    handle_invalid_vacancy_input,
    vacancy_file_handler,
    vacancy_url_handler,
)

logger = logging.getLogger(__name__)


def vacancy_upload_handler() -> ConversationHandler:
    """
    Обработчик для загрузки новой вакансии.
    """
    return ConversationHandler(
        entry_points=[
            upload_vacancy_handler,
        ],
        states={
            AWAITING_VACANCY_UPLOAD: [
                vacancy_file_handler,
                vacancy_url_handler,
                MessageHandler(filters.PHOTO, handle_invalid_vacancy_input),
                fallback_vacancy_handler,
            ],
        },
        fallbacks=[
            CallbackQueryHandler(cancel, pattern="^cancel_action$"),
            MessageHandler(filters.TEXT & ~filters.COMMAND, global_fallback_handler),
        ],
        map_to_parent={
            # После завершения работы с вакансиями, возвращаемся в главное меню
            MAIN_MENU: MAIN_MENU,
            # При отмене, также возвращаемся в главное меню
            ConversationHandler.END: MAIN_MENU,
        },
    )

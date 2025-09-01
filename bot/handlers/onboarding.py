import logging

from telegram.ext import (
    CallbackQueryHandler,
    CommandHandler,
    ConversationHandler,
    MessageHandler,
    filters,
)

from bot.handlers.common import cancel, global_fallback_handler
from bot.handlers.states import AWAITING_RESUME_UPLOAD, MAIN_MENU
from bot.handlers.resume import (
    resume_file_handler,
    resume_url_handler,
    fallback_resume_handler,
    handle_invalid_resume_input,
)
from bot.handlers.start import start

logger = logging.getLogger(__name__)

def onboarding_handler() -> ConversationHandler:
    """
    Обработчик для онбординга нового пользователя, включая загрузку первого резюме.
    """
    return ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            AWAITING_RESUME_UPLOAD: [
                resume_file_handler,
                resume_url_handler,
                MessageHandler(filters.PHOTO, handle_invalid_resume_input),
                fallback_resume_handler,
            ],
        },
        fallbacks=[
            CallbackQueryHandler(cancel, pattern="^cancel_action$"),
            MessageHandler(filters.TEXT & ~filters.COMMAND, global_fallback_handler),
        ],
        per_user=True,
        per_chat=True,
        allow_reentry=True,
        # Точка выхода из онбординга - переход в главное меню
        map_to_parent={
            MAIN_MENU: MAIN_MENU,
        }
    )

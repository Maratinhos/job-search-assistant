import logging
from telegram.ext import (
    Application,
    ConversationHandler,
    CallbackQueryHandler,
    MessageHandler,
    filters,
)

from config import TELEGRAM_BOT_TOKEN
from bot.handlers.common import cancel, global_fallback_handler
from bot.handlers.onboarding import onboarding_handler
from bot.handlers.main_menu import main_menu_handler
from bot.handlers.states import MAIN_MENU, UPDATE_RESUME


logger = logging.getLogger(__name__)


def create_application() -> Application:
    """
    Создает и настраивает экземпляр приложения Telegram с вложенными ConversationHandler.
    """
    if not TELEGRAM_BOT_TOKEN:
        raise ValueError("Токен TELEGRAM_BOT_TOKEN не найден в .env файле!")

    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    # Главный обработчик диалога, который управляет всем состоянием бота
    conv_handler = ConversationHandler(
        entry_points=[onboarding_handler()],
        states={
            MAIN_MENU: [main_menu_handler()],
            UPDATE_RESUME: [onboarding_handler()],
        },
        fallbacks=[
            CallbackQueryHandler(cancel, pattern="^cancel_action$"),
            MessageHandler(filters.TEXT & ~filters.COMMAND, global_fallback_handler),
        ],
        per_user=True,
        per_chat=True,
        allow_reentry=True,
    )

    application.add_handler(conv_handler)

    return application


async def main() -> None:
    """
    Основная асинхронная функция для запуска бота.
    """
    try:
        application = create_application()
        logger.info("Бот запускается...")
        await application.run_polling()
    except Exception as e:
        logger.critical(f"Критическая ошибка при запуске бота: {e}", exc_info=True)

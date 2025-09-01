import logging
from telegram.ext import (
    Application,
    CommandHandler,
    ConversationHandler,
    CallbackQueryHandler,
    MessageHandler,
    filters,
)

from config import TELEGRAM_BOT_TOKEN
from bot.handlers.start import start
from bot.handlers.common import cancel, global_fallback_handler
from bot.handlers.resume import (
    AWAITING_RESUME_UPLOAD,
    AWAITING_VACANCY_UPLOAD,
    MAIN_MENU,
    resume_file_handler,
    resume_url_handler,
    fallback_resume_handler,
    handle_invalid_resume_input,
)
from bot.handlers.vacancy import (
    vacancy_file_handler,
    vacancy_url_handler,
    fallback_vacancy_handler,
    handle_invalid_vacancy_input,
)
from bot.handlers.analysis import (
    analyze_match_handler,
    generate_letter_handler,
    generate_hr_plan_handler,
    generate_tech_plan_handler,
)
from bot.handlers.menu import (
    update_resume_handler,
    upload_vacancy_handler,
    select_vacancy_handler,
    vacancy_selected_handler,
)

logger = logging.getLogger(__name__)


def create_application() -> Application:
    """
    Создает и настраивает экземпляр приложения Telegram с единым ConversationHandler.
    """
    if not TELEGRAM_BOT_TOKEN:
        raise ValueError("Токен TELEGRAM_BOT_TOKEN не найден в .env файле!")

    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    # Главный обработчик диалога, который управляет всем состоянием бота
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            AWAITING_RESUME_UPLOAD: [
                resume_file_handler,
                resume_url_handler,
                MessageHandler(filters.PHOTO, handle_invalid_resume_input),
                fallback_resume_handler,
            ],
            AWAITING_VACANCY_UPLOAD: [
                vacancy_file_handler,
                vacancy_url_handler,
                MessageHandler(filters.PHOTO, handle_invalid_vacancy_input),
                fallback_vacancy_handler,
            ],
            MAIN_MENU: [
                # Действия для анализа (из analysis.py)
                analyze_match_handler,
                generate_letter_handler,
                generate_hr_plan_handler,
                generate_tech_plan_handler,
                # Действия из меню (из menu.py)
                update_resume_handler,
                upload_vacancy_handler,
                select_vacancy_handler,
                vacancy_selected_handler,
            ],
        },
        fallbacks=[
            CallbackQueryHandler(cancel, pattern="^cancel_action$"),
            MessageHandler(filters.TEXT & ~filters.COMMAND, global_fallback_handler),
        ],
        per_user=True,
        per_chat=True,
        allow_reentry=True  # Позволяет повторно входить в диалог с помощью /start
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

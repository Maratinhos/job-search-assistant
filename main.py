import asyncio
import logging
import sys

from bot.bot import main as run_bot
from db.database import init_db

# Настройка логирования
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)


async def main():
    """Основная функция для запуска бота."""
    try:
        logger.info("Инициализация базы данных...")
        init_db()
        logger.info("База данных инициализирована.")

        logger.info("Запуск бота...")
        # Используем await для запуска асинхронной функции run_bot
        await run_bot()

    except Exception as e:
        logger.critical(f"Произошла критическая ошибка на верхнем уровне: {e}", exc_info=True)
    finally:
        logger.info("Бот остановлен.")


if __name__ == "__main__":
    # На Windows может потребоваться другая политика событий для корректной работы asyncio
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Получен сигнал остановки от пользователя")
    except Exception as e:
        logger.critical(f"Критическая ошибка в main: {e}", exc_info=True)

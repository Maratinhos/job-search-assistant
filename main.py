import asyncio
import logging

from bot.bot import main as run_bot
from db.database import init_db

# Настройка логирования
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)


def main():
    """Основная функция для запуска бота."""
    try:
        logger.info("Инициализация базы данных...")
        init_db()
        logger.info("База данных инициализирована.")

        logger.info("Запуск бота...")
        # Используем asyncio.run() для запуска асинхронной функции run_bot
        asyncio.run(run_bot())

    except Exception as e:
        logger.critical(f"Произошла критическая ошибка на верхнем уровне: {e}", exc_info=True)
    finally:
        logger.info("Бот остановлен.")


if __name__ == "__main__":
    main()

# Исправленный main.py
import asyncio
import logging
import sys
import signal

from bot.bot import create_application
from db.database import init_db

# Настройка логирования
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# Глобальная переменная для graceful shutdown
shutdown_event = asyncio.Event()

def signal_handler(signum, frame):
    """Обработчик сигналов для graceful shutdown"""
    logger.info(f"Получен сигнал {signum}, инициируем остановку...")
    shutdown_event.set()

async def main():
    """Основная функция для запуска бота."""
    application = None
    try:
        logger.info("Инициализация базы данных...")
        init_db()
        logger.info("База данных инициализирована.")

        logger.info("Создание приложения бота...")
        application = create_application()
        
        logger.info("Запуск бота...")
        
        # Инициализируем приложение
        await application.initialize()
        await application.start()
        
        # Запускаем updater
        await application.updater.start_polling()
        
        logger.info("Бот успешно запущен и работает...")
        
        # Ожидаем сигнал остановки
        await shutdown_event.wait()
        
    except KeyboardInterrupt:
        logger.info("Получен KeyboardInterrupt")
    except Exception as e:
        logger.critical(f"Произошла критическая ошибка: {e}", exc_info=True)
    finally:
        if application:
            logger.info("Остановка бота...")
            try:
                await application.updater.stop()
                await application.stop()
                await application.shutdown()
                logger.info("Бот успешно остановлен.")
            except Exception as e:
                logger.error(f"Ошибка при остановке бота: {e}")


if __name__ == "__main__":
    # Настройка обработчиков сигналов
    if sys.platform != "win32":
        signal.signal(signal.SIGTERM, signal_handler)
        signal.signal(signal.SIGINT, signal_handler)
    
    # Правильная политика для Windows
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
    
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Получен сигнал остановки от пользователя")
        shutdown_event.set()
    except Exception as e:
        logger.critical(f"Критическая ошибка в main: {e}", exc_info=True)
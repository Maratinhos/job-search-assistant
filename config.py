import os
from dotenv import load_dotenv

# Загружаем переменные окружения из файла .env
# опция override=True позволяет перезаписывать системные переменные
load_dotenv(override=True)

# Токен для Telegram Bot API
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

# Ключ для OpenAI API
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Ключ для Gen-API
GEN_API_KEY = os.getenv("GEN_API_KEY")

# Название файла базы данных
DB_NAME = "bot_database.sqlite"

# Проверка на наличие токенов перенесена в модули, которые их непосредственно используют (bot.py и openai.py),
# чтобы не вызывать ошибку при импорте во время тестов.

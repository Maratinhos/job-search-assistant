import pytest
import os
from unittest.mock import MagicMock, AsyncMock
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from telegram import Update
from telegram.ext import ContextTypes
from alembic.config import Config
from alembic import command

from db.models import Base

# Используем файловую БД для тестов, чтобы избежать проблем с Alembic и in-memory SQLite
TEST_DATABASE_URL = "sqlite:///./test.db"


@pytest.fixture(scope="function")
def db_session():
    """
    Фикстура pytest для создания новой сессии БД для каждой тестовой функции.
    Применяет миграции Alembic для создания схемы и наполнения начальными данными.
    """
    # Удаляем старый файл БД, если он остался от предыдущих запусков
    if os.path.exists("test.db"):
        os.remove("test.db")

    engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})

    # Настраиваем и применяем миграции
    alembic_cfg = Config("alembic.ini")
    alembic_cfg.set_main_option("sqlalchemy.url", TEST_DATABASE_URL)
    command.upgrade(alembic_cfg, "head")

    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        # Удаляем файл БД после тестов
        if os.path.exists("test.db"):
            os.remove("test.db")


@pytest.fixture
def update_mock():
    """Фикстура для мока Update."""
    update = MagicMock(spec=Update)
    update.effective_chat.id = 12345

    message_mock = AsyncMock()
    message_mock.reply_text = AsyncMock()
    update.message = message_mock
    update.effective_message = message_mock

    callback_query_mock = AsyncMock()
    callback_query_mock.answer = AsyncMock()
    callback_query_mock.edit_message_text = AsyncMock()
    callback_query_mock.message = AsyncMock()
    callback_query_mock.message.reply_text = AsyncMock()
    update.callback_query = callback_query_mock

    return update


@pytest.fixture
def context_mock():
    """Фикстура для мока Context."""
    context = MagicMock(spec=ContextTypes.DEFAULT_TYPE)
    context.user_data = {}
    context.bot = MagicMock()
    context.bot.send_message = AsyncMock()
    return context

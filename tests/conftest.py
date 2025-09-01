import pytest
from unittest.mock import MagicMock, AsyncMock
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from telegram import Update
from telegram.ext import ContextTypes

from db.models import Base

TEST_DATABASE_URL = "sqlite:///:memory:"


@pytest.fixture(scope="function")
def db_session():
    """
    Фикстура pytest для создания новой сессии БД для каждой тестовой функции.
    """
    engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


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

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from telegram import Update
from telegram.ext import ContextTypes

from bot.handlers.start import start
from bot.handlers.resume import AWAITING_RESUME_UPLOAD, AWAITING_VACANCY_UPLOAD, MAIN_MENU
from db import models
from bot import messages, keyboards

@pytest.mark.anyio
@patch('bot.handlers.start.keyboards', new_callable=MagicMock)
@patch('bot.handlers.start.crud')
@patch('bot.handlers.start.get_db')
async def test_start_no_resume(mock_get_db, mock_crud, mock_keyboards):
    """
    Тестирует команду /start, когда у пользователя еще нет резюме.
    """
    # --- Mocks Setup ---
    mock_db = MagicMock()
    mock_user = models.User(id=1, chat_id=123)
    mock_crud.get_or_create_user.return_value = mock_user
    mock_crud.get_user_resume.return_value = None  # No resume
    mock_get_db.return_value = iter([mock_db])
    mock_keyboards.cancel_keyboard.return_value = "cancel_keyboard_markup"


    update = AsyncMock(spec=Update)
    update.effective_chat.id = 123
    update.message = AsyncMock()

    context = MagicMock(spec=ContextTypes.DEFAULT_TYPE)

    # --- Call ---
    result = await start(update, context)

    # --- Assertions ---
    assert result == AWAITING_RESUME_UPLOAD
    update.message.reply_text.assert_any_call(messages.WELCOME_MESSAGE)
    update.message.reply_text.assert_any_call(messages.ASK_FOR_RESUME, reply_markup="cancel_keyboard_markup")

@pytest.mark.anyio
@patch('bot.handlers.start.keyboards', new_callable=MagicMock)
@patch('bot.handlers.start.crud')
@patch('bot.handlers.start.get_db')
async def test_start_with_resume_no_vacancies(mock_get_db, mock_crud, mock_keyboards):
    """
    Тестирует команду /start, когда у пользователя есть резюме, но нет вакансий.
    """
    # --- Mocks Setup ---
    mock_db = MagicMock()
    mock_user = models.User(id=1, chat_id=123)
    mock_resume = models.Resume(id=1, user_id=1, file_path="path", source="test", title="My Resume Title")
    mock_crud.get_or_create_user.return_value = mock_user
    mock_crud.get_user_resume.return_value = mock_resume
    mock_crud.get_user_vacancies.return_value = []  # No vacancies
    mock_get_db.return_value = iter([mock_db])
    mock_keyboards.cancel_keyboard.return_value = "cancel_keyboard_markup"

    update = AsyncMock(spec=Update)
    update.effective_chat.id = 123
    update.message = AsyncMock()

    context = MagicMock(spec=ContextTypes.DEFAULT_TYPE)

    # --- Call ---
    result = await start(update, context)

    # --- Assertions ---
    assert result == AWAITING_VACANCY_UPLOAD
    expected_message = messages.MAIN_MENU_NO_VACANCIES.format(resume_title="My Resume Title")
    update.message.reply_text.assert_any_call(expected_message)
    update.message.reply_text.assert_any_call(messages.ASK_FOR_VACANCY, reply_markup="cancel_keyboard_markup")


@pytest.mark.anyio
@patch('bot.handlers.start.keyboards', new_callable=MagicMock)
@patch('bot.handlers.start.crud')
@patch('bot.handlers.start.get_db')
async def test_start_with_resume_and_vacancies(mock_get_db, mock_crud, mock_keyboards):
    """
    Тестирует команду /start, когда у пользователя есть и резюме, и вакансии.
    """
    # --- Mocks Setup ---
    mock_db = MagicMock()
    mock_user = models.User(id=1, chat_id=123)
    mock_resume = models.Resume(id=1, user_id=1, file_path="path", source="test", title="My Awesome Resume")
    mock_vacancy = models.Vacancy(id=1, user_id=1, name="DevOps", file_path="path", source="test")
    mock_crud.get_or_create_user.return_value = mock_user
    mock_crud.get_user_resume.return_value = mock_resume
    mock_crud.get_user_vacancies.return_value = [mock_vacancy]
    mock_get_db.return_value = iter([mock_db])
    mock_keyboards.main_menu_keyboard.return_value = "main_menu_markup"


    update = AsyncMock(spec=Update)
    update.effective_chat.id = 123
    update.message = AsyncMock()

    context = MagicMock(spec=ContextTypes.DEFAULT_TYPE)
    context.user_data = {}

    # --- Call ---
    result = await start(update, context)

    # --- Assertions ---
    assert result == MAIN_MENU
    expected_message = messages.MAIN_MENU_MESSAGE.format(resume_title="My Awesome Resume", vacancy_count=1)
    update.message.reply_text.assert_any_call(expected_message, reply_markup="main_menu_markup")
    assert context.user_data['selected_vacancy_id'] == mock_vacancy.id

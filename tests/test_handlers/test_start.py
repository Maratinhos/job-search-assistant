import pytest
from unittest.mock import AsyncMock, MagicMock, patch, call
from telegram.constants import ParseMode

from bot.handlers.start import start
from bot.handlers.states import AWAITING_RESUME_UPLOAD, AWAITING_VACANCY_UPLOAD, MAIN_MENU
from db import models
from bot import messages, keyboards
from bot.utils import escape_markdown_v2


@pytest.mark.anyio
@patch('bot.handlers.start.keyboards')
@patch('bot.handlers.start.crud')
@patch('bot.handlers.start.get_db')
async def test_start_no_resume(mock_get_db, mock_crud, mock_keyboards, update_mock, context_mock):
    """
    Тестирует команду /start, когда у пользователя еще нет резюме.
    """
    # --- Mocks Setup ---
    mock_db = MagicMock()
    mock_user = models.User(id=1, chat_id=12345)
    mock_crud.get_or_create_user.return_value = mock_user
    mock_crud.get_user_resume.return_value = None  # No resume
    mock_get_db.return_value = iter([mock_db])
    mock_keyboards.cancel_keyboard.return_value = "cancel_keyboard_markup"

    # --- Call ---
    result = await start(update_mock, context_mock)

    # --- Assertions ---
    assert result == AWAITING_RESUME_UPLOAD

    expected_calls = [
        call(escape_markdown_v2(messages.WELCOME_MESSAGE), parse_mode=ParseMode.MARKDOWN_V2),
        call(
            escape_markdown_v2(messages.ASK_FOR_RESUME),
            reply_markup="cancel_keyboard_markup",
            parse_mode=ParseMode.MARKDOWN_V2,
        ),
    ]
    update_mock.message.reply_text.assert_has_calls(expected_calls, any_order=False)


@pytest.mark.anyio
@patch('bot.handlers.start.keyboards')
@patch('bot.handlers.start.crud')
@patch('bot.handlers.start.get_db')
async def test_start_with_resume_no_vacancies(mock_get_db, mock_crud, mock_keyboards, update_mock, context_mock):
    """
    Тестирует команду /start, когда у пользователя есть резюме, но нет вакансий.
    """
    # --- Mocks Setup ---
    mock_db = MagicMock()
    mock_user = models.User(id=1, chat_id=12345)
    mock_resume = models.Resume(id=1, user_id=1, file_path="path", source="test", title="My Resume Title")
    mock_crud.get_or_create_user.return_value = mock_user
    mock_crud.get_user_resume.return_value = mock_resume
    mock_crud.get_user_vacancies.return_value = []  # No vacancies
    mock_get_db.return_value = iter([mock_db])
    mock_keyboards.cancel_keyboard.return_value = "cancel_keyboard_markup"

    # --- Call ---
    result = await start(update_mock, context_mock)

    # --- Assertions ---
    assert result == AWAITING_VACANCY_UPLOAD

    expected_main_menu_message = messages.MAIN_MENU_NO_VACANCIES.format(resume_title="My Resume Title")
    expected_calls = [
        call(escape_markdown_v2(expected_main_menu_message), parse_mode=ParseMode.MARKDOWN_V2),
        call(
            escape_markdown_v2(messages.ASK_FOR_VACANCY),
            reply_markup="cancel_keyboard_markup",
            parse_mode=ParseMode.MARKDOWN_V2,
        ),
    ]
    update_mock.message.reply_text.assert_has_calls(expected_calls, any_order=False)


@pytest.mark.anyio
@patch('bot.handlers.start.show_main_menu', new_callable=AsyncMock)
@patch('bot.handlers.start.crud')
@patch('bot.handlers.start.get_db')
async def test_start_with_resume_and_vacancies(mock_get_db, mock_crud, mock_show_main_menu, update_mock, context_mock):
    """
    Тестирует команду /start, когда у пользователя есть и резюме, и вакансии.
    """
    # --- Mocks Setup ---
    mock_db = MagicMock()
    mock_user = models.User(id=1, chat_id=12345)
    mock_resume = models.Resume(id=1, user_id=1, file_path="path", source="test", title="My Awesome Resume")
    mock_vacancy = models.Vacancy(id=1, user_id=1, title="DevOps", file_path="path", source="test")
    mock_crud.get_or_create_user.return_value = mock_user
    mock_crud.get_user_resume.return_value = mock_resume
    mock_crud.get_user_vacancies.return_value = [mock_vacancy]
    mock_get_db.return_value = iter([mock_db])

    # --- Call ---
    result = await start(update_mock, context_mock)

    # --- Assertions ---
    assert result == MAIN_MENU
    assert context_mock.user_data['selected_vacancy_id'] == 1
    update_mock.message.reply_text.assert_not_called()
    mock_show_main_menu.assert_called_once_with(update_mock, context_mock)

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from telegram import Update, Document
from telegram.ext import ContextTypes

from bot.handlers.vacancy import handle_vacancy_file, process_vacancy_text
from bot.handlers.resume import AWAITING_VACANCY_UPLOAD, MAIN_MENU
from bot import messages, keyboards
from db import models

@pytest.fixture
def update_mock():
    """Фикстура для мока Update."""
    update = MagicMock(spec=Update)
    update.effective_chat.id = 12345
    update.effective_message = AsyncMock()
    return update

@pytest.fixture
def context_mock():
    """Фикстура для мока Context."""
    context = MagicMock(spec=ContextTypes.DEFAULT_TYPE)
    context.user_data = {}
    return context

@pytest.mark.anyio
@patch('bot.handlers.vacancy.process_vacancy_text', new_callable=AsyncMock)
async def test_handle_vacancy_file_success(mock_process_vacancy, update_mock, context_mock):
    mock_document = MagicMock(spec=Document)
    mock_document.file_name = "vacancy.txt"
    mock_file = AsyncMock()
    mock_file.download_as_bytearray.return_value = b"Vacancy text"
    mock_document.get_file.return_value = mock_file
    update_mock.message.document = mock_document
    await handle_vacancy_file(update_mock, context_mock)
    mock_process_vacancy.assert_called_once_with(
        update_mock, context_mock, "Vacancy text", source="vacancy.txt"
    )

@pytest.mark.anyio
@patch('bot.handlers.vacancy.show_main_menu', new_callable=AsyncMock)
@patch('bot.handlers.vacancy.save_text_to_file', return_value="/fake/path/vacancy.txt")
@patch('bot.handlers.vacancy.crud')
@patch('bot.handlers.vacancy.get_ai_client')
async def test_process_vacancy_text_success(mock_get_ai, mock_crud, mock_save, mock_show_main_menu, update_mock, context_mock):
    mock_ai_client = MagicMock()
    mock_ai_client.verify_vacancy.return_value = {
        "text": '{"is_vacancy": true, "title": "Test Vacancy"}',
        "usage": {"total_tokens": 100}
    }
    mock_get_ai.return_value = mock_ai_client

    mock_db_session = MagicMock()
    mock_crud.get_or_create_user.return_value = MagicMock(id=1)
    mock_crud.create_vacancy.return_value = MagicMock(id=99)
    mock_resume = MagicMock(spec=models.Resume)
    mock_resume.title = "My Resume"
    mock_crud.get_user_resume.return_value = mock_resume

    with patch('bot.handlers.vacancy.get_db', return_value=iter([mock_db_session])):
        result_state = await process_vacancy_text(update_mock, context_mock, "text", "source")

    mock_crud.create_vacancy.assert_called_once()
    assert context_mock.user_data['selected_vacancy_id'] == 99
    assert result_state == MAIN_MENU
    mock_show_main_menu.assert_called_once_with(update_mock, context_mock)

@pytest.mark.anyio
@patch('bot.handlers.vacancy.save_text_to_file')
@patch('bot.handlers.vacancy.crud')
@patch('bot.handlers.vacancy.get_ai_client')
async def test_process_vacancy_text_ai_fails_verification(mock_get_ai, mock_crud, mock_save, update_mock, context_mock):
    mock_ai_client = MagicMock()
    mock_ai_client.verify_vacancy.return_value = {"is_vacancy": False, "usage": {"total_tokens": 50}}
    mock_get_ai.return_value = mock_ai_client

    mock_db_session = MagicMock()
    mock_crud.get_or_create_user.return_value = MagicMock(id=1)

    cancel_kb = keyboards.cancel_keyboard()
    with patch('bot.handlers.vacancy.get_db', return_value=iter([mock_db_session])),\
         patch('bot.handlers.vacancy.keyboards.cancel_keyboard', return_value=cancel_kb):
        result_state = await process_vacancy_text(update_mock, context_mock, "not a vacancy", "source")

    mock_crud.create_vacancy.assert_not_called()
    update_mock.effective_message.reply_text.assert_any_call(messages.ASK_FOR_VACANCY, reply_markup=cancel_kb)
    assert result_state == AWAITING_VACANCY_UPLOAD

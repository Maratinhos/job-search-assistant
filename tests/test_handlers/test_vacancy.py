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
async def test_process_vacancy_text_success(
    mock_get_ai, mock_crud, mock_save, mock_show_main_menu, update_mock, context_mock
):
    """Тестирует успешный сценарий обработки вакансии, включая логирование."""
    mock_ai_client = MagicMock()
    mock_ai_client.verify_vacancy.return_value = {
        "text": '{"is_vacancy": true, "title": "Test Vacancy"}',
        "cost": 0.003,
        "prompt_tokens": 60,
        "completion_tokens": 120,
        "total_tokens": 180,
    }
    mock_get_ai.return_value = mock_ai_client

    mock_db_session = MagicMock()
    mock_user = MagicMock(id=1)
    mock_crud.get_or_create_user.return_value = mock_user
    mock_crud.create_vacancy.return_value = MagicMock(id=99)

    with patch('bot.handlers.vacancy.get_db', return_value=iter([mock_db_session])):
        result_state = await process_vacancy_text(update_mock, context_mock, "text", "source")

    mock_crud.create_ai_usage_log.assert_called_once_with(
        db=mock_db_session,
        user_id=mock_user.id,
        prompt_tokens=60,
        completion_tokens=120,
        total_tokens=180,
        cost=0.003,
        action="verify_vacancy",
    )
    mock_crud.create_vacancy.assert_called_once()
    assert context_mock.user_data['selected_vacancy_id'] == 99
    assert result_state == MAIN_MENU
    mock_show_main_menu.assert_called_once_with(update_mock, context_mock)


@pytest.mark.anyio
@patch('bot.handlers.vacancy.crud')
@patch('bot.handlers.vacancy.get_ai_client')
async def test_process_vacancy_text_ai_fails_verification(
    mock_get_ai, mock_crud, update_mock, context_mock
):
    """Тестирует сценарий, когда AI не подтверждает вакансию, но логирование происходит."""
    mock_ai_client = MagicMock()
    mock_ai_client.verify_vacancy.return_value = {
        "text": '{"is_vacancy": false}',
        "cost": 0.001,
        "prompt_tokens": 40,
        "completion_tokens": 10,
        "total_tokens": 50,
    }
    mock_get_ai.return_value = mock_ai_client

    mock_db_session = MagicMock()
    mock_user = MagicMock(id=1)
    mock_crud.get_or_create_user.return_value = mock_user

    with patch('bot.handlers.vacancy.get_db', return_value=iter([mock_db_session])):
        result_state = await process_vacancy_text(update_mock, context_mock, "not a vacancy", "source")

    mock_crud.create_ai_usage_log.assert_called_once_with(
        db=mock_db_session,
        user_id=mock_user.id,
        prompt_tokens=40,
        completion_tokens=10,
        total_tokens=50,
        cost=0.001,
        action="verify_vacancy",
    )
    mock_crud.create_vacancy.assert_not_called()
    assert result_state == AWAITING_VACANCY_UPLOAD

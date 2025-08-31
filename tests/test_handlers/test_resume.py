import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from telegram import Update, User, Message, Document, File
from telegram.ext import ConversationHandler, ContextTypes

from bot.handlers.resume import (
    handle_resume_file,
    process_resume_text,
    AWAITING_RESUME_UPLOAD,
    AWAITING_VACANCY_UPLOAD,
)
from db import models


@pytest.mark.anyio
@patch('bot.handlers.resume.get_ai_client')
@patch('bot.handlers.resume.crud')
@patch('bot.handlers.resume.save_text_to_file', return_value="some/path/resume.txt")
@patch('bot.handlers.resume.get_db')
async def test_process_resume_text_success(
    mock_get_db, mock_save_text, mock_crud, mock_get_ai_client
):
    """
    Тестирует успешный сценарий обработки текста резюме.
    """
    # --- Mocks Setup ---
    # AI Client
    mock_ai_client = MagicMock()
    mock_ai_client.verify_resume.return_value = {
        "text": '{"is_resume": true, "title": "Senior Python Developer"}',
        "usage": {"total_tokens": 100}
    }
    mock_get_ai_client.return_value = mock_ai_client

    # Database
    mock_db = MagicMock()
    mock_user = models.User(id=1, chat_id=123)
    mock_crud.get_or_create_user.return_value = mock_user
    mock_get_db.return_value = iter([mock_db])

    # Telegram Update
    update = AsyncMock(spec=Update)
    update.effective_chat.id = 123
    update.effective_message = AsyncMock(spec=Message)

    context = MagicMock(spec=ContextTypes.DEFAULT_TYPE)

    # --- Call ---
    result = await process_resume_text(update, context, "resume text", "test_source")

    # --- Assertions ---
    # AI client was called
    mock_ai_client.verify_resume.assert_called_once_with("resume text")

    # DB user was fetched
    mock_crud.get_or_create_user.assert_called_once_with(mock_db, chat_id=123)

    # AI usage was logged
    mock_crud.create_ai_usage_log.assert_called_once()

    # File was saved
    mock_save_text.assert_called_once_with("resume text", "resumes")

    # Resume was created in DB
    mock_crud.create_resume.assert_called_once_with(
        mock_db,
        user_id=mock_user.id,
        file_path="some/path/resume.txt",
        source="test_source",
        title="Senior Python Developer"
    )

    # Correct state is returned
    assert result == AWAITING_VACANCY_UPLOAD

    # User was notified
    update.effective_message.reply_text.assert_called()


@pytest.mark.anyio
@patch('bot.handlers.resume.get_ai_client')
async def test_process_resume_text_verification_failed(mock_get_ai_client):
    """
    Тестирует сценарий, когда AI не подтверждает, что текст является резюме.
    """
    # --- Mocks Setup ---
    mock_ai_client = MagicMock()
    mock_ai_client.verify_resume.return_value = {
        "text": '{"is_resume": false, "title": null}',
        "usage": {"total_tokens": 50}
    }
    mock_get_ai_client.return_value = mock_ai_client

    update = AsyncMock(spec=Update)
    update.effective_chat.id = 123
    update.effective_message = AsyncMock(spec=Message)

    context = MagicMock(spec=ContextTypes.DEFAULT_TYPE)

    # --- Call ---
    with patch('bot.handlers.resume.get_db'), patch('bot.handlers.resume.crud'):
        result = await process_resume_text(update, context, "not a resume", "test")

    # --- Assertions ---
    assert result == AWAITING_RESUME_UPLOAD
    # Check that the user is informed about the failure
    assert "не похож на резюме" in update.effective_message.reply_text.call_args_list[1].args[0]


@pytest.mark.anyio
@patch('bot.handlers.resume.get_ai_client')
@patch('bot.handlers.resume.crud')
@patch('bot.handlers.resume.save_text_to_file', return_value="some/path/resume.txt")
@patch('bot.handlers.resume.get_db')
async def test_process_resume_text_new_ai_format(
    mock_get_db, mock_save_text, mock_crud, mock_get_ai_client
):
    """
    Тестирует успешный сценарий обработки текста резюме с новым форматом ответа от AI.
    """
    # --- Mocks Setup ---
    # AI Client
    mock_ai_client = MagicMock()
    # This is the response format provided by the user
    mock_ai_client.verify_resume.return_value = {
        'request_id': 24075135,
        'model': 'gpt-5',
        'cost': 0.2593,
        'response': [{
            'logprobs': None,
            'finish_reason': 'stop',
            'native_finish_reason': 'completed',
            'index': 0,
            'message': {
                'role': 'assistant',
                'content': '{"is_resume": true, "title": "Senior BI Analyst"}'
            }
        }]
    }
    mock_get_ai_client.return_value = mock_ai_client

    # Database
    mock_db = MagicMock()
    mock_user = models.User(id=1, chat_id=123)
    mock_crud.get_or_create_user.return_value = mock_user
    mock_get_db.return_value = iter([mock_db])

    # Telegram Update
    update = AsyncMock(spec=Update)
    update.effective_chat.id = 123
    update.effective_message = AsyncMock(spec=Message)

    context = MagicMock(spec=ContextTypes.DEFAULT_TYPE)

    # --- Call ---
    result = await process_resume_text(update, context, "resume text", "test_source")

    # --- Assertions ---
    # Resume was created in DB with the correct title
    mock_crud.create_resume.assert_called_once_with(
        mock_db,
        user_id=mock_user.id,
        file_path="some/path/resume.txt",
        source="test_source",
        title="Senior BI Analyst"
    )

    # Correct state is returned
    assert result == AWAITING_VACANCY_UPLOAD

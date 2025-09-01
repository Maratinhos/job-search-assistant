import pytest
import os
from unittest.mock import AsyncMock, MagicMock, patch, mock_open

from telegram import Update
from telegram.ext import ContextTypes

from bot.handlers import analysis
from db import models

@pytest.mark.anyio
@patch('bot.handlers.analysis.uuid.uuid4', return_value='test-uuid')
@patch('os.makedirs')
@patch('builtins.open', new_callable=mock_open, read_data="file content")
@patch('bot.handlers.analysis.get_ai_client')
@patch('bot.handlers.analysis.crud')
@patch('bot.handlers.analysis.get_db')
async def test_perform_analysis_success(mock_get_db, mock_crud, mock_get_ai, mock_open_file, mock_makedirs, mock_uuid):
    """Тестирует успешное выполнение анализа и сохранения результата."""
    mock_update = AsyncMock(spec=Update)
    mock_context = MagicMock(spec=ContextTypes.DEFAULT_TYPE)
    chat_id = 12345
    user_id = 1
    resume_id = 10
    vacancy_id = 20

    mock_update.effective_chat.id = chat_id
    mock_context.user_data = {'selected_vacancy_id': vacancy_id}
    mock_update.callback_query = AsyncMock()
    mock_update.callback_query.answer = AsyncMock()
    mock_update.callback_query.message.reply_text = AsyncMock()

    mock_db = MagicMock()
    mock_get_db.return_value = iter([mock_db])

    mock_user = MagicMock(id=user_id)
    mock_resume = MagicMock(id=resume_id, file_path="resume.txt")
    mock_vacancy = MagicMock(id=vacancy_id, file_path="vacancy.txt")

    mock_crud.get_or_create_user.return_value = mock_user
    mock_crud.get_user_resume.return_value = mock_resume
    mock_crud.get_vacancy_by_id.return_value = mock_vacancy
    mock_crud.get_analysis_result.return_value = None

    mock_ai_client = MagicMock()
    mock_ai_client.analyze_match.return_value = {
        "text": "This is a test analysis.",
        "cost": 0.005,
        "prompt_tokens": 100,
        "completion_tokens": 200,
        "total_tokens": 300,
    }
    mock_get_ai.return_value = mock_ai_client

    action = "analyze_match"
    await analysis._perform_analysis(mock_update, mock_context, action)

    mock_open_file.assert_any_call("resume.txt", 'r', encoding='utf-8')
    mock_open_file.assert_any_call("vacancy.txt", 'r', encoding='utf-8')

    mock_crud.create_analysis_result.assert_called_once_with(
        mock_db,
        resume_id=resume_id,
        vacancy_id=vacancy_id,
        action_type=action,
        file_path=os.path.join("storage/analysis_results", "test-uuid.txt")
    )

    mock_crud.create_ai_usage_log.assert_called_once_with(
        db=mock_db,
        user_id=user_id,
        prompt_tokens=100,
        completion_tokens=200,
        total_tokens=300,
        cost=0.005,
        action=action,
        resume_id=resume_id,
        vacancy_id=vacancy_id,
    )

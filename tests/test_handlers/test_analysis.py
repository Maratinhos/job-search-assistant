import pytest
import os
from unittest.mock import AsyncMock, MagicMock, patch, mock_open

from bot.handlers import analysis
from db import models
from ai.actions import ACTION_REGISTRY

# Теперь мы можем использовать фикстуры update_mock и context_mock из conftest.py

@pytest.mark.anyio
@patch('bot.handlers.analysis.uuid.uuid4', return_value='test-uuid')
@patch('os.makedirs')
@patch('builtins.open', new_callable=mock_open, read_data="file content")
@patch('bot.handlers.analysis.get_ai_client')
@patch('bot.handlers.analysis.crud')
@patch('bot.handlers.analysis.get_db')
async def test_perform_analysis_success(
    mock_get_db, mock_crud, mock_get_ai, mock_open_file, mock_makedirs, mock_uuid,
    update_mock, context_mock
):
    """Тестирует успешное выполнение анализа и сохранения результата с использованием ACTION_REGISTRY."""
    # Настройка моков
    user_id = 1
    resume_id = 10
    vacancy_id = 20
    action = "analyze_match"
    context_mock.user_data['selected_vacancy_id'] = vacancy_id

    mock_db = MagicMock()
    mock_get_db.return_value = iter([mock_db])

    mock_user = MagicMock(id=user_id)
    mock_resume = MagicMock(id=resume_id, file_path="resume.txt")
    mock_vacancy = MagicMock(id=vacancy_id, file_path="vacancy.txt")

    mock_crud.get_or_create_user.return_value = mock_user
    mock_crud.get_user_resume.return_value = mock_resume
    mock_crud.get_vacancy_by_id.return_value = mock_vacancy
    mock_crud.get_analysis_result.return_value = None # No cached result

    # Настройка мока AI клиента для consolidated_analysis
    mock_ai_client = MagicMock()
    mock_analysis_data = {
        "match_analysis": "This is the match analysis.",
        "cover_letter": "This is the cover letter.",
        "hr_call_plan": "This is the HR call plan.",
        "tech_interview_plan": "This is the tech interview plan."
    }
    mock_ai_response = {
        "json": mock_analysis_data,
        "usage": {
            "cost": 0.005,
            "prompt_tokens": 100,
            "completion_tokens": 200,
            "total_tokens": 300,
        }
    }
    mock_ai_client.get_consolidated_analysis.return_value = mock_ai_response
    mock_get_ai.return_value = mock_ai_client

    # Вызов тестируемой функции
    await analysis._perform_analysis(update_mock, context_mock, action)

    # Проверки
    mock_open_file.assert_any_call("resume.txt", 'r', encoding='utf-8')
    mock_open_file.assert_any_call("vacancy.txt", 'r', encoding='utf-8')

    # Проверяем, что был вызван правильный метод AI
    mock_ai_client.get_consolidated_analysis.assert_called_once_with("file content", "file content")

    # Проверяем, что результат сохраняется в БД
    mock_crud.create_analysis_result.assert_called_once_with(
        mock_db, mock_resume.id, mock_vacancy.id, mock_analysis_data
    )

    # Проверяем логирование использования
    mock_crud.create_ai_usage_log.assert_called_once_with(
        db=mock_db,
        user_id=user_id,
        prompt_tokens=100,
        completion_tokens=200,
        total_tokens=300,
        cost=0.005,
        action="consolidated_analysis",
        resume_id=mock_resume.id,
        vacancy_id=mock_vacancy.id,
    )

    # Проверяем, что пользователю был отправлен результат
    update_mock.callback_query.message.reply_text.assert_called()
    last_call_args = update_mock.callback_query.message.reply_text.call_args

    action_details = ACTION_REGISTRY.get(action)
    expected_header = action_details["response_header"]
    expected_body = mock_analysis_data[action_details["db_field"]]

    assert expected_header in last_call_args.kwargs['text']
    assert expected_body in last_call_args.kwargs['text']

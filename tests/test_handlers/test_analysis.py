import pytest
import os
from unittest.mock import AsyncMock, MagicMock, patch, mock_open

from bot.handlers import analysis
from db import models
from bot.utils import escape_markdown_v2

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
    mock_crud.get_analysis_result.return_value = None

    # Настройка мока AI клиента
    mock_ai_client = MagicMock()
    mock_ai_response = {
        "text": "This is a test analysis.",
        "usage": {
            "cost": 0.005,
            "prompt_tokens": 100,
            "completion_tokens": 200,
            "total_tokens": 300,
        }
    }
    # Мокаем метод, который будет вызываться через getattr
    mock_analyze_method = MagicMock(return_value=mock_ai_response)
    # Устанавливаем мок-метод как атрибут на мок-клиенте
    # Это важно, так как код теперь использует getattr(ai_client, "analyze_match")
    setattr(mock_ai_client, "analyze_match", mock_analyze_method)

    mock_get_ai.return_value = mock_ai_client

    # Вызов тестируемой функции
    await analysis._perform_analysis(update_mock, context_mock, action)

    # Проверки
    mock_open_file.assert_any_call("resume.txt", 'r', encoding='utf-8')
    mock_open_file.assert_any_call("vacancy.txt", 'r', encoding='utf-8')

    # Проверяем, что был вызван правильный метод AI
    mock_analyze_method.assert_called_once_with("file content", "file content")

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

    # Проверяем, что пользователю был отправлен результат
    update_mock.callback_query.message.reply_text.assert_called()
    last_call_args = update_mock.callback_query.message.reply_text.call_args
    # Проверяем, что заголовок из ACTION_REGISTRY и текст ответа AI присутствуют
    escaped_header = escape_markdown_v2("Анализ завершен:")
    escaped_body = escape_markdown_v2("This is a test analysis.")
    assert escaped_header in last_call_args.kwargs['text']
    assert escaped_body in last_call_args.kwargs['text']

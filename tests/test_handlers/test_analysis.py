import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from telegram import Update, User as TUser, Chat, Message, CallbackQuery
from telegram.ext import ContextTypes

from bot.handlers import analysis
from db import models

@pytest.mark.asyncio
async def test_perform_analysis_success():
    """Тестирует успешное выполнение анализа и сохранения результата."""
    # 1. Настройка моков
    mock_update = AsyncMock(spec=Update)
    mock_context = MagicMock(spec=ContextTypes.DEFAULT_TYPE)

    chat_id = 12345
    user_id = 1
    resume_id = 10
    vacancy_id = 20

    # Моки для Telegram объектов
    mock_update.effective_chat.id = chat_id
    mock_context.user_data = {'selected_vacancy_id': vacancy_id}
    mock_update.callback_query = AsyncMock(spec=CallbackQuery)
    mock_update.callback_query.answer = AsyncMock()
    mock_update.callback_query.message.reply_text = AsyncMock()

    # Моки для базы данных
    mock_db = MagicMock()
    mock_user = models.User(id=user_id, chat_id=chat_id)
    mock_resume = models.Resume(id=resume_id, user_id=user_id, file_path="resume.txt", title="Resume")
    mock_vacancy = models.Vacancy(id=vacancy_id, user_id=user_id, file_path="vacancy.txt", name="Vacancy")

    # Моки для CRUD операций
    mock_crud = MagicMock()
    mock_crud.get_or_create_user.return_value = mock_user
    mock_crud.get_user_resume.return_value = mock_resume
    mock_crud.get_vacancy_by_id.return_value = mock_vacancy
    mock_crud.create_analysis_result = MagicMock()
    mock_crud.create_ai_usage_log = MagicMock()

    # Мок для AI клиента
    mock_ai_client = MagicMock()
    mock_ai_client.analyze_match.return_value = {
        "text": "This is a test analysis.",
        "usage": {"prompt_tokens": 5, "completion_tokens": 10, "total_tokens": 15}
    }

    # Патчинг
    with patch('bot.handlers.analysis.get_db', return_value=(mock_db for _ in range(1))),\
         patch('bot.handlers.analysis.crud', mock_crud),\
         patch('bot.handlers.analysis.get_ai_client', return_value=mock_ai_client),\
         patch('builtins.open', new_callable=MagicMock),\
         patch('os.makedirs'),\
         patch('uuid.uuid4', return_value='test-uuid'):

        # 2. Вызов функции
        await analysis._perform_analysis(mock_update, mock_context, "analyze_match")

        # 3. Проверки
        # Проверяем, что reply_text был вызван для отправки результата
        mock_update.callback_query.message.reply_text.assert_any_call(text="⏳ Выполняю ваш запрос... Это может занять некоторое время.")

        # Проверяем вызов create_analysis_result
        mock_crud.create_analysis_result.assert_called_once()
        call_args = mock_crud.create_analysis_result.call_args
        assert call_args.kwargs['resume_id'] == resume_id
        assert call_args.kwargs['vacancy_id'] == vacancy_id
        assert call_args.kwargs['action_type'] == "analyze_match"
        assert "test-uuid.txt" in call_args.kwargs['file_path']

        # Проверяем вызов create_ai_usage_log
        mock_crud.create_ai_usage_log.assert_called_once()
        log_args = mock_crud.create_ai_usage_log.call_args
        assert log_args.kwargs['user_id'] == user_id
        assert log_args.kwargs['action'] == "analyze_match"
        assert log_args.kwargs['resume_id'] == resume_id
        assert log_args.kwargs['vacancy_id'] == vacancy_id

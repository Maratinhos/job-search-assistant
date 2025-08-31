import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from telegram import Update
from telegram.ext import ContextTypes, ConversationHandler

from bot.handlers.common import global_fallback_handler, cancel
from bot.handlers.resume import MAIN_MENU, AWAITING_RESUME_UPLOAD
from bot import messages, keyboards

@pytest.fixture
def update_mock():
    """Фикстура для мока Update."""
    update = MagicMock(spec=Update)
    update.effective_chat.id = 12345
    update.message = AsyncMock()
    update.message.text = "непонятный текст"
    update.callback_query = None # Убедимся, что это не callback
    return update

@pytest.fixture
def context_mock():
    """Фикстура для мока Context."""
    context = MagicMock(spec=ContextTypes.DEFAULT_TYPE)
    context.user_data = {}
    return context

@pytest.mark.anyio
@patch('bot.handlers.common.keyboards', new_callable=MagicMock)
@patch('bot.handlers.common.crud')
@patch('bot.handlers.common.get_db')
async def test_global_fallback_handler_with_resume(mock_get_db, mock_crud, mock_keyboards, update_mock, context_mock):
    """
    Тест: fallback-обработчик для пользователя, у которого уже есть резюме.
    Ожидание: Пользователя возвращает в главное меню.
    """
    # --- Mocks ---
    mock_db_session = MagicMock()
    mock_get_db.return_value = iter([mock_db_session])

    mock_user = MagicMock(id=1)
    mock_resume = MagicMock(id=10)
    mock_crud.get_or_create_user.return_value = mock_user
    mock_crud.get_user_resumes.return_value = [mock_resume]
    mock_crud.get_user_vacancies.return_value = [] # 0 вакансий

    # --- Call ---
    result_state = await global_fallback_handler(update_mock, context_mock)

    # --- Assertions ---
    mock_crud.get_user_resumes.assert_called_once_with(mock_db_session, user_id=mock_user.id)
    mock_crud.get_user_vacancies.assert_called_once_with(mock_db_session, user_id=mock_user.id)
    update_mock.message.reply_text.assert_called_once_with(
        text=messages.GLOBAL_FALLBACK_MESSAGE,
        reply_markup=mock_keyboards.main_menu_keyboard.return_value
    )
    mock_keyboards.main_menu_keyboard.assert_called_once_with(vacancy_count=0, has_resume=True)
    assert result_state == MAIN_MENU

@pytest.mark.anyio
@patch('bot.handlers.common.keyboards', new_callable=MagicMock)
@patch('bot.handlers.common.crud')
@patch('bot.handlers.common.get_db')
async def test_global_fallback_handler_no_resume(mock_get_db, mock_crud, mock_keyboards, update_mock, context_mock):
    """
    Тест: fallback-обработчик для нового пользователя без резюме.
    Ожидание: Пользователю предлагается загрузить резюме.
    """
    # --- Mocks ---
    mock_db_session = MagicMock()
    mock_get_db.return_value = iter([mock_db_session])

    mock_user = MagicMock(id=1)
    mock_crud.get_or_create_user.return_value = mock_user
    mock_crud.get_user_resumes.return_value = [] # <-- Нет резюме

    # --- Call ---
    result_state = await global_fallback_handler(update_mock, context_mock)

    # --- Assertions ---
    update_mock.message.reply_text.assert_any_call(messages.WELCOME_MESSAGE)
    update_mock.message.reply_text.assert_any_call(
        messages.ASK_FOR_RESUME,
        reply_markup=mock_keyboards.cancel_keyboard.return_value
    )
    assert result_state == AWAITING_RESUME_UPLOAD

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from telegram import Update
from telegram.ext import ContextTypes

from bot.handlers.menu import update_resume_request
from bot.handlers.resume import AWAITING_RESUME_UPLOAD
from bot import messages, keyboards


@pytest.mark.anyio
@patch('bot.handlers.menu.keyboards', new_callable=MagicMock)
async def test_update_resume_request(mock_keyboards):
    """
    Тестирует обработчик 'update_resume_request'.
    Проверяет, что бот отправляет правильное сообщение и переходит в состояние ожидания резюме.
    """
    # --- Mocks Setup ---
    mock_keyboards.cancel_keyboard.return_value = "cancel_keyboard_markup"

    update = AsyncMock(spec=Update)
    query = AsyncMock()
    update.callback_query = query
    context = MagicMock(spec=ContextTypes.DEFAULT_TYPE)

    # --- Call ---
    result = await update_resume_request(update, context)

    # --- Assertions ---
    assert result == AWAITING_RESUME_UPLOAD
    query.answer.assert_called_once()
    query.edit_message_text.assert_called_once_with(
        messages.ASK_FOR_RESUME,
        reply_markup="cancel_keyboard_markup"
    )

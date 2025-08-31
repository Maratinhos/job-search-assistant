import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from telegram import Update
from telegram.ext import ContextTypes

from bot.handlers.menu import update_resume_request, select_vacancy, on_vacancy_selected
from bot.handlers.resume import AWAITING_RESUME_UPLOAD, MAIN_MENU
from bot import messages, keyboards
from db import models


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


@pytest.mark.anyio
@patch('bot.handlers.menu.get_db')
@patch('bot.handlers.menu.crud')
@patch('bot.handlers.menu.keyboards')
async def test_select_vacancy(mock_keyboards, mock_crud, mock_get_db):
    """
    Тест: обработчик 'select_vacancy' корректно показывает список вакансий.
    """
    # --- Mocks ---
    update = AsyncMock()
    query = AsyncMock()
    update.callback_query = query
    context = MagicMock()

    mock_user = models.User(id=1, chat_id=123)
    mock_vacancies = [models.Vacancy(id=1, title="Vacancy 1"), models.Vacancy(id=2, title="Vacancy 2")]
    mock_crud.get_or_create_user.return_value = mock_user
    mock_crud.get_user_vacancies.return_value = mock_vacancies
    mock_keyboards.vacancy_selection_keyboard.return_value = "vacancy_selection_markup"

    # --- Call ---
    result = await select_vacancy(update, context)

    # --- Assertions ---
    assert result == MAIN_MENU
    query.answer.assert_called_once()
    query.edit_message_text.assert_called_once_with(
        messages.CHOOSE_VACANCY_FOR_ACTION,
        reply_markup="vacancy_selection_markup"
    )
    mock_keyboards.vacancy_selection_keyboard.assert_called_once_with(mock_vacancies)


@pytest.mark.anyio
@patch('bot.handlers.menu.show_main_menu')
async def test_on_vacancy_selected(mock_show_main_menu):
    """
    Тест: обработчик 'on_vacancy_selected' корректно обновляет user_data и показывает меню.
    """
    # --- Mocks ---
    update = AsyncMock()
    query = AsyncMock()
    query.data = "vacancy_select_42"
    update.callback_query = query
    context = MagicMock()
    context.user_data = {}

    # --- Call ---
    result = await on_vacancy_selected(update, context)

    # --- Assertions ---
    assert result == MAIN_MENU
    assert context.user_data['selected_vacancy_id'] == 42
    query.answer.assert_called_once()
    mock_show_main_menu.assert_called_once_with(update, context)

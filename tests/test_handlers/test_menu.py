import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from bot.handlers.menu import update_resume_request, select_vacancy, on_vacancy_selected
from bot.handlers.states import SELECTING_VACANCY, MAIN_MENU, UPDATE_RESUME
from bot import messages, keyboards
from db import models


@pytest.mark.anyio
@patch('bot.handlers.menu.keyboards')
async def test_update_resume_request(mock_keyboards, update_mock, context_mock):
    """
    Тестирует обработчик 'update_resume_request'.
    Проверяет, что бот отправляет правильное сообщение и переходит в состояние ожидания резюме.
    """
    mock_keyboards.cancel_keyboard.return_value = "cancel_keyboard_markup"

    result = await update_resume_request(update_mock, context_mock)

    assert result == UPDATE_RESUME
    update_mock.callback_query.answer.assert_called_once()
    update_mock.callback_query.edit_message_text.assert_called_once_with(
        messages.ASK_FOR_RESUME,
        reply_markup="cancel_keyboard_markup"
    )


@pytest.mark.anyio
@patch('bot.handlers.menu.get_db')
@patch('bot.handlers.menu.crud')
@patch('bot.handlers.menu.keyboards')
async def test_select_vacancy(mock_keyboards, mock_crud, mock_get_db, update_mock, context_mock):
    """
    Тест: обработчик 'select_vacancy' корректно показывает список вакансий.
    """
    mock_user = models.User(id=1, chat_id=12345)
    mock_vacancies = [models.Vacancy(id=1, title="Vacancy 1"), models.Vacancy(id=2, title="Vacancy 2")]
    mock_crud.get_or_create_user.return_value = mock_user
    mock_crud.get_user_vacancies.return_value = mock_vacancies
    mock_keyboards.vacancy_selection_keyboard.return_value = "vacancy_selection_markup"

    db_session = MagicMock()
    mock_get_db.return_value = iter([db_session])

    result = await select_vacancy(update_mock, context_mock)

    assert result == SELECTING_VACANCY
    update_mock.callback_query.answer.assert_called_once()
    update_mock.callback_query.edit_message_text.assert_called_once_with(
        messages.CHOOSE_VACANCY_FOR_ACTION,
        reply_markup="vacancy_selection_markup"
    )
    mock_keyboards.vacancy_selection_keyboard.assert_called_once_with(mock_vacancies)


@pytest.mark.anyio
@patch('bot.handlers.menu.show_main_menu', new_callable=AsyncMock)
async def test_on_vacancy_selected(mock_show_main_menu, update_mock, context_mock):
    """
    Тест: обработчик 'on_vacancy_selected' корректно обновляет user_data и показывает меню.
    """
    update_mock.callback_query.data = "vacancy_select_42"

    result = await on_vacancy_selected(update_mock, context_mock)

    assert result == MAIN_MENU
    assert context_mock.user_data['selected_vacancy_id'] == 42
    update_mock.callback_query.answer.assert_called_once()
    mock_show_main_menu.assert_called_once_with(update_mock, context_mock)

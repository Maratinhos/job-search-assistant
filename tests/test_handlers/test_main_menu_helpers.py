import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from bot.handlers.main_menu_helpers import show_main_menu
from bot.handlers.resume import MAIN_MENU
from bot import messages, keyboards
from db import models

@pytest.mark.anyio
@patch('bot.handlers.main_menu_helpers.get_db')
@patch('bot.handlers.main_menu_helpers.crud')
@patch('bot.handlers.main_menu_helpers.keyboards')
async def test_show_main_menu_with_selected_vacancy(mock_keyboards, mock_crud, mock_get_db):
    """
    Тест: главное меню отображается корректно, когда вакансия выбрана.
    """
    # --- Mocks ---
    update = AsyncMock()
    context = MagicMock()
    context.user_data = {'selected_vacancy_id': 1}

    mock_user = models.User(id=1, chat_id=123)
    mock_resume = models.Resume(id=1, user_id=1, title="My Resume")
    mock_vacancies = [models.Vacancy(id=1, user_id=1, title="Vacancy 1")]
    mock_selected_vacancy = models.Vacancy(id=1, user_id=1, title="Vacancy 1")

    db_mock = MagicMock()
    mock_get_db.return_value = iter([db_mock])
    db_mock.query.return_value.filter_by.return_value.first.return_value = None


    mock_crud.get_or_create_user.return_value = mock_user
    mock_crud.get_user_resume.return_value = mock_resume
    mock_crud.get_user_vacancies.return_value = mock_vacancies
    mock_crud.get_vacancy_by_id.return_value = mock_selected_vacancy
    mock_crud.get_active_survey.return_value = None
    mock_crud.get_active_purchase.return_value = None
    mock_keyboards.main_menu_keyboard.return_value = "main_menu_keyboard_markup"

    # --- Call ---
    await show_main_menu(update, context)

    # --- Assertions ---
    balance_text = messages.BALANCE_MESSAGE.format(runs_left=0, runs_total=0)
    expected_message = messages.MAIN_MENU_WITH_VACANCY_MESSAGE.format(
        vacancy_title="Vacancy 1",
        resume_title="My Resume",
        balance_info=balance_text
    )
    update.callback_query.edit_message_text.assert_called_once_with(
        expected_message,
        reply_markup="main_menu_keyboard_markup"
    )
    mock_keyboards.main_menu_keyboard.assert_called_once_with(
        vacancy_count=1,
        has_resume=True,
        has_selected_vacancy=True,
        show_survey_button=False
    )

@pytest.mark.anyio
@patch('bot.handlers.main_menu_helpers.get_db')
@patch('bot.handlers.main_menu_helpers.crud')
@patch('bot.handlers.main_menu_helpers.keyboards')
async def test_show_main_menu_no_selected_vacancy(mock_keyboards, mock_crud, mock_get_db):
    """
    Тест: главное меню отображается корректно, когда вакансия не выбрана, но вакансии есть.
    """
    # --- Mocks ---
    update = AsyncMock()
    context = MagicMock()
    context.user_data = {}

    mock_user = models.User(id=1, chat_id=123)
    mock_resume = models.Resume(id=1, user_id=1, title="My Resume")
    mock_vacancies = [models.Vacancy(id=1, user_id=1, title="Vacancy 1")]

    db_mock = MagicMock()
    mock_get_db.return_value = iter([db_mock])
    db_mock.query.return_value.filter_by.return_value.first.return_value = None

    mock_crud.get_or_create_user.return_value = mock_user
    mock_crud.get_user_resume.return_value = mock_resume
    mock_crud.get_user_vacancies.return_value = mock_vacancies
    mock_crud.get_active_survey.return_value = None
    mock_crud.get_active_purchase.return_value = None
    mock_keyboards.main_menu_keyboard.return_value = "main_menu_keyboard_markup"

    # --- Call ---
    await show_main_menu(update, context)

    # --- Assertions ---
    balance_text = messages.BALANCE_MESSAGE.format(runs_left=0, runs_total=0)
    expected_message = messages.MAIN_MENU_MESSAGE.format(
        resume_title="My Resume",
        balance_info=balance_text
    )
    update.callback_query.edit_message_text.assert_called_once_with(
        expected_message,
        reply_markup="main_menu_keyboard_markup"
    )
    mock_keyboards.main_menu_keyboard.assert_called_once_with(
        vacancy_count=1,
        has_resume=True,
        has_selected_vacancy=False,
        show_survey_button=False
    )

@pytest.mark.anyio
@patch('bot.handlers.main_menu_helpers.get_db')
@patch('bot.handlers.main_menu_helpers.crud')
@patch('bot.handlers.main_menu_helpers.keyboards')
async def test_show_main_menu_no_vacancies(mock_keyboards, mock_crud, mock_get_db):
    """
    Тест: главное меню отображается корректно, когда нет сохраненных вакансий.
    """
    # --- Mocks ---
    update = AsyncMock()
    context = MagicMock()
    context.user_data = {}

    mock_user = models.User(id=1, chat_id=123)
    mock_resume = models.Resume(id=1, user_id=1, title="My Resume")

    db_mock = MagicMock()
    mock_get_db.return_value = iter([db_mock])
    db_mock.query.return_value.filter_by.return_value.first.return_value = None

    mock_crud.get_or_create_user.return_value = mock_user
    mock_crud.get_user_resume.return_value = mock_resume
    mock_crud.get_user_vacancies.return_value = []
    mock_crud.get_active_survey.return_value = None
    mock_crud.get_active_purchase.return_value = None
    mock_keyboards.main_menu_keyboard.return_value = "main_menu_keyboard_markup"

    # --- Call ---
    await show_main_menu(update, context)

    # --- Assertions ---
    balance_text = messages.BALANCE_MESSAGE.format(runs_left=0, runs_total=0)
    expected_message = messages.MAIN_MENU_NO_VACANCIES.format(
        resume_title="My Resume",
        balance_info=balance_text
    )
    update.callback_query.edit_message_text.assert_called_once_with(
        expected_message,
        reply_markup="main_menu_keyboard_markup"
    )
    mock_keyboards.main_menu_keyboard.assert_called_once_with(
        vacancy_count=0,
        has_resume=True,
        has_selected_vacancy=False,
        show_survey_button=False
    )

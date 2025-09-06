import pytest
from unittest.mock import AsyncMock, MagicMock, patch, call, ANY

from bot.handlers.start import start
from bot.handlers.states import AWAITING_RESUME_UPLOAD, AWAITING_VACANCY_UPLOAD, MAIN_MENU
from db import models
from bot import messages, keyboards


@pytest.mark.anyio
@patch('bot.handlers.start.keyboards')
@patch('bot.handlers.start.crud')
@patch('bot.handlers.start.get_db')
async def test_start_no_resume(mock_get_db, mock_crud, mock_keyboards, update_mock, context_mock):
    """
    Тестирует команду /start, когда у пользователя еще нет резюме.
    """
    # --- Mocks Setup ---
    mock_db = MagicMock()
    mock_user = models.User(id=1, chat_id=12345)
    mock_crud.get_or_create_user.return_value = mock_user
    mock_crud.get_user_resume.return_value = None  # No resume
    mock_get_db.return_value = iter([mock_db])
    mock_keyboards.cancel_keyboard.return_value = "cancel_keyboard_markup"

    # --- Call ---
    result = await start(update_mock, context_mock)

    # --- Assertions ---
    assert result == AWAITING_RESUME_UPLOAD

    expected_calls = [
        call(messages.WELCOME_MESSAGE),
        call(
            messages.ASK_FOR_RESUME,
            reply_markup="cancel_keyboard_markup",
        ),
    ]
    update_mock.message.reply_text.assert_has_calls(expected_calls, any_order=False)


@pytest.mark.anyio
@patch('bot.handlers.start.keyboards')
@patch('bot.handlers.start.crud')
@patch('bot.handlers.start.get_db')
async def test_start_with_resume_no_vacancies(mock_get_db, mock_crud, mock_keyboards, update_mock, context_mock):
    """
    Тестирует команду /start, когда у пользователя есть резюме, но нет вакансий.
    """
    # --- Mocks Setup ---
    mock_db = MagicMock()
    mock_user = models.User(id=1, chat_id=12345)
    mock_resume = models.Resume(id=1, user_id=1, file_path="path", source="test", title="My Resume Title")
    mock_crud.get_or_create_user.return_value = mock_user
    mock_crud.get_user_resume.return_value = mock_resume
    mock_crud.get_user_vacancies.return_value = []  # No vacancies
    mock_crud.get_active_purchase.return_value = None
    mock_get_db.return_value = iter([mock_db])
    mock_keyboards.cancel_keyboard.return_value = "cancel_keyboard_markup"

    # --- Call ---
    result = await start(update_mock, context_mock)

    # --- Assertions ---
    assert result == AWAITING_VACANCY_UPLOAD

    balance_text = messages.BALANCE_MESSAGE.format(runs_left=0, runs_total=0)
    expected_main_menu_message = messages.MAIN_MENU_NO_VACANCIES.format(
        resume_title="My Resume Title",
        balance_info=balance_text
    )
    expected_calls = [
        call(expected_main_menu_message),
        call(
            messages.ASK_FOR_VACANCY,
            reply_markup="cancel_keyboard_markup",
        ),
    ]
    update_mock.message.reply_text.assert_has_calls(expected_calls, any_order=False)


@pytest.mark.anyio
@patch('bot.handlers.start.show_main_menu', new_callable=AsyncMock)
@patch('bot.handlers.start.crud')
@patch('bot.handlers.start.get_db')
async def test_start_with_resume_and_vacancies(mock_get_db, mock_crud, mock_show_main_menu, update_mock, context_mock):
    """
    Тестирует команду /start, когда у пользователя есть и резюме, и вакансии.
    """
    # --- Mocks Setup ---
    mock_db = MagicMock()
    mock_user = models.User(id=1, chat_id=12345)
    mock_resume = models.Resume(id=1, user_id=1, file_path="path", source="test", title="My Awesome Resume")
    mock_vacancy = models.Vacancy(id=1, user_id=1, title="DevOps", file_path="path", source="test")
    mock_crud.get_or_create_user.return_value = mock_user
    mock_crud.get_user_resume.return_value = mock_resume
    mock_crud.get_user_vacancies.return_value = [mock_vacancy]
    mock_get_db.return_value = iter([mock_db])

    # --- Call ---
    result = await start(update_mock, context_mock)

    # --- Assertions ---
    assert result == MAIN_MENU
    assert context_mock.user_data['selected_vacancy_id'] == 1
    update_mock.message.reply_text.assert_not_called()
    mock_show_main_menu.assert_called_once_with(update_mock, context_mock)


@pytest.mark.anyio
@patch('bot.handlers.start.crud')
@patch('bot.handlers.start.get_db')
async def test_start_with_deeplink_arg(mock_get_db, mock_crud, update_mock, context_mock):
    """
    Тестирует команду /start с deeplink аргументом (UTM-меткой).
    """
    # --- Mocks Setup ---
    mock_db = MagicMock()
    mock_user = models.User(id=1, chat_id=12345)
    mock_crud.get_or_create_user.return_value = mock_user
    mock_crud.get_user_resume.return_value = None # Для простоты, пусть у пользователя нет резюме
    mock_get_db.return_value = iter([mock_db])
    context_mock.args = ["ads_google"] # Эмулируем deeplink ?start=ads_google

    # --- Call ---
    await start(update_mock, context_mock)

    # --- Assertions ---
    # Проверяем, что была вызвана функция сохранения UTM-метки
    mock_crud.create_utm_track.assert_called_once_with(
        mock_db,
        user_id=mock_user.id,
        utm_source="ads_google"
    )

    # Проверяем, что остальная логика start() продолжает выполняться
    # (в данном случае, запрос резюме)
    update_mock.message.reply_text.assert_called_with(
        messages.ASK_FOR_RESUME,
        reply_markup=ANY,
    )

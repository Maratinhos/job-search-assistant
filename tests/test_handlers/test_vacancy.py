import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from telegram import Document, File
from bot.handlers.vacancy import (
    handle_vacancy_file,
    handle_vacancy_url,
    handle_invalid_vacancy_input,
)
from bot.handlers.states import AWAITING_VACANCY_UPLOAD, MAIN_MENU
from bot import messages
from bot.utils import escape_markdown_v2

# Фикстуры update_mock и context_mock из conftest.py используются неявно

@pytest.mark.anyio
@patch('bot.handlers.vacancy.show_main_menu', new_callable=AsyncMock)
@patch('bot.handlers.vacancy.process_document', new_callable=AsyncMock)
@patch('bot.handlers.vacancy.crud')
@patch('bot.handlers.vacancy.get_db')
async def test_handle_vacancy_file_success(
    mock_get_db, mock_crud, mock_process_document, mock_show_main_menu, update_mock, context_mock
):
    """Тестирует успешную обработку файла вакансии, когда сервис возвращает success."""
    # --- Mocks ---
    mock_db = MagicMock()
    mock_get_db.return_value = iter([mock_db])
    mock_crud.get_or_create_user.return_value = MagicMock(id=1, chat_id=12345)
    mock_process_document.return_value = (True, "Senior Python Developer") # Сервис успешен

    mock_document = MagicMock(spec=Document)
    mock_document.file_name = "vacancy.txt"
    mock_file = AsyncMock(spec=File)
    mock_file.download_as_bytearray.return_value = b"Vacancy text"
    mock_document.get_file.return_value = mock_file
    update_mock.message.document = mock_document

    # --- Call ---
    result = await handle_vacancy_file(update_mock, context_mock)

    # --- Asserts ---
    mock_process_document.assert_called_once()
    assert any(
        escape_markdown_v2(messages.VACANCY_UPLOADED_SUCCESS) in call.args[0]
        for call in update_mock.message.reply_text.call_args_list
    )
    mock_show_main_menu.assert_called_once()
    assert result == MAIN_MENU

@pytest.mark.anyio
@patch('bot.handlers.vacancy.process_document', new_callable=AsyncMock)
@patch('bot.handlers.vacancy.crud')
@patch('bot.handlers.vacancy.get_db')
async def test_handle_vacancy_file_failure(
    mock_get_db, mock_crud, mock_process_document, update_mock, context_mock
):
    """Тестирует обработку файла вакансии, когда сервис возвращает failure."""
    # --- Mocks ---
    mock_db = MagicMock()
    mock_get_db.return_value = iter([mock_db])
    mock_crud.get_or_create_user.return_value = MagicMock(id=1, chat_id=12345)
    mock_process_document.return_value = (False, None) # Сервис провалился

    mock_document = MagicMock(spec=Document)
    mock_document.file_name = "vacancy.txt"
    mock_file = AsyncMock(spec=File)
    mock_file.download_as_bytearray.return_value = b"Vacancy text"
    mock_document.get_file.return_value = mock_file
    update_mock.message.document = mock_document

    # --- Call ---
    result = await handle_vacancy_file(update_mock, context_mock)

    # --- Asserts ---
    mock_process_document.assert_called_once()
    assert any(
        escape_markdown_v2(messages.VACANCY_VERIFICATION_FAILED) in call.args[0]
        for call in update_mock.message.reply_text.call_args_list
    )
    assert result == AWAITING_VACANCY_UPLOAD


@pytest.mark.anyio
@patch('bot.handlers.vacancy.show_main_menu', new_callable=AsyncMock)
@patch('bot.handlers.vacancy.scrape_hh_url', return_value="Vacancy from URL")
@patch('bot.handlers.vacancy.process_document', new_callable=AsyncMock)
@patch('bot.handlers.vacancy.crud')
@patch('bot.handlers.vacancy.get_db')
async def test_handle_vacancy_url_success(
    mock_get_db, mock_crud, mock_process_document, mock_scrape, mock_show_main_menu, update_mock, context_mock
):
    """Тестирует успешную обработку URL вакансии."""
    # --- Mocks ---
    mock_db = MagicMock()
    mock_get_db.return_value = iter([mock_db])
    mock_crud.get_or_create_user.return_value = MagicMock(id=1, chat_id=12345)
    mock_process_document.return_value = (True, "Scraped Vacancy")
    update_mock.message.text = "https://hh.ru/vacancy/123"

    # --- Call ---
    result = await handle_vacancy_url(update_mock, context_mock)

    # --- Asserts ---
    mock_scrape.assert_called_once_with("https://hh.ru/vacancy/123")
    mock_process_document.assert_called_once()
    mock_show_main_menu.assert_called_once()
    assert result == MAIN_MENU

@pytest.mark.anyio
async def test_handle_invalid_vacancy_input(update_mock, context_mock):
    """Тестирует, что бот корректно обрабатывает невалидный ввод."""
    update_mock.message.text = "просто текст"
    update_mock.message.document = None

    result = await handle_invalid_vacancy_input(update_mock, context_mock)

    update_mock.message.reply_text.assert_called_once()
    assert escape_markdown_v2(messages.VACANCY_INVALID_FORMAT) in update_mock.message.reply_text.call_args.args[0]
    assert result == AWAITING_VACANCY_UPLOAD

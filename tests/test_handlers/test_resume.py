import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from telegram import Document, File
from bot.handlers.resume import (
    handle_resume_file,
    handle_resume_url,
    handle_invalid_resume_input,
)
from bot.handlers.states import AWAITING_RESUME_UPLOAD, MAIN_MENU
from bot import messages
from bot.utils import escape_markdown_v2

# Фикстуры update_mock и context_mock из conftest.py используются неявно

@pytest.mark.anyio
@patch('bot.handlers.resume.show_main_menu', new_callable=AsyncMock)
@patch('bot.handlers.resume.process_document', new_callable=AsyncMock)
@patch('bot.handlers.resume.crud')
@patch('bot.handlers.resume.get_db')
async def test_handle_resume_file_success(
    mock_get_db, mock_crud, mock_process_document, mock_show_main_menu, update_mock, context_mock
):
    """Тестирует успешную обработку файла резюме, когда сервис возвращает success."""
    # --- Mocks ---
    mock_db = MagicMock()
    mock_get_db.return_value = iter([mock_db])
    mock_crud.get_or_create_user.return_value = MagicMock(id=1, chat_id=12345)
    mock_process_document.return_value = (True, "Senior Python Developer") # Сервис успешен

    mock_document = MagicMock(spec=Document)
    mock_document.file_name = "resume.txt"
    mock_file = AsyncMock(spec=File)
    mock_file.download_as_bytearray.return_value = b"Resume text"
    mock_document.get_file.return_value = mock_file
    update_mock.message.document = mock_document

    # --- Call ---
    result = await handle_resume_file(update_mock, context_mock)

    # --- Asserts ---
    mock_process_document.assert_called_once()
    assert any(
        escape_markdown_v2(messages.RESUME_UPLOADED_SUCCESS) in call.args[0]
        for call in update_mock.message.reply_text.call_args_list
    )
    mock_show_main_menu.assert_called_once()
    assert result == MAIN_MENU


@pytest.mark.anyio
@patch('bot.handlers.resume.process_document', new_callable=AsyncMock)
@patch('bot.handlers.resume.crud')
@patch('bot.handlers.resume.get_db')
async def test_handle_resume_file_failure(
    mock_get_db, mock_crud, mock_process_document, update_mock, context_mock
):
    """Тестирует обработку файла резюме, когда сервис возвращает failure."""
    # --- Mocks ---
    mock_db = MagicMock()
    mock_get_db.return_value = iter([mock_db])
    mock_crud.get_or_create_user.return_value = MagicMock(id=1, chat_id=12345)
    mock_process_document.return_value = (False, None) # Сервис провалился

    mock_document = MagicMock(spec=Document)
    mock_document.file_name = "resume.txt"
    mock_file = AsyncMock(spec=File)
    mock_file.download_as_bytearray.return_value = b"Resume text"
    mock_document.get_file.return_value = mock_file
    update_mock.message.document = mock_document

    # --- Call ---
    result = await handle_resume_file(update_mock, context_mock)

    # --- Asserts ---
    mock_process_document.assert_called_once()
    assert any(
        escape_markdown_v2(messages.RESUME_VERIFICATION_FAILED) in call.args[0]
        for call in update_mock.message.reply_text.call_args_list
    )
    assert result == AWAITING_RESUME_UPLOAD


@pytest.mark.anyio
@patch('bot.handlers.resume.show_main_menu', new_callable=AsyncMock)
@patch('bot.handlers.resume.scrape_hh_url', return_value="Resume from URL")
@patch('bot.handlers.resume.process_document', new_callable=AsyncMock)
@patch('bot.handlers.resume.crud')
@patch('bot.handlers.resume.get_db')
async def test_handle_resume_url_success(
    mock_get_db, mock_crud, mock_process_document, mock_scrape, mock_show_main_menu, update_mock, context_mock
):
    """Тестирует успешную обработку URL резюме."""
    # --- Mocks ---
    mock_db = MagicMock()
    mock_get_db.return_value = iter([mock_db])
    mock_crud.get_or_create_user.return_value = MagicMock(id=1, chat_id=12345)
    mock_process_document.return_value = (True, "Scraped Developer")
    update_mock.message.text = "https://hh.ru/resume/123"

    # --- Call ---
    result = await handle_resume_url(update_mock, context_mock)

    # --- Asserts ---
    mock_scrape.assert_called_once_with("https://hh.ru/resume/123")
    mock_process_document.assert_called_once()
    mock_show_main_menu.assert_called_once()
    assert result == MAIN_MENU


@pytest.mark.anyio
async def test_handle_invalid_resume_input(update_mock, context_mock):
    """Тестирует, что бот корректно обрабатывает невалидный ввод."""
    update_mock.message.text = "просто текст"
    update_mock.message.document = None

    result = await handle_invalid_resume_input(update_mock, context_mock)

    update_mock.message.reply_text.assert_called_once()
    assert escape_markdown_v2(messages.RESUME_INVALID_FORMAT) in update_mock.message.reply_text.call_args.args[0]
    assert result == AWAITING_RESUME_UPLOAD

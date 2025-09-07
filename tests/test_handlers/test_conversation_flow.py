import pytest
from unittest.mock import patch, AsyncMock, MagicMock
from telegram import Document

from bot.handlers.start import start
from bot.handlers.resume import handle_resume_file
from bot.handlers.vacancy import handle_vacancy_file
from bot.handlers.states import AWAITING_RESUME_UPLOAD, AWAITING_VACANCY_UPLOAD, MAIN_MENU
from db import crud, models


@pytest.mark.anyio
@patch("bot.handlers.vacancy.crud")
@patch("bot.handlers.resume.crud")
@patch("bot.handlers.start.crud")
@patch("bot.handlers.vacancy.show_main_menu", new_callable=AsyncMock)
@patch("bot.handlers.resume.show_main_menu", new_callable=AsyncMock)
@patch("bot.handlers.start.get_db")
@patch("bot.handlers.resume.get_db")
@patch("bot.handlers.vacancy.get_db")
async def test_conversation_flow(
    mock_vacancy_get_db,
    mock_resume_get_db,
    mock_start_get_db,
    mock_resume_show_main_menu,
    mock_vacancy_show_main_menu,
    mock_start_crud,
    mock_resume_crud,
    mock_vacancy_crud,
    db_session,
    update_mock,
    context_mock,
):
    """
    Tests the conversation flow by calling handlers in sequence.
    """
    # Mock get_db to be a generator that yields the test session
    def db_session_generator():
        yield db_session

    mock_start_get_db.side_effect = db_session_generator
    mock_resume_get_db.side_effect = db_session_generator
    mock_vacancy_get_db.side_effect = db_session_generator

    # Mock crud methods for all handlers
    user = MagicMock(id=1, chat_id=12345)
    resume = MagicMock(id=1)
    mock_start_crud.get_or_create_user.return_value = user
    mock_start_crud.get_user_resume.return_value = None  # Start with no resume
    mock_resume_crud.get_or_create_user.return_value = user
    mock_resume_crud.get_user_resume.return_value = None
    mock_resume_crud.get_user_vacancies.return_value = [] # No vacancies yet
    mock_resume_crud.get_user_balance.return_value = MagicMock(balance=10)
    mock_vacancy_crud.get_or_create_user.return_value = user
    mock_vacancy_crud.get_user_resume.return_value = resume
    mock_vacancy_crud.get_user_balance.return_value = MagicMock(balance=10)


    async def mock_process_document(update, context, db, user_id, text, source, doc_type):
        if doc_type == "resume":
            mock_resume_crud.create_resume.return_value = MagicMock(id=1, title="Test Resume")
            return True, mock_resume_crud.create_resume.return_value
        elif doc_type == "vacancy":
            mock_vacancy_crud.create_vacancy.return_value = MagicMock(id=1, title="Test Vacancy")
            return True, mock_vacancy_crud.create_vacancy.return_value
        return False, None

    with patch("bot.handlers.resume.process_document", new=mock_process_document), \
         patch("bot.handlers.vacancy.process_document", new=mock_process_document):

        # 1. /start (no resume) -> AWAITING_RESUME_UPLOAD
        context_mock.args = []  # Убедимся, что тест не передает deeplink аргументы
        state = await start(update_mock, context_mock)
        assert state == AWAITING_RESUME_UPLOAD

        # After start, user has a resume
        mock_start_crud.get_user_resume.return_value = resume
        mock_resume_crud.get_user_resume.return_value = resume

        # 2. Upload resume -> AWAITING_VACANCY_UPLOAD
        mock_document = MagicMock(spec=Document)
        mock_document.file_name = "resume.txt"
        mock_file = AsyncMock()
        mock_file.download_as_bytearray.return_value = b"Resume text"
        mock_document.get_file.return_value = mock_file
        update_mock.message.document = mock_document

        state = await handle_resume_file(update_mock, context_mock)
        assert state == AWAITING_VACANCY_UPLOAD

        # After resume upload, user has vacancies
        mock_vacancy_crud.get_user_vacancies.return_value = [MagicMock(id=1)]

        # 3. Upload vacancy -> MAIN_MENU
        mock_document.file_name = "vacancy.txt"
        mock_file.download_as_bytearray.return_value = b"Vacancy text"
        update_mock.message.document = mock_document

        state = await handle_vacancy_file(update_mock, context_mock)
        assert state == MAIN_MENU
        mock_vacancy_show_main_menu.assert_called_once()

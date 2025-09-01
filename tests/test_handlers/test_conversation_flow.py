import pytest
from unittest.mock import patch, AsyncMock, MagicMock
from telegram import Document

from bot.handlers.start import start
from bot.handlers.resume import handle_resume_file
from bot.handlers.vacancy import handle_vacancy_file
from bot.handlers.states import AWAITING_RESUME_UPLOAD, AWAITING_VACANCY_UPLOAD, MAIN_MENU
from db import crud, models

@pytest.mark.anyio
@patch("bot.handlers.vacancy.show_main_menu", new_callable=AsyncMock)
@patch("bot.handlers.resume.show_main_menu", new_callable=AsyncMock)
async def test_conversation_flow(
    mock_resume_show_main_menu,
    mock_vacancy_show_main_menu,
    db_session,
    update_mock,
    context_mock,
):
    """
    Tests the conversation flow by calling handlers in sequence.
    """
    async def mock_process_document(update, context, db, user_id, text, source, doc_type):
        if doc_type == "resume":
            # In a real scenario, the document service would create the resume.
            # Here, we simulate this by creating it directly.
            crud.create_resume(db, user_id, "test.txt", source, "Test Resume")
            return True, "Test Resume"
        elif doc_type == "vacancy":
            crud.create_vacancy(db, user_id, "test.txt", source, "Test Vacancy")
            return True, "Test Vacancy"
        return False, None

    with patch("bot.handlers.resume.process_document", new=mock_process_document):
        with patch("bot.handlers.vacancy.process_document", new=mock_process_document):
            # 1. /start (no resume) -> AWAITING_RESUME_UPLOAD
            state = await start(update_mock, context_mock)
            assert state == AWAITING_RESUME_UPLOAD

            # 2. Upload resume -> AWAITING_VACANCY_UPLOAD
            mock_document = MagicMock(spec=Document)
            mock_document.file_name = "resume.txt"
            mock_file = AsyncMock()
            mock_file.download_as_bytearray.return_value = b"Resume text"
            mock_document.get_file.return_value = mock_file
            update_mock.message.document = mock_document

            state = await handle_resume_file(update_mock, context_mock)
            assert state == AWAITING_VACANCY_UPLOAD

            # 3. Upload vacancy -> MAIN_MENU
            mock_document.file_name = "vacancy.txt"
            mock_file.download_as_bytearray.return_value = b"Vacancy text"
            update_mock.message.document = mock_document

            state = await handle_vacancy_file(update_mock, context_mock)
            assert state == MAIN_MENU
            mock_vacancy_show_main_menu.assert_called_once()

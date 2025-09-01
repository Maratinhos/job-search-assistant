import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from telegram import Update, User, Message, Document, File
from telegram.ext import ConversationHandler, ContextTypes

from bot.handlers.resume import (
    handle_resume_file,
    process_resume_text,
    AWAITING_RESUME_UPLOAD,
    AWAITING_VACANCY_UPLOAD,
    handle_invalid_resume_input,
)
from db import models

# Используем фикстуры update_mock и context_mock из conftest.py

@pytest.mark.anyio
@patch('bot.handlers.resume.process_resume_text', new_callable=AsyncMock)
async def test_handle_resume_file_success(mock_process_resume, update_mock, context_mock):
    """Тестирует успешную обработку файла резюме."""
    mock_document = MagicMock(spec=Document)
    mock_document.file_name = "resume.txt"
    mock_file = AsyncMock()
    mock_file.download_as_bytearray.return_value = b"Resume text"
    mock_document.get_file.return_value = mock_file
    update_mock.message.document = mock_document

    await handle_resume_file(update_mock, context_mock)

    mock_process_resume.assert_called_once_with(
        update_mock, context_mock, "Resume text", source="resume.txt"
    )

@pytest.mark.anyio
@patch('bot.handlers.resume.get_ai_client')
@patch('bot.handlers.resume.crud')
@patch('bot.handlers.resume.save_text_to_file', return_value="some/path/resume.txt")
@patch('bot.handlers.resume.get_db')
async def test_process_resume_text_success(
    mock_get_db, mock_save_text, mock_crud, mock_get_ai_client,
    update_mock, context_mock  # Добавляем фикстуры
):
    """
    Тестирует успешный сценарий обработки текста резюме, включая логирование.
    """
    # --- Mocks Setup ---
    mock_ai_client = MagicMock()
    mock_ai_client.verify_resume.return_value = {
        "text": '{"is_resume": true, "title": "Senior Python Developer"}',
        "usage": {
            "cost": 0.002,
            "prompt_tokens": 50,
            "completion_tokens": 150,
            "total_tokens": 200,
        }
    }
    mock_get_ai_client.return_value = mock_ai_client

    mock_db = MagicMock()
    mock_user = models.User(id=1, chat_id=12345) # ID из фикстуры
    mock_crud.get_or_create_user.return_value = mock_user
    mock_get_db.return_value = iter([mock_db])

    # --- Call ---
    result = await process_resume_text(update_mock, context_mock, "resume text", "test_source")

    # --- Assertions ---
    mock_ai_client.verify_resume.assert_called_once_with("resume text")
    mock_crud.get_or_create_user.assert_called_once_with(mock_db, chat_id=12345)

    mock_crud.create_ai_usage_log.assert_called_once_with(
        db=mock_db,
        user_id=mock_user.id,
        prompt_tokens=50,
        completion_tokens=150,
        total_tokens=200,
        cost=0.002,
        action="verify_resume",
    )
    mock_save_text.assert_called_once_with("resume text", "resumes")
    mock_crud.create_resume.assert_called_once_with(
        mock_db,
        user_id=mock_user.id,
        file_path="some/path/resume.txt",
        source="test_source",
        title="Senior Python Developer"
    )

    assert result == AWAITING_VACANCY_UPLOAD
    update_mock.message.reply_text.assert_called()


@pytest.mark.anyio
@patch('bot.handlers.resume.get_ai_client')
@patch('bot.handlers.resume.crud')
@patch('bot.handlers.resume.get_db')
async def test_process_resume_text_verification_failed(
    mock_get_db, mock_crud, mock_get_ai_client,
    update_mock, context_mock # Добавляем фикстуры
):
    """
    Тестирует сценарий, когда AI не подтверждает, что текст является резюме.
    """
    # --- Mocks Setup ---
    mock_ai_client = MagicMock()
    mock_ai_client.verify_resume.return_value = {
        "text": '{"is_resume": false, "title": null}',
        "usage": {
            "cost": 0.001,
            "prompt_tokens": 30,
            "completion_tokens": 20,
            "total_tokens": 50,
        }
    }
    mock_get_ai_client.return_value = mock_ai_client

    mock_db = MagicMock()
    mock_user = models.User(id=1, chat_id=12345)
    mock_crud.get_or_create_user.return_value = mock_user
    mock_get_db.return_value = iter([mock_db])

    # --- Call ---
    result = await process_resume_text(update_mock, context_mock, "not a resume", "test")

    # --- Assertions ---
    mock_crud.create_ai_usage_log.assert_called_once_with(
        db=mock_db,
        user_id=mock_user.id,
        prompt_tokens=30,
        completion_tokens=20,
        total_tokens=50,
        cost=0.001,
        action="verify_resume",
    )
    mock_crud.create_resume.assert_not_called()

    assert result == AWAITING_RESUME_UPLOAD
    # Проверяем, что пользователю сообщили об ошибке
    # (в `process_resume_text` несколько вызовов `reply_text`)
    update_mock.message.reply_text.assert_called()
    # Проверяем, что один из вызовов содержал нужное сообщение
    any_call_had_error_msg = any(
        "не похож на резюме" in call.args[0]
        for call in update_mock.message.reply_text.call_args_list
    )
    assert any_call_had_error_msg


@pytest.mark.anyio
@patch('bot.handlers.resume.get_ai_client')
@patch('bot.handlers.resume.crud')
@patch('bot.handlers.resume.get_db')
async def test_process_resume_text_invalid_json(
    mock_get_db, mock_crud, mock_get_ai_client,
    update_mock, context_mock
):
    """
    Тестирует сценарий, когда AI возвращает некорректный JSON.
    """
    # --- Mocks Setup ---
    mock_ai_client = MagicMock()
    # Ответ AI - это невалидный JSON
    mock_ai_client.verify_resume.return_value = {
        "text": '{"is_resume": true, "title": "Missing Quote}',
        "usage": {"cost": 0.001, "total_tokens": 50}
    }
    mock_get_ai_client.return_value = mock_ai_client

    mock_db = MagicMock()
    mock_user = models.User(id=1, chat_id=12345)
    mock_crud.get_or_create_user.return_value = mock_user
    mock_get_db.return_value = iter([mock_db])

    # --- Call ---
    result = await process_resume_text(update_mock, context_mock, "some text", "test")

    # --- Assertions ---
    # Логирование должно произойти в любом случае
    mock_crud.create_ai_usage_log.assert_called_once()
    # Резюме не должно быть создано
    mock_crud.create_resume.assert_not_called()
    # Пользователь должен получить сообщение об ошибке
    any_call_had_error_msg = any(
        "не похож на резюме" in call.args[0]
        for call in update_mock.message.reply_text.call_args_list
    )
    assert any_call_had_error_msg
    # Должны остаться в том же состоянии
    assert result == AWAITING_RESUME_UPLOAD


@pytest.mark.anyio
async def test_handle_invalid_resume_input_photo(update_mock, context_mock):
    """
    Тестирует, что бот корректно обрабатывает получение фото
    в состоянии ожидания резюме.
    """
    # Мокируем сообщение с фото
    update_mock.message.photo = [MagicMock()]
    update_mock.message.document = None
    update_mock.message.text = ""

    # Вызываем обработчик для невалидного ввода
    result = await handle_invalid_resume_input(update_mock, context_mock)

    # Проверяем, что бот отправил сообщение о неверном формате
    update_mock.message.reply_text.assert_called_once()
    assert "неверный формат" in update_mock.message.reply_text.call_args.args[0].lower()

    # Проверяем, что состояние не изменилось
    assert result == AWAITING_RESUME_UPLOAD

@pytest.mark.anyio
async def test_handle_resume_file_download_error(update_mock, context_mock):
    """
    Тестирует обработку ошибки при скачивании файла из Telegram.
    """
    # --- Mocks Setup ---
    mock_document = MagicMock(spec=Document)
    mock_document.file_name = "resume.txt"

    # Мокируем get_file, чтобы он возвращал мок файла
    mock_file = AsyncMock(spec=File)
    # Мокируем download_as_bytearray, чтобы он вызывал ошибку
    mock_file.download_as_bytearray.side_effect = Exception("Download failed")
    mock_document.get_file.return_value = mock_file

    update_mock.message.document = mock_document

    # --- Call ---
    result = await handle_resume_file(update_mock, context_mock)

    # --- Assertions ---
    # Проверяем, что пользователю отправили сообщение об ошибке
    update_mock.message.reply_text.assert_called_once()
    assert "ошибка при загрузке файла" in update_mock.message.reply_text.call_args.args[0].lower()

    # Проверяем, что мы остались в том же состоянии
    assert result == AWAITING_RESUME_UPLOAD

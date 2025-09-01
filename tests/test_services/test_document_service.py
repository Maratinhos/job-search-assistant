import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from services.document_service import process_document
from db import models

# Фикстуры update_mock и context_mock из conftest.py используются неявно

@pytest.mark.anyio
@patch('services.document_service.get_ai_client')
@patch('services.document_service.crud')
@patch('services.document_service.save_text_to_file', return_value="some/path/resume.txt")
async def test_process_document_resume_success(
    mock_save_text, mock_crud, mock_get_ai_client, update_mock, context_mock
):
    """Тестирует успешную обработку РЕЗЮМЕ через process_document."""
    # --- Mocks ---
    mock_db = MagicMock()
    mock_ai_client = MagicMock()
    mock_ai_client.verify_resume.return_value = {
        "text": '{"is_resume": true, "title": "Test Resume"}',
        "usage": {"cost": 0.001, "total_tokens": 100, "prompt_tokens": 50, "completion_tokens": 50},
    }
    mock_get_ai_client.return_value = mock_ai_client
    mock_user = models.User(id=1)
    mock_crud.get_or_create_user.return_value = mock_user

    # --- Call ---
    success, title = await process_document(
        update=update_mock,
        context=context_mock,
        db=mock_db,
        user_id=mock_user.id,
        text="Resume text",
        source="upload",
        doc_type="resume",
    )

    # --- Asserts ---
    assert success is True
    assert title == "Test Resume"
    mock_ai_client.verify_resume.assert_called_once_with("Resume text")
    mock_crud.create_ai_usage_log.assert_called_once()
    mock_save_text.assert_called_once_with("Resume text", "resumes")
    mock_crud.create_resume.assert_called_once()


@pytest.mark.anyio
@patch('services.document_service.get_ai_client')
@patch('services.document_service.crud')
@patch('services.document_service.save_text_to_file', return_value="some/path/vacancy.txt")
async def test_process_document_vacancy_success(
    mock_save_text, mock_crud, mock_get_ai_client, update_mock, context_mock
):
    """Тестирует успешную обработку ВАКАНСИИ через process_document."""
    # --- Mocks ---
    mock_db = MagicMock()
    mock_ai_client = MagicMock()
    # Мокируем метод для вакансии
    mock_ai_client.verify_vacancy.return_value = {
        "text": '{"is_vacancy": true, "title": "Test Vacancy"}',
        "usage": {"cost": 0.002, "total_tokens": 200, "prompt_tokens": 100, "completion_tokens": 100},
    }
    mock_get_ai_client.return_value = mock_ai_client
    mock_user = models.User(id=1)
    # Создаем мок для vacancy, который будет возвращен из create_vacancy
    mock_vacancy = models.Vacancy(id=99, title="Test Vacancy")
    mock_crud.create_vacancy.return_value = mock_vacancy


    # --- Call ---
    success, title = await process_document(
        update=update_mock,
        context=context_mock,
        db=mock_db,
        user_id=mock_user.id,
        text="Vacancy text",
        source="upload",
        doc_type="vacancy",
    )

    # --- Asserts ---
    assert success is True
    assert title == "Test Vacancy"
    mock_ai_client.verify_vacancy.assert_called_once_with("Vacancy text")
    mock_crud.create_ai_usage_log.assert_called_once()
    mock_save_text.assert_called_once_with("Vacancy text", "vacancies")
    mock_crud.create_vacancy.assert_called_once()
    # Проверяем, что ID вакансии сохранился в user_data
    assert context_mock.user_data['selected_vacancy_id'] == 99


@pytest.mark.anyio
@patch('services.document_service.get_ai_client')
@patch('services.document_service.crud')
async def test_process_document_ai_verification_fails(
    mock_crud, mock_get_ai_client, update_mock, context_mock
):
    """Тестирует случай, когда AI-валидация документа проваливается."""
    # --- Mocks ---
    mock_db = MagicMock()
    mock_ai_client = MagicMock()
    mock_ai_client.verify_resume.return_value = {"text": '{"is_resume": false}'}
    mock_get_ai_client.return_value = mock_ai_client
    mock_user = models.User(id=1)

    # --- Call ---
    success, title = await process_document(
        update=update_mock,
        context=context_mock,
        db=mock_db,
        user_id=mock_user.id,
        text="Invalid text",
        source="upload",
        doc_type="resume",
    )

    # --- Asserts ---
    assert success is False
    assert title is None
    mock_crud.create_resume.assert_not_called()
    mock_crud.create_vacancy.assert_not_called()

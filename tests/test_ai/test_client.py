import pytest
from ai.client import AIClient
from ai.providers.mock import MockProvider
from ai import prompts

# Фикстура, которая подменяет реального AI-провайдера на мок-версию перед каждым тестом.
@pytest.fixture(autouse=True)
def mock_ai_provider(monkeypatch):
    """
    Заменяет AIProvider на MockProvider для всех тестов в этом файле.
    `autouse=True` применяет эту фикстуру автоматически ко всем тестам.
    """
    monkeypatch.setattr("ai.client.AIProvider", MockProvider)

def test_verify_resume_returns_mock_response():
    """
    Тестирует, что `verify_resume` возвращает корректный ответ от `MockProvider`.
    """
    client = AIClient()
    response = client.verify_resume("some resume text")

    # Проверяем, что ответ соответствует тому, что должен вернуть MockProvider
    assert response["text"] == "да"
    assert "usage" in response
    assert response["usage"]["total_tokens"] > 0

def test_verify_vacancy_returns_mock_response():
    """
    Тестирует, что `verify_vacancy` возвращает корректный ответ от `MockProvider`.
    """
    client = AIClient()
    response = client.verify_vacancy("some vacancy text")
    assert response["text"] == "да"

def test_analyze_match_returns_mock_response():
    """
    Тестирует, что `analyze_match` возвращает корректный ответ от `MockProvider`.
    """
    client = AIClient()
    response = client.analyze_match("resume", "vacancy")
    assert "Анализ соответствия (MOCK)" in response["text"]

def test_generate_cover_letter_returns_mock_response():
    """
    Тестирует, что `generate_cover_letter` возвращает корректный ответ от `MockProvider`.
    """
    client = AIClient()
    response = client.generate_cover_letter("resume", "vacancy")
    assert "Сопроводительное письмо (MOCK)" in response["text"]

def test_generate_hr_call_plan_returns_mock_response():
    """
    Тестирует, что `generate_hr_call_plan` возвращает корректный ответ от `MockProvider`.
    """
    client = AIClient()
    response = client.generate_hr_call_plan("resume", "vacancy")
    assert "План для созвона с HR (MOCK)" in response["text"]

def test_generate_tech_interview_plan_returns_mock_response():
    """
    Тестирует, что `generate_tech_interview_plan` возвращает корректный ответ от `MockProvider`.
    """
    client = AIClient()
    response = client.generate_tech_interview_plan("resume", "vacancy")
    assert "План для технического собеседования (MOCK)" in response["text"]

import pytest
from ai.client import AIClient
from ai import prompts

# Фикстура для мока провайдера, чтобы не создавать его в каждом тесте
@pytest.fixture
def mock_provider(mocker):
    return mocker.patch('ai.client.AIProvider')

def test_verify_resume(mock_provider):
    """Тестирует, что `verify_resume` вызывает правильный метод провайдера с правильным промптом."""
    client = AIClient()
    client.verify_resume("some resume text")

    mock_provider.return_value.verify_text.assert_called_once_with(
        "some resume text", prompts.VERIFY_RESUME_PROMPT
    )

def test_verify_vacancy(mock_provider):
    """Тестирует, что `verify_vacancy` вызывает правильный метод провайдера с правильным промптом."""
    client = AIClient()
    client.verify_vacancy("some vacancy text")

    mock_provider.return_value.verify_text.assert_called_once_with(
        "some vacancy text", prompts.VERIFY_VACANCY_PROMPT
    )

def test_analyze_match(mock_provider):
    """Тестирует, что `analyze_match` вызывает `analyze` с правильными аргументами."""
    client = AIClient()
    client.analyze_match("resume", "vacancy")

    mock_provider.return_value.analyze.assert_called_once_with(
        prompts.ANALYZE_MATCH_PROMPT,
        resume_text="resume",
        vacancy_text="vacancy"
    )

def test_generate_cover_letter(mock_provider):
    """Тестирует, что `generate_cover_letter` вызывает `analyze` с правильными аргументами."""
    client = AIClient()
    client.generate_cover_letter("resume", "vacancy")

    mock_provider.return_value.analyze.assert_called_once_with(
        prompts.GENERATE_COVER_LETTER_PROMPT,
        resume_text="resume",
        vacancy_text="vacancy"
    )

def test_generate_hr_call_plan(mock_provider):
    """Тестирует, что `generate_hr_call_plan` вызывает `analyze` с правильными аргументами."""
    client = AIClient()
    client.generate_hr_call_plan("resume", "vacancy")

    mock_provider.return_value.analyze.assert_called_once_with(
        prompts.GENERATE_HR_CALL_PLAN_PROMPT,
        resume_text="resume",
        vacancy_text="vacancy"
    )

def test_generate_tech_interview_plan(mock_provider):
    """Тестирует, что `generate_tech_interview_plan` вызывает `analyze` с правильными аргументами."""
    client = AIClient()
    client.generate_tech_interview_plan("resume", "vacancy")

    mock_provider.return_value.analyze.assert_called_once_with(
        prompts.GENERATE_TECH_INTERVIEW_PLAN_PROMPT,
        resume_text="resume",
        vacancy_text="vacancy"
    )

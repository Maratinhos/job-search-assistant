import pytest
from ai.providers.mock import MockProvider
from ai import prompts

# --- Test Cases ---
test_cases = [
    (
        prompts.VERIFY_RESUME_PROMPT.format(text="some text"),
        '{"is_resume": true, "title": "Mock Resume Title"}',
        "Resume Verification"
    ),
    (
        prompts.VERIFY_VACANCY_PROMPT.format(text="some text"),
        '{"is_vacancy": true, "title": "Mock Vacancy Title"}',
        "Vacancy Verification"
    ),
    (
        prompts.ANALYZE_MATCH_PROMPT.format(resume_text="a", vacancy_text="b"),
        "Анализ соответствия (MOCK)",
        "Analysis"
    ),
    (
        prompts.GENERATE_COVER_LETTER_PROMPT.format(resume_text="a", vacancy_text="b"),
        "Сопроводительное письмо (MOCK)",
        "Cover Letter"
    ),
    (
        prompts.GENERATE_HR_CALL_PLAN_PROMPT.format(resume_text="a", vacancy_text="b"),
        "План для созвона с HR (MOCK)",
        "HR Call Plan"
    ),
    (
        prompts.GENERATE_TECH_INTERVIEW_PLAN_PROMPT.format(resume_text="a", vacancy_text="b"),
        "План для технического собеседования (MOCK)",
        "Tech Interview Plan"
    ),
]

@pytest.mark.parametrize("prompt, expected_response_part, description", test_cases)
def test_mock_provider_responses(prompt, expected_response_part, description):
    """
    Тестирует, что мок-провайдер возвращает ожидаемые ответы для разных промптов.
    """
    provider = MockProvider()
    response = provider._get_completion(prompt)

    # Для JSON-ответов проверяем точное совпадение, для остальных - вхождение подстроки.
    if expected_response_part.startswith('{'):
        assert response["text"] == expected_response_part, f"Failed on: {description}"
    else:
        assert expected_response_part in response["text"], f"Failed on: {description}"

    # Также проверяем, что 'usage' данные всегда присутствуют
    assert "usage" in response
    assert "total_tokens" in response["usage"]
    assert response["usage"]["total_tokens"] > 0

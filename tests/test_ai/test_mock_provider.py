from ai.providers.mock import MockProvider
from ai import prompts


def test_mock_provider_responses():
    """
    Тестирует, что мок-провайдер возвращает ожидаемые ответы для разных промптов.
    """
    provider = MockProvider()

    # Test resume verification
    resume_prompt = prompts.VERIFY_RESUME_PROMPT.format(text="some text")
    response = provider._get_completion(resume_prompt)
    assert response["text"] == "да"

    # Test vacancy verification
    vacancy_prompt = prompts.VERIFY_VACANCY_PROMPT.format(text="some text")
    response = provider._get_completion(vacancy_prompt)
    assert response["text"] == "да"

    # Test analysis
    analysis_prompt = prompts.ANALYZE_MATCH_PROMPT.format(
        resume_text="a", vacancy_text="b"
    )
    response = provider._get_completion(analysis_prompt)
    assert "Анализ соответствия (MOCK)" in response["text"]

    # Test cover letter
    cover_letter_prompt = prompts.GENERATE_COVER_LETTER_PROMPT.format(
        resume_text="a", vacancy_text="b"
    )
    response = provider._get_completion(cover_letter_prompt)
    assert "Сопроводительное письмо (MOCK)" in response["text"]

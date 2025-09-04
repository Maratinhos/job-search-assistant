import logging

logger = logging.getLogger(__name__)


class MockProvider:
    """
    Класс для мок-взаимодействия с API AI.
    Используется в тестах для изоляции от внешних сервисов.
    """

    def __init__(self, api_key: str = "mock_key"):
        # The key is not used, but we accept it to match the interface.
        logger.info("Инициализирован Mock AI провайдер.")

    def _get_completion(self, prompt: str, is_json: bool = False) -> dict:
        """
        Возвращает моковые данные, имитируя ответ от AI.
        """
        logger.info(f"Отправка запроса к Mock AI. Промпт: {prompt[:150]}...")

        if is_json:
            text_response = """
            {
                "match_analysis": "Анализ соответствия (MOCK)",
                "cover_letter": "Сопроводительное письмо (MOCK)",
                "hr_call_plan": "План для созвона с HR (MOCK)",
                "tech_interview_plan": "План для технического собеседования (MOCK)"
            }
            """
        elif "является ли следующий текст резюме" in prompt:
            text_response = '{"is_resume": true, "title": "Mock Resume Title"}'
        elif "является ли он описанием вакансии" in prompt:
            text_response = '{"is_vacancy": true, "title": "Mock Vacancy Title"}'
        elif "Проанализируй на соответствие" in prompt:
            text_response = "Анализ соответствия (MOCK): Кандидат отлично подходит."
        elif "Напиши сопроводительное письмо" in prompt:
            text_response = "Сопроводительное письмо (MOCK)"
        elif "Составь план для созвона с HR" in prompt:
            text_response = "План для созвона с HR (MOCK)"
        elif "Составь подробный план для технического собеседования" in prompt:
            text_response = "План для технического собеседования (MOCK)"
        else:
            text_response = "Ответ от Mock AI"

        prompt_tokens = len(prompt.split())
        completion_tokens = len(text_response.split())
        usage = {
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
            "total_tokens": prompt_tokens + completion_tokens,
        }

        response_data = {"usage": usage}
        if is_json:
            response_data["json"] = json.loads(text_response)
            response_data["text"] = None
        else:
            response_data["text"] = text_response
            response_data["json"] = None

        return response_data

    def verify_text(self, text: str, prompt_template: str) -> dict:
        """
        Формирует промпт и вызывает мок-AI для верификации.
        """
        prompt = prompt_template.format(text=text)
        return self._get_completion(prompt)

    def analyze(self, prompt_template: str, is_json: bool = False, **kwargs) -> dict:
        """
        Выполняет мок-анализ или генерацию текста.
        """
        prompt = prompt_template.format(**kwargs)
        return self._get_completion(prompt, is_json)

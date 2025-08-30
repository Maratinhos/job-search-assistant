import logging
# import openai # In a real scenario, you would import the library

from config import OPENAI_API_KEY

logger = logging.getLogger(__name__)


class OpenAIProvider:
    """
    Класс для взаимодействия с API OpenAI.
    NOTE: This is a mock implementation.
    """

    def __init__(self, api_key: str = OPENAI_API_KEY):
        if not api_key:
            # In a real application, you might want to handle this more gracefully
            # For now, we'll just log a warning because we are mocking the service.
            logger.warning("OpenAI API key not found. Running in mock mode.")

        # In a real scenario, you would initialize the client like this:
        # openai.api_key = api_key
        logger.info("Инициализирован OpenAI провайдер (MOCK).")

    def _get_completion(self, prompt: str) -> dict:
        """
        Отправляет запрос к API OpenAI и возвращает ответ в виде словаря,
        включающего текст и информацию о токенах.
        NOTE: This is a mock implementation.
        """
        logger.info(f"Отправка запроса к OpenAI (MOCK). Промпт: {prompt[:150]}...")

        # Mock responses based on prompt content
        if "Проверь, является ли следующий текст резюме" in prompt:
            text_response = "да"
        elif "Проверь, является ли следующий текст описанием вакансии" in prompt:
            text_response = "да"
        elif "Проанализируй соответствие" in prompt:
            text_response = "Анализ соответствия (MOCK): Кандидат отлично подходит. Сильные стороны: опыт в Python. Недостатки: нет опыта в Go. Оценка: 95%."
        elif "Напиши сопроводительное письмо" in prompt:
            text_response = "Сопроводительное письмо (MOCK): Уважаемый HR, я очень заинтересован в этой вакансии и уверен, что мой опыт будет полезен."
        elif "Составь план для созвона с HR" in prompt:
            text_response = "План для созвона с HR (MOCK):\n1. Представиться и рассказать о своем опыте.\n2. Задать вопросы о компании и команде.\n3. Обсудить ожидания от роли."
        elif "Составь подробный план для технического собеседования" in prompt:
            text_response = "План для технического собеседования (MOCK):\n1. Вопросы по Python (data structures, algorithms).\n2. Вопросы по базам данных (SQL, NoSQL).\n3. Красные флаги: отсутствие тестов в проектах."
        else:
            text_response = "Ответ от OpenAI (MOCK)"

        # Mock token usage. In a real scenario, this would come from the API response.
        prompt_tokens = len(prompt.split())
        completion_tokens = len(text_response.split())
        usage = {
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
            "total_tokens": prompt_tokens + completion_tokens,
        }

        return {"text": text_response, "usage": usage}

    def verify_text(self, text: str, prompt_template: str) -> dict:
        """
        Формирует промпт и вызывает AI для верификации.
        Возвращает полный ответ от AI, включая токен-статистику.
        """
        prompt = prompt_template.format(text=text)
        return self._get_completion(prompt)

    def analyze(self, prompt_template: str, **kwargs) -> dict:
        """
        Выполняет анализ или генерацию текста на основе шаблона и аргументов.
        Возвращает полный ответ от AI, включая токен-статистику.
        """
        prompt = prompt_template.format(**kwargs)
        return self._get_completion(prompt)

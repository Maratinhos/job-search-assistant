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

    def _get_completion(self, prompt: str) -> str:
        """
        Отправляет запрос к API OpenAI и возвращает ответ.
        NOTE: This is a mock implementation.
        """
        logger.info(f"Отправка запроса к OpenAI (MOCK). Промпт: {prompt[:150]}...")

        # Mock responses based on prompt content
        if "Проверь, является ли следующий текст резюме" in prompt:
            return "да"
        if "Проверь, является ли следующий текст описанием вакансии" in prompt:
            return "да"
        if "Проанализируй соответствие" in prompt:
            return "Анализ соответствия (MOCK): Кандидат отлично подходит. Сильные стороны: опыт в Python. Недостатки: нет опыта в Go. Оценка: 95%."
        if "Напиши сопроводительное письмо" in prompt:
            return "Сопроводительное письмо (MOCK): Уважаемый HR, я очень заинтересован в этой вакансии и уверен, что мой опыт будет полезен."
        if "Составь план для созвона с HR" in prompt:
            return "План для созвона с HR (MOCK):\n1. Представиться и рассказать о своем опыте.\n2. Задать вопросы о компании и команде.\n3. Обсудить ожидания от роли."
        if "Составь подробный план для технического собеседования" in prompt:
            return "План для технического собеседования (MOCK):\n1. Вопросы по Python (data structures, algorithms).\n2. Вопросы по базам данных (SQL, NoSQL).\n3. Красные флаги: отсутствие тестов в проектах."

        return "Ответ от OpenAI (MOCK)"

    def verify_text(self, text: str, prompt_template: str) -> bool:
        """
        Проверяет текст (резюме или вакансия) с помощью простого ответа 'да'/'нет'.
        """
        prompt = prompt_template.format(text=text)
        response = self._get_completion(prompt)
        return "да" in response.lower()

    def analyze(self, prompt_template: str, **kwargs) -> str:
        """
        Выполняет анализ или генерацию текста на основе шаблона и аргументов.
        """
        prompt = prompt_template.format(**kwargs)
        return self._get_completion(prompt)

import logging
import requests

from config import GEN_API_KEY

logger = logging.getLogger(__name__)


class GenApiProvider:
    """
    Класс для взаимодействия с API gen-api.ru.
    """

    API_URL = "https://api.gen-api.ru/api/v1/networks/gpt-5-mini"

    def __init__(self, api_key: str = GEN_API_KEY):
        if not api_key:
            logger.error("Gen-API key not found.")
            raise ValueError("Gen-API key is required.")
        self.api_key = api_key
        self.headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "Authorization": f"Bearer {self.api_key}",
        }
        logger.info("Инициализирован Gen-API провайдер.")

    def _get_completion(self, prompt: str) -> dict:
        """
        Отправляет синхронный запрос к API gen-api.ru и возвращает ответ.
        """
        logger.info(f"Отправка запроса к Gen-API. Промпт: {prompt[:150]}...")

        payload = {
            "is_sync": True,
            "model": "gpt-5-mini",
            "messages": [{"role": "user", "content": prompt}],
        }

        try:
            response = requests.post(self.API_URL, json=payload, headers=self.headers)
            response.raise_for_status()  # Raise an exception for bad status codes
            data = response.json()

            # Assuming the response text is in the 'output' field, based on async response example
            text_response = data.get("output", "Error: could not parse response from Gen-API.")

            # Mimic the token usage structure from OpenAIProvider
            prompt_tokens = len(prompt.split())
            completion_tokens = len(text_response.split())
            usage = {
                "prompt_tokens": prompt_tokens,
                "completion_tokens": completion_tokens,
                "total_tokens": prompt_tokens + completion_tokens,
            }

            return {"text": text_response, "usage": usage}

        except requests.exceptions.RequestException as e:
            logger.error(f"Ошибка при запросе к Gen-API: {e}")
            return {"text": f"Error communicating with Gen-API: {e}", "usage": {"total_tokens": 0}}

    def verify_text(self, text: str, prompt_template: str) -> dict:
        """
        Формирует промпт и вызывает AI для верификации.
        """
        prompt = prompt_template.format(text=text)
        return self._get_completion(prompt)

    def analyze(self, prompt_template: str, **kwargs) -> dict:
        """
        Выполняет анализ или генерацию текста на основе шаблона и аргументов.
        """
        prompt = prompt_template.format(**kwargs)
        return self._get_completion(prompt)

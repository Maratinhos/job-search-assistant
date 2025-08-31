import logging
import requests
import ast
import json
import re

from config import GEN_API_KEY

logger = logging.getLogger(__name__)


class GenAPIProvider:
    """
    Класс для взаимодействия с API gen-api.ru.
    """

    API_URL = "https://api.gen-api.ru/api/v1/networks/gpt-5"

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
        Отправляет синхронный запрос к API gen-api.ru, логирует ответ и пытается
        извлечь из него JSON, в том числе из вложенных структур.
        """
        logger.info(f"Отправка запроса к Gen-API. Промпт: {prompt[:150]}...")
        payload = {"is_sync": True, "model": "gpt-5-mini", "messages": [{"role": "user", "content": prompt}]}

        try:
            response = requests.post(self.API_URL, json=payload, headers=self.headers)
            response.raise_for_status()
            raw_response_text = response.text
            logger.info(f"Получен сырой ответ от Gen-API: {raw_response_text}")

            try:
                data = response.json()

                # NEW: Try to extract from the deeply nested structure first
                try:
                    content_str = data['response'][0]['message']['content']
                except (KeyError, IndexError, TypeError):
                    content_str = None

                # Fallback to the old logic if the new structure is not found
                if not content_str:
                    content_str = data.get("result", {}).get("text") or data.get("text")

                if isinstance(content_str, str):
                    match = re.search(r'\{.*\}', content_str, re.DOTALL)
                    if match:
                        json_str = match.group(0)
                        try:
                            return json.loads(json_str)
                        except json.JSONDecodeError as e:
                            logger.error(f"Не удалось распарсить как JSON извлеченную строку: {json_str}. Ошибка: {e}")
                            return data # Return original data on parsing error
                return data # Return original data if no content string found

            except requests.exceptions.JSONDecodeError:
                logger.warning(f"Ответ не является валидным JSON. Попытка найти JSON в сыром тексте.")
                match = re.search(r'\{.*\}', raw_response_text, re.DOTALL)
                if match:
                    json_str = match.group(0)
                    try:
                        return json.loads(json_str)
                    except json.JSONDecodeError as e:
                        logger.error(f"Не удалось распарсить как JSON строку из сырого текста: {json_str}. Ошибка: {e}")

                return {"is_vacancy": False, "title": None, "error": "Invalid response from AI"}

        except requests.exceptions.RequestException as e:
            logger.error(f"Ошибка при запросе к Gen-API: {e}")
            return {"is_vacancy": False, "title": None, "error": f"RequestException: {e}"}

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

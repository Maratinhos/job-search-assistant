import logging
import requests
import time
import json
from config import GEN_API_KEY

logger = logging.getLogger(__name__)


class GenAPIProvider:
    """
    Класс для взаимодействия с API gen-api.ru.
    """

    API_URL = "https://api.gen-api.ru/api/v1/networks/gpt-5"
    RESULT_URL = "https://api.gen-api.ru/api/v1/request/get/{request_id}"
    POLLING_INTERVAL = 3  # Секунды
    MAX_POLLING_ATTEMPTS = 100  # Максимальное количество попыток

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
        Отправляет асинхронный запрос к API gen-api.ru и получает результат
        через long-polling.
        """
        logger.info(f"Отправка асинхронного запроса к Gen-API. Промпт: {prompt[:150]}...")
        payload = {
            "model": "gpt-5-mini",
            "messages": [{"role": "user", "content": prompt}],
        }

        try:
            # 1. Отправляем начальный запрос на создание задачи
            initial_response = requests.post(self.API_URL, json=payload, headers=self.headers)
            initial_response.raise_for_status()
            initial_data = initial_response.json()
            logger.info(f"Получен ответ на создание задачи: {initial_data}")

            request_id = initial_data.get("request_id")
            if not request_id:
                logger.error(f"Не удалось получить request_id из ответа: {initial_data}")
                return {"text": None, "error": "Failed to get request_id"}

            # 2. Опрашиваем статус задачи
            for attempt in range(self.MAX_POLLING_ATTEMPTS):
                logger.info(f"Попытка {attempt + 1}/{self.MAX_POLLING_ATTEMPTS}: Проверка статуса для request_id {request_id}")
                time.sleep(self.POLLING_INTERVAL)

                result_response = requests.get(self.RESULT_URL.format(request_id=request_id), headers=self.headers)
                result_response.raise_for_status()
                result_data = result_response.json()

                status = result_data.get("status")
                logger.info(f"Текущий статус задачи: {status}")

                if status == "success":
                    logger.info(f"Задача {request_id} успешно выполнена. Ответ: {result_data}")
                    try:
                        # Извлекаем основной текстовый контент
                        content = result_data["full_response"][0]["message"]["content"]
                        return {"text": content, "full_response": result_data}
                    except (KeyError, IndexError, TypeError) as e:
                        logger.error(f"Не удалось извлечь контент из успешного ответа: {e}. Ответ: {result_data}")
                        return {"text": None, "error": f"Failed to parse successful response: {e}"}

                elif status == "failed":
                    logger.error(f"Задача {request_id} провалена. Ответ: {result_data}")
                    return {"text": None, "error": "AI task failed", "full_response": result_data}

                elif status != "processing":
                    logger.warning(f"Неизвестный статус задачи {request_id}: {status}")

            logger.error(f"Превышено максимальное количество попыток для request_id {request_id}")
            return {"text": None, "error": "Polling timeout"}

        except requests.exceptions.RequestException as e:
            logger.error(f"Ошибка при запросе к Gen-API: {e}")
            return {"text": None, "error": f"RequestException: {e}"}
        except json.JSONDecodeError as e:
            logger.error(f"Ошибка декодирования JSON ответа от Gen-API: {e}")
            return {"text": None, "error": f"JSONDecodeError: {e}"}

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

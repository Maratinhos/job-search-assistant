import logging
import requests
import time
import json
import tiktoken
from config import GEN_API_KEY

logger = logging.getLogger(__name__)


class GenAPIProvider:
    """
    Класс для взаимодействия с API gen-api.ru.
    """

    llm = 'gpt-4-1'
    model = 'gpt-4.1-mini'

    API_URL = f"https://api.gen-api.ru/api/v1/networks/{llm}"
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
        # Инициализация кодировщика токенов
        try:
            self.encoding = tiktoken.get_encoding("cl100k_base")
        except Exception as e:
            logger.error(f"Не удалось инициализировать кодировщик tiktoken: {e}")
            self.encoding = None
        logger.info("Инициализирован Gen-API провайдер.")

    def _calculate_tokens(self, text: str) -> int:
        """Подсчитывает количество токенов в тексте."""
        if not self.encoding or not text:
            return 0
        return len(self.encoding.encode(text))

    def _create_error_response(self, prompt: str, cost: float = 0.0) -> dict:
        """Создает стандартизированный ответ об ошибке."""
        prompt_tokens = self._calculate_tokens(prompt)
        return {
            "text": None,
            "usage": {
                "cost": cost,
                "prompt_tokens": prompt_tokens,
                "completion_tokens": 0,
                "total_tokens": prompt_tokens,
            },
        }

    def _get_completion(self, prompt: str, is_json: bool = False) -> dict:
        """
        Отправляет асинхронный запрос к API gen-api.ru, получает результат
        и возвращает унифицированный словарь с текстом и usage.
        """
        logger.info(f"Отправка асинхронного запроса к Gen-API. Промпт: {prompt[:150]}...")
        payload = {
            "model": self.model,
            "messages": [{"role": "user", "content": prompt}],
        }
        if is_json:
            payload["response_format"] = {"type": "json_object"}

        try:
            initial_response = requests.post(self.API_URL, json=payload, headers=self.headers)
            initial_response.raise_for_status()
            initial_data = initial_response.json()
            logger.info(f"Получен ответ на создание задачи: {initial_data}")

            request_id = initial_data.get("request_id")
            if not request_id:
                logger.error(f"Не удалось получить request_id из ответа: {initial_data}")
                return self._create_error_response(prompt)

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
                        content = result_data["full_response"][0]["message"]["content"]
                        cost = result_data.get("cost", 0.0)

                        prompt_tokens = self._calculate_tokens(prompt)
                        completion_tokens = self._calculate_tokens(content)
                        total_tokens = prompt_tokens + completion_tokens

                        response_data = {
                            "usage": {
                                "cost": float(cost) if cost else 0.0,
                                "prompt_tokens": prompt_tokens,
                                "completion_tokens": completion_tokens,
                                "total_tokens": total_tokens,
                            }
                        }

                        if is_json:
                            try:
                                response_data["json"] = json.loads(content)
                                response_data["text"] = None
                            except json.JSONDecodeError:
                                logger.error("Не удалось декодировать JSON из ответа AI.")
                                return self._create_error_response(prompt)
                        else:
                            response_data["text"] = content
                            response_data["json"] = None

                        return response_data

                    except (KeyError, IndexError, TypeError) as e:
                        logger.error(f"Не удалось извлечь контент из успешного ответа: {e}. Ответ: {result_data}")
                        return self._create_error_response(prompt)

                elif status == "failed":
                    logger.error(f"Задача {request_id} провалена. Ответ: {result_data}")
                    cost = float(result_data.get("cost", 0.0))
                    return self._create_error_response(prompt, cost=cost)

                elif status != "processing":
                    logger.warning(f"Неизвестный статус задачи {request_id}: {status}")

            logger.error(f"Превышено максимальное количество попыток для request_id {request_id}")
            return self._create_error_response(prompt)

        except requests.exceptions.RequestException as e:
            logger.error(f"Ошибка при запросе к Gen-API: {e}")
            return self._create_error_response(prompt)
        except json.JSONDecodeError as e:
            logger.error(f"Ошибка декодирования JSON ответа от Gen-API: {e}")
            return self._create_error_response(prompt)

    def verify_text(self, text: str, prompt_template: str) -> dict:
        """
        Формирует промпт и вызывает AI для верификации.
        """
        prompt = prompt_template.format(text=text)
        return self._get_completion(prompt)

    def analyze(self, prompt_template: str, is_json: bool = False, **kwargs) -> dict:
        """
        Выполняет анализ или генерацию текста на основе шаблона и аргументов.
        """
        prompt = prompt_template.format(**kwargs)
        return self._get_completion(prompt, is_json)

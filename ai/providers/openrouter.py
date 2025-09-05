import logging
import json
from openai import OpenAI

from config import OPENROUTER_API_KEY

logger = logging.getLogger(__name__)

# Constants for OpenRouter
OPENROUTER_API_BASE_URL = "https://openrouter.ai/api/v1"
YOUR_SITE_URL = "https://github.com/Jules-Labs/ai-cv-res-analyzer"
YOUR_SITE_NAME = "AI CV RES Analyzer"
MODEL_NAME = "deepseek/deepseek-chat-v3.1:free"


class OpenRouterProvider:
    """
    Класс для взаимодействия с API OpenRouter.
    """

    def __init__(self, api_key: str = OPENROUTER_API_KEY):
        if not api_key:
            logger.error("OpenRouter API key not found.")
            raise ValueError("OpenRouter API key is required.")

        self.client = OpenAI(
            base_url=OPENROUTER_API_BASE_URL,
            api_key=api_key,
        )
        self.extra_headers = {
            "HTTP-Referer": YOUR_SITE_URL,
            "X-Title": YOUR_SITE_NAME,
        }
        logger.info("Инициализирован OpenRouter провайдер.")

    def _get_completion(self, prompt: str, is_json: bool = False) -> dict:
        """
        Отправляет запрос к API OpenRouter и возвращает ответ.
        """
        logger.info(f"Отправка запроса к OpenRouter. Промпт: {prompt[:150]}...")

        messages = [{"role": "user", "content": prompt}]

        request_params = {
            "model": MODEL_NAME,
            "messages": messages,
            "extra_headers": self.extra_headers,
        }

        if is_json:
            request_params["response_format"] = {"type": "json_object"}

        try:
            completion = self.client.chat.completions.create(**request_params)

            usage = {
                "prompt_tokens": completion.usage.prompt_tokens,
                "completion_tokens": completion.usage.completion_tokens,
                "total_tokens": completion.usage.total_tokens,
            }

            response_data = {"usage": usage}
            message_content = completion.choices[0].message.content

            if not message_content:
                raise ValueError("API returned an empty response content.")

            if is_json:
                # Очищаем строку от возможных обрамляющих символов
                if message_content.startswith("```json"):
                    message_content = message_content[7:-3].strip()
                elif message_content.startswith("```"):
                    message_content = message_content[3:-3].strip()
                response_data["json"] = json.loads(message_content)
                response_data["text"] = None
            else:
                response_data["text"] = message_content
                response_data["json"] = None

            return response_data

        except Exception as e:
            logger.error(f"Ошибка при вызове API OpenRouter: {e}")
            return {
                "usage": {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0},
                "text": f"Error from OpenRouter: {e}",
                "json": None,
            }

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

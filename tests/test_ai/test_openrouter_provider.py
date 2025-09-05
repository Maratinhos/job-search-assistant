import pytest
from unittest.mock import patch, MagicMock
import json

from ai.providers.openrouter import OpenRouterProvider, MODEL_NAME

# --- Test Data ---
SUCCESS_JSON_CONTENT = {"key": "value"}
SUCCESS_JSON_STRING = json.dumps(SUCCESS_JSON_CONTENT)
PROMPT_TEXT = "some prompt"

# --- Fixtures ---
@pytest.fixture
def provider():
    """Фикстура для создания экземпляра OpenRouterProvider с тестовым ключом."""
    with patch('ai.providers.openrouter.OpenAI') as mock_openai:
        mock_client = MagicMock()
        mock_openai.return_value = mock_client
        yield OpenRouterProvider(api_key="test_key")

# --- Helper Functions ---
def mock_completion(content: str):
    """Хелпер для создания мока ответа от chat.completions.create."""
    mock_choice = MagicMock()
    mock_choice.message.content = content

    mock_usage = MagicMock()
    mock_usage.prompt_tokens = 5
    mock_usage.completion_tokens = 10
    mock_usage.total_tokens = 15

    mock_completion_obj = MagicMock()
    mock_completion_obj.choices = [mock_choice]
    mock_completion_obj.usage = mock_usage

    return mock_completion_obj

# --- Tests ---

def test_get_completion_json_clean(provider):
    """Тест для чистого JSON ответа."""
    provider.client.chat.completions.create.return_value = mock_completion(SUCCESS_JSON_STRING)

    result = provider._get_completion(PROMPT_TEXT, is_json=True)

    assert result["json"] == SUCCESS_JSON_CONTENT
    assert result["text"] is None
    provider.client.chat.completions.create.assert_called_once()

def test_get_completion_json_with_backticks(provider):
    """Тест для JSON, обернутого в ```...```."""
    formatted_json = f"```{SUCCESS_JSON_STRING}```"
    provider.client.chat.completions.create.return_value = mock_completion(formatted_json)

    result = provider._get_completion(PROMPT_TEXT, is_json=True)

    assert result["json"] == SUCCESS_JSON_CONTENT
    assert result["text"] is None

def test_get_completion_json_with_json_prefix_and_backticks(provider):
    """Тест для JSON, обернутого в ```json...```."""
    formatted_json = f"```json\n{SUCCESS_JSON_STRING}\n```"
    provider.client.chat.completions.create.return_value = mock_completion(formatted_json)

    result = provider._get_completion(PROMPT_TEXT, is_json=True)

    assert result["json"] == SUCCESS_JSON_CONTENT
    assert result["text"] is None

def test_get_completion_empty_response(provider):
    """Тест для пустого ответа от API."""
    provider.client.chat.completions.create.return_value = mock_completion("")

    result = provider._get_completion(PROMPT_TEXT, is_json=True)

    assert result["json"] is None
    assert "API returned an empty response content." in result["text"]

def test_get_completion_invalid_json(provider):
    """Тест для невалидного JSON."""
    provider.client.chat.completions.create.return_value = mock_completion("not a json")

    result = provider._get_completion(PROMPT_TEXT, is_json=True)

    assert result["json"] is None
    assert "Expecting value" in result["text"]

def test_get_completion_non_json_request(provider):
    """Тест для обычного текстового запроса."""
    text_content = "This is a simple text response."
    provider.client.chat.completions.create.return_value = mock_completion(text_content)

    result = provider._get_completion(PROMPT_TEXT, is_json=False)

    assert result["text"] == text_content
    assert result["json"] is None

def test_get_completion_api_error(provider):
    """Тест на случай ошибки при вызове API."""
    error_message = "API Key is invalid"
    provider.client.chat.completions.create.side_effect = Exception(error_message)

    result = provider._get_completion(PROMPT_TEXT, is_json=True)

    assert result["json"] is None
    assert f"Error from OpenRouter: {error_message}" in result["text"]
    assert result["usage"]["total_tokens"] == 0

def test_init_no_api_key():
    """Тест на ошибку, если API ключ не предоставлен."""
    with patch('ai.providers.openrouter.OPENROUTER_API_KEY', None):
        with pytest.raises(ValueError, match="OpenRouter API key is required."):
            OpenRouterProvider(api_key=None)

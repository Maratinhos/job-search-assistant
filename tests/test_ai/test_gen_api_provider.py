import pytest
from unittest.mock import patch, MagicMock
import requests

from ai.providers.gen_api import GenAPIProvider


@patch('requests.post')
def test_get_completion_success(mock_post):
    """
    Тестирует успешный вызов _get_completion.
    Проверяет, что провайдер правильно парсит успешный JSON ответ.
    """
    # --- Mocks Setup ---
    mock_response = MagicMock()
    # This is the structure the provider should return
    expected_json = {
        'request_id': 24075792,
        'model': 'gpt-5',
        'cost': 0.2358,
        'response': [{'message': {'content': '{"is_resume": true}'}}]
    }
    mock_response.json.return_value = expected_json
    mock_response.raise_for_status.return_value = None
    mock_post.return_value = mock_response

    # --- Call ---
    provider = GenAPIProvider(api_key="test_key")
    result = provider._get_completion("test prompt")

    # --- Assertions ---
    assert result == expected_json
    mock_post.assert_called_once()
    mock_response.raise_for_status.assert_called_once()


@patch('requests.post')
def test_get_completion_request_exception(mock_post):
    """
    Тестирует обработку ошибки при запросе к API.
    """
    # --- Mocks Setup ---
    mock_post.side_effect = requests.exceptions.RequestException("Test error")

    # --- Call ---
    provider = GenAPIProvider(api_key="test_key")
    result = provider._get_completion("test prompt")

    # --- Assertions ---
    assert "Error communicating with Gen-API" in result["text"]
    assert result["usage"]["total_tokens"] == 0


@patch('requests.post')
def test_get_completion_json_decode_error(mock_post):
    """
    Тестирует обработку ошибки декодирования JSON.
    """
    # --- Mocks Setup ---
    mock_response = MagicMock()
    mock_response.raise_for_status.return_value = None
    mock_response.json.side_effect = requests.exceptions.JSONDecodeError("Test JSON error", "", 0)
    mock_post.return_value = mock_response

    # --- Call ---
    provider = GenAPIProvider(api_key="test_key")
    result = provider._get_completion("test prompt")

    # --- Assertions ---
    assert "Error decoding JSON from Gen-API" in result["text"]
    assert result["usage"]["total_tokens"] == 0

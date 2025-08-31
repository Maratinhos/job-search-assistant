import pytest
from unittest.mock import patch, MagicMock
import requests
import json

from ai.providers.gen_api import GenAPIProvider

# Ожидаемый результат успешного парсинга
EXPECTED_PARSED_JSON = {"is_vacancy": True, "title": "Software Engineer"}

@pytest.fixture
def provider():
    """Фикстура для создания экземпляра GenAPIProvider."""
    return GenAPIProvider(api_key="test_key")

def mock_response(status_code=200, text_content=None, json_content=None):
    """Хелпер для создания мока ответа requests."""
    mock_res = MagicMock()
    mock_res.raise_for_status.side_effect = (
        requests.exceptions.HTTPError if status_code >= 400 else None
    )
    mock_res.status_code = status_code
    mock_res.text = text_content
    # json.loads(text_content) может быть вызван внутри response.json()
    # Поэтому мокаем и его для консистентности
    if json_content:
        mock_res.json.return_value = json_content
    else:
        # Если json_content не предоставлен, но текст есть, пытаемся его распарсить
        try:
            mock_res.json.return_value = json.loads(text_content)
        except (json.JSONDecodeError, TypeError):
            mock_res.json.side_effect = requests.exceptions.JSONDecodeError("mock error", "", 0)

    return mock_res


@patch('requests.post')
def test_success_nested_json_in_result_text(mock_post, provider):
    """Тест: AI возвращает JSON как строку в поле result.text."""
    api_response_json = {
        "result": {"text": '```json\n{"is_vacancy": true, "title": "Software Engineer"}\n```'}
    }
    mock_post.return_value = mock_response(
        text_content=json.dumps(api_response_json),
        json_content=api_response_json
    )

    result = provider._get_completion("prompt")

    assert result == EXPECTED_PARSED_JSON

@patch('requests.post')
def test_success_direct_json_as_top_level(mock_post, provider):
    """Тест: AI возвращает ожидаемый JSON как ответ верхнего уровня."""
    mock_post.return_value = mock_response(
        text_content=json.dumps(EXPECTED_PARSED_JSON),
        json_content=EXPECTED_PARSED_JSON
    )

    result = provider._get_completion("prompt")

    assert result == EXPECTED_PARSED_JSON

@patch('requests.post')
def test_failure_invalid_json_string_in_text(mock_post, provider):
    """Тест: AI возвращает некорректную JSON-строку."""
    api_response_json = {"text": '{"is_vacancy": True, "title": "Software Engineer",}'} # Лишняя запятая
    mock_post.return_value = mock_response(
        text_content=json.dumps(api_response_json),
        json_content=api_response_json
    )

    result = provider._get_completion("prompt")

    # В этом случае парсер должен упасть и вернуть исходный dict
    assert result == api_response_json

@patch('requests.post')
def test_failure_non_json_raw_response(mock_post, provider):
    """Тест: Ответ API - это не JSON, а просто текст."""
    raw_text = "Sorry, I can't help with that."
    mock_post.return_value = mock_response(text_content=raw_text)

    result = provider._get_completion("prompt")

    assert result["error"] == "Invalid response from AI"
    assert result["is_vacancy"] is False

@patch('requests.post')
def test_failure_api_request_exception(mock_post, provider):
    """Тест: Возникает исключение при запросе к API."""
    mock_post.side_effect = requests.exceptions.RequestException("Network Error")

    result = provider._get_completion("prompt")

    assert "RequestException" in result["error"]
    assert result["is_vacancy"] is False

@patch('requests.post')
def test_success_deeply_nested_json(mock_post, provider):
    """Тест: AI возвращает JSON в глубоко вложенной структуре, как в логах."""
    api_response_json = {
        "response": [{
            "message": {
                "content": '{"is_vacancy": true, "title": "Software Engineer"}'
            }
        }]
    }
    mock_post.return_value = mock_response(
        text_content=json.dumps(api_response_json),
        json_content=api_response_json
    )

    result = provider._get_completion("prompt")

    assert result == EXPECTED_PARSED_JSON

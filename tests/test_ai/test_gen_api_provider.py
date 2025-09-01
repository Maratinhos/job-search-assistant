import pytest
from unittest.mock import patch, MagicMock, call
import requests
import json

from ai.providers.gen_api import GenAPIProvider

# --- Test Data ---
SUCCESS_CONTENT = '{"is_vacancy": true, "title": "Software Engineer"}'
REQUEST_ID = "test_request_123"
PROMPT_TEXT = "some prompt"

# --- Fixtures ---
@pytest.fixture
def provider():
    """Фикстура для создания экземпляра GenAPIProvider с тестовым ключом."""
    # Используем мок для tiktoken, чтобы избежать реальной загрузки
    with patch('tiktoken.get_encoding') as mock_get_encoding:
        mock_encoder = MagicMock()
        # "some prompt" -> 2 tokens
        # SUCCESS_CONTENT -> 15 tokens
        mock_encoder.encode.side_effect = lambda text: list(range(2)) if text == PROMPT_TEXT else list(range(15))
        mock_get_encoding.return_value = mock_encoder
        yield GenAPIProvider(api_key="test_key")


# --- Helper Functions ---
def mock_response(status_code=200, json_content=None, text_content=""):
    """Хелпер для создания мока ответа requests."""
    mock_res = MagicMock()
    if status_code >= 400:
        mock_res.raise_for_status.side_effect = requests.exceptions.HTTPError(f"Error {status_code}", response=mock_res)
    else:
        mock_res.raise_for_status.return_value = None
    mock_res.status_code = status_code
    mock_res.json.return_value = json_content
    mock_res.text = text_content if json_content is None else json.dumps(json_content)
    return mock_res

# --- Tests ---

@patch('time.sleep', return_value=None)
@patch('requests.get')
@patch('requests.post')
def test_get_completion_success_flow(mock_post, mock_get, mock_sleep, provider):
    """
    Тест полного успешного сценария:
    1. POST запрос для создания задачи -> request_id
    2. Первый GET запрос -> status: processing
    3. Второй GET запрос -> status: success с результатом.
    """
    mock_post.return_value = mock_response(200, {"request_id": REQUEST_ID})
    mock_get.side_effect = [
        mock_response(200, {"status": "processing"}),
        mock_response(200, {
            "status": "success",
            "cost": 0.0015,
            "full_response": [{"message": {"content": SUCCESS_CONTENT}}]
        })
    ]

    result = provider._get_completion(PROMPT_TEXT)

    assert mock_post.call_count == 1
    assert mock_get.call_count == 2
    expected_get_url = provider.RESULT_URL.format(request_id=REQUEST_ID)
    mock_get.assert_has_calls([call(expected_get_url, headers=provider.headers)] * 2)

    assert result["text"] == SUCCESS_CONTENT
    assert result["usage"]["cost"] == 0.0015
    assert result["usage"]["prompt_tokens"] == 2
    assert result["usage"]["completion_tokens"] == 15
    assert result["usage"]["total_tokens"] == 17

@patch('time.sleep', return_value=None)
@patch('requests.get')
@patch('requests.post')
def test_get_completion_failed_status(mock_post, mock_get, mock_sleep, provider):
    """Тест сценария, когда задача завершается со статусом 'failed'."""
    mock_post.return_value = mock_response(200, {"request_id": REQUEST_ID})
    mock_get.return_value = mock_response(200, {
        "status": "failed",
        "cost": 0.0001,
        "error_message": "Something went wrong"
    })

    result = provider._get_completion(PROMPT_TEXT)

    assert result["text"] is None
    assert result["usage"]["cost"] == 0.0001
    assert result["usage"]["prompt_tokens"] == 2
    assert result["usage"]["completion_tokens"] == 0
    assert result["usage"]["total_tokens"] == 2

@patch('time.sleep', return_value=None)
@patch('requests.get')
@patch('requests.post')
def test_get_completion_polling_timeout(mock_post, mock_get, mock_sleep, provider):
    """Тест сценария, когда превышено максимальное количество попыток опроса."""
    mock_post.return_value = mock_response(200, {"request_id": REQUEST_ID})
    mock_get.return_value = mock_response(200, {"status": "processing"})

    result = provider._get_completion(PROMPT_TEXT)

    assert mock_get.call_count == provider.MAX_POLLING_ATTEMPTS
    assert result["text"] is None
    assert result["usage"]["cost"] == 0.0
    assert result["usage"]["prompt_tokens"] == 2
    assert result["usage"]["total_tokens"] == 2

@patch('requests.post')
def test_get_completion_initial_post_fails(mock_post, provider):
    """Тест сценария, когда первоначальный POST запрос падает."""
    mock_post.side_effect = requests.exceptions.RequestException("Network Error")

    result = provider._get_completion(PROMPT_TEXT)

    assert result["text"] is None
    assert result["usage"]["cost"] == 0.0
    assert result["usage"]["prompt_tokens"] == 2
    assert result["usage"]["total_tokens"] == 2

@patch('time.sleep', return_value=None)
@patch('requests.get')
@patch('requests.post')
def test_get_completion_polling_get_fails(mock_post, mock_get, mock_sleep, provider):
    """Тест сценария, когда GET запрос при опросе падает."""
    mock_post.return_value = mock_response(200, {"request_id": REQUEST_ID})
    mock_get.side_effect = requests.exceptions.RequestException("Network Error")

    result = provider._get_completion(PROMPT_TEXT)

    assert result["text"] is None
    assert result["usage"]["cost"] == 0.0
    assert result["usage"]["prompt_tokens"] == 2
    assert result["usage"]["total_tokens"] == 2

@patch('time.sleep', return_value=None)
@patch('requests.get')
@patch('requests.post')
def test_get_completion_bad_success_response(mock_post, mock_get, mock_sleep, provider):
    """Тест, когда статус 'success', но структура ответа некорректна."""
    mock_post.return_value = mock_response(200, {"request_id": REQUEST_ID})
    mock_get.return_value = mock_response(200, {
        "status": "success",
        "full_response": [{"message": {"wrong_key": "no content here"}}]
    })

    result = provider._get_completion(PROMPT_TEXT)

    assert result["text"] is None
    assert result["usage"]["cost"] == 0.0
    assert result["usage"]["prompt_tokens"] == 2
    assert result["usage"]["total_tokens"] == 2

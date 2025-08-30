from scraper.hh_scraper import scrape_hh_url
import requests

def test_scrape_hh_url_success(requests_mock):
    """
    Тестирует успешный скрейпинг страницы.
    """
    url = "https://hh.ru/resume/some_id"
    html_content = """
    <html>
        <head><title>My Resume</title></head>
        <body>
            <main>
                <h1>John Doe</h1>
                <p>Software Engineer</p>
                <script>console.log("hello");</script>
                <style>.foo { color: red; }</style>
            </main>
        </body>
    </html>
    """
    requests_mock.get(url, text=html_content, status_code=200)

    result = scrape_hh_url(url)

    assert result is not None
    # Проверяем, что основной текст извлечен
    assert "John Doe" in result
    assert "Software Engineer" in result
    # Проверяем, что теги script и style были удалены и их содержимое не попало в результат
    assert "console.log" not in result
    assert "color: red" not in result

def test_scrape_hh_url_http_error(requests_mock):
    """
    Тестирует случай, когда сервер возвращает ошибку (например, 404 Not Found).
    """
    url = "https://hh.ru/resume/not_found"
    requests_mock.get(url, status_code=404)

    result = scrape_hh_url(url)

    assert result is None

def test_scrape_hh_url_request_exception(requests_mock):
    """
    Тестирует случай, когда происходит сетевая ошибка (например, нет подключения).
    """
    url = "https://hh.ru/resume/network_error"
    requests_mock.get(url, exc=requests.exceptions.RequestException)

    result = scrape_hh_url(url)

    assert result is None

def test_scrape_invalid_url_scheme():
    """
    Тестирует передачу некорректного URL (без схемы http/https).
    """
    url = "not_a_valid_url.com"
    result = scrape_hh_url(url)
    assert result is None

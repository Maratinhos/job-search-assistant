import requests
from bs4 import BeautifulSoup
import logging

logger = logging.getLogger(__name__)

# Headers to mimic a browser request, which can help avoid simple anti-bot measures.
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
    "Accept-Language": "en-US,en;q=0.9,ru;q=0.8",
    "Accept-Encoding": "gzip, deflate, br",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8",
}


def scrape_hh_url(url: str) -> str | None:
    """
    Скрейпит текстовое содержимое со страницы по URL.
    Предназначен для hh.ru, но может работать и с другими сайтами.
    Возвращает текст страницы или None в случае ошибки.
    """
    if not url.startswith(('http://', 'https://')):
        logger.warning(f"Некорректный URL: {url}")
        return None

    try:
        logger.info(f"Начинаю скрейпинг URL: {url}")
        response = requests.get(url, headers=HEADERS, timeout=15)
        response.raise_for_status()  # Проверка на HTTP ошибки (4xx или 5xx)

        # Устанавливаем кодировку, чтобы избежать проблем с кириллицей
        response.encoding = response.apparent_encoding

        soup = BeautifulSoup(response.text, "html.parser")

        # Удаляем теги <script> и <style>, так как они не содержат полезного текста
        for script_or_style in soup(["script", "style"]):
            script_or_style.decompose()

        # Ищем основной контент. Селекторы могут потребовать обновления, если hh.ru изменит верстку.
        # Это более общий подход, чем поиск одного конкретного класса.
        # Попробуем найти тег main, body или корневой div.
        content_area = soup.find("main") or soup.find("body")

        if not content_area:
            logger.warning(f"Не удалось найти основной контент на странице {url}")
            return None

        # Извлекаем текст, очищая от лишних пробелов и пустых строк
        text = content_area.get_text(separator="\n", strip=True)

        logger.info(f"Скрейпинг успешно завершен. Длина текста: {len(text)} символов.")
        return text

    except requests.RequestException as e:
        logger.error(f"Ошибка при запросе к URL {url}: {e}")
        return None
    except Exception as e:
        logger.error(f"Непредвиденная ошибка при скрейпинге {url}: {e}")
        return None

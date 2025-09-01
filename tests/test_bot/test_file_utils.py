import pytest
import os
from unittest.mock import patch

from bot.file_utils import save_text_to_file, STORAGE_DIR

@pytest.fixture(autouse=True)
def mock_storage_dir(monkeypatch, tmp_path):
    """
    Фикстура для временной замены базовой директории хранения (STORAGE_DIR)
    на временную директорию, предоставляемую pytest (tmp_path).
    Это гарантирует, что тесты не будут создавать файлы в реальной 'storage'.
    `autouse=True` применяет эту фикстуру ко всем тестам в файле.
    """
    # Преобразуем tmp_path в строку, так как file_utils работает со строковыми путями
    temp_storage_path = str(tmp_path)
    monkeypatch.setattr('bot.file_utils.STORAGE_DIR', temp_storage_path)
    # Возвращаем путь для возможного использования в тестах
    return temp_storage_path

@patch('bot.file_utils.uuid.uuid4', return_value='test-uuid')
def test_save_text_to_file_creates_dir_and_file(mock_uuid, mock_storage_dir):
    """
    Тест проверяет, что функция:
    1. Создает поддиректорию, если она не существует.
    2. Создает файл с корректным содержимым.
    3. Возвращает правильный путь к файлу.
    """
    test_content = "Это тестовое содержимое резюме."
    subfolder = "resumes"

    # Вызываем тестируемую функцию
    returned_path = save_text_to_file(test_content, subfolder)

    # Формируем ожидаемый путь
    # mock_storage_dir - это путь к временной директории, подставленный фикстурой
    expected_dir = os.path.join(mock_storage_dir, subfolder)
    expected_file_path = os.path.join(expected_dir, "test-uuid.txt")

    # 1. Проверяем, что путь был возвращен корректно
    assert returned_path == expected_file_path

    # 2. Проверяем, что директория была создана
    assert os.path.isdir(expected_dir)

    # 3. Проверяем, что файл существует
    assert os.path.isfile(expected_file_path)

    # 4. Проверяем содержимое файла
    with open(expected_file_path, 'r', encoding='utf-8') as f:
        content_in_file = f.read()
    assert content_in_file == test_content

@patch('builtins.open')
def test_save_text_to_file_handles_io_error(mock_open, mock_storage_dir):
    """
    Тест проверяет, что функция корректно обрабатывает IOError
    при записи файла и возвращает None.
    """
    # Настраиваем мок open, чтобы он вызывал исключение
    mock_open.side_effect = IOError("Permission denied")

    test_content = "Some content"
    subfolder = "vacancies"

    # Вызываем функцию и ожидаем, что она вернет None
    result = save_text_to_file(test_content, subfolder)

    assert result is None

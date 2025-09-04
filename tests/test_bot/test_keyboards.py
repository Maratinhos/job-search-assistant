import pytest
from unittest.mock import MagicMock
from telegram import InlineKeyboardButton, InlineKeyboardMarkup

from bot.keyboards import (
    main_menu_keyboard,
    vacancy_selection_keyboard,
    cancel_keyboard,
)

def test_cancel_keyboard():
    """
    Тест проверяет, что `cancel_keyboard` создает клавиатуру с одной кнопкой "Отмена".
    """
    keyboard = cancel_keyboard()

    assert isinstance(keyboard, InlineKeyboardMarkup)
    assert len(keyboard.inline_keyboard) == 1

    button = keyboard.inline_keyboard[0][0]
    assert isinstance(button, InlineKeyboardButton)
    assert button.text == "Отмена"
    assert button.callback_data == "cancel_action"

def test_vacancy_selection_keyboard():
    """
    Тест проверяет, что `vacancy_selection_keyboard` правильно создает кнопки для выбора вакансий.
    """
    # Создаем моки вакансий
    mock_vacancy_1 = MagicMock()
    mock_vacancy_1.id = 101
    mock_vacancy_1.title = "Python Developer"

    mock_vacancy_2 = MagicMock()
    mock_vacancy_2.id = 102
    mock_vacancy_2.title = "Data Scientist"

    vacancies = [mock_vacancy_1, mock_vacancy_2]

    keyboard = vacancy_selection_keyboard(vacancies)

    assert isinstance(keyboard, InlineKeyboardMarkup)
    # 2 кнопки вакансий + "Загрузить новую" + "Отмена"
    assert len(keyboard.inline_keyboard) == 4

    # Проверяем первую кнопку вакансии
    button1 = keyboard.inline_keyboard[0][0]
    assert button1.text == "Python Developer"
    assert button1.callback_data == "vacancy_select_101"

    # Проверяем вторую кнопку вакансии
    button2 = keyboard.inline_keyboard[1][0]
    assert button2.text == "Data Scientist"
    assert button2.callback_data == "vacancy_select_102"

    # Проверяем кнопку "Отмена"
    cancel_button = keyboard.inline_keyboard[3][0]
    assert cancel_button.text == "Отмена"
    assert cancel_button.callback_data == "cancel_action"

# Используем параметризацию для тестирования различных состояний главного меню
@pytest.mark.parametrize(
    "vacancy_count, has_resume, has_selected_vacancy, show_survey_button, expected_buttons, description",
    [
        # Сценарий 1: Все опции доступны, включая опрос
        (5, True, True, True, [
            "📊 Анализ резюме/вакансии", "✉️ Сопроводительное письмо", "📞 План созвона с HR", "💻 План тех. собеседования",
            "📝 Пройти опрос", f"📂 Выбрать другую вакансию (5)", "➕ Загрузить новую вакансию", "🔄 Обновить резюме"
        ], "Все опции, включая опрос"),

        # Сценарий 2: Все опции доступны, но без опроса
        (5, True, True, False, [
            "📊 Анализ резюме/вакансии", "✉️ Сопроводительное письмо", "📞 План созвона с HR", "💻 План тех. собеседования",
            f"📂 Выбрать другую вакансию (5)", "➕ Загрузить новую вакансию", "🔄 Обновить резюме"
        ], "Все опции, кроме опроса"),

        # Сценарий 3: Нет выбранной вакансии, есть резюме и другие вакансии
        (2, True, False, True, [
            "📝 Пройти опрос", f"📂 Выбрать другую вакансию (2)", "➕ Загрузить новую вакансию", "🔄 Обновить резюме"
        ], "Нет выбранной вакансии, с опросом"),

        # Сценарий 4: Нет вакансий, есть резюме
        (0, True, False, False, [
            "➕ Загрузить новую вакансию", "🔄 Обновить резюме"
        ], "Нет вакансий, без опроса"),

        # Сценарий 5: Есть выбранная вакансия, но нет резюме
        (2, False, True, True, [
            "📊 Анализ резюме/вакансии", "✉️ Сопроводительное письмо", "📞 План созвона с HR", "💻 План тех. собеседования",
            "📝 Пройти опрос", f"📂 Выбрать другую вакансию (2)", "➕ Загрузить новую вакансию"
        ], "Нет резюме, с опросом"),

        # Сценарий 6: Самый минимальный сценарий
        (0, False, False, False, [
            "➕ Загрузить новую вакансию"
        ], "Минимальный сценарий, без опроса"),

        # Сценарий 7: Только кнопка опроса и стандартные кнопки
        (0, True, False, True, [
            "📝 Пройти опрос", "➕ Загрузить новую вакансию", "🔄 Обновить резюме"
        ], "Только опрос и базовые кнопки"),
    ]
)
def test_main_menu_keyboard(vacancy_count, has_resume, has_selected_vacancy, show_survey_button, expected_buttons, description):
    """
    Тест проверяет генерацию главного меню в различных состояниях.
    """
    keyboard = main_menu_keyboard(vacancy_count, has_resume, has_selected_vacancy, show_survey_button)

    # Собираем все тексты кнопок из клавиатуры в один список
    actual_buttons_texts = [button.text for row in keyboard.inline_keyboard for button in row]

    assert actual_buttons_texts == expected_buttons, f"Ошибка в сценарии: {description}"
    assert len(actual_buttons_texts) == len(expected_buttons), f"Ошибка в сценарии: {description}"

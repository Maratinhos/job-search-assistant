from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from db.models import Vacancy
from typing import List

# --- Main Menu Keyboards ---
def main_menu_keyboard(
    vacancy_count: int,
    has_resume: bool,
    has_selected_vacancy: bool
) -> InlineKeyboardMarkup:
    """Генерирует клавиатуру для главного меню."""
    buttons = []

    if has_selected_vacancy:
        buttons.extend([
            [InlineKeyboardButton("Анализ резюме/вакансии", callback_data="analyze_match")],
            [InlineKeyboardButton("Сопроводительное письмо", callback_data="generate_letter")],
            [InlineKeyboardButton("План созвона с HR", callback_data="generate_hr_plan")],
            [InlineKeyboardButton("План тех. собеседования", callback_data="generate_tech_plan")],
        ])

    if vacancy_count > 0:
        buttons.append([InlineKeyboardButton(f"Выбрать другую вакансию ({vacancy_count})", callback_data="select_vacancy")])

    buttons.append([InlineKeyboardButton("Загрузить новую вакансию", callback_data="upload_vacancy")])

    if has_resume:
        buttons.append([InlineKeyboardButton("Обновить резюме", callback_data="update_resume")])

    return InlineKeyboardMarkup(buttons)

# --- Vacancy Selection Keyboard ---
def vacancy_selection_keyboard(vacancies: List[Vacancy]) -> InlineKeyboardMarkup:
    """Генерирует клавиатуру для выбора вакансии."""
    buttons = []
    for vacancy in vacancies:
        # callback_data will be like 'vacancy_select_123'
        buttons.append([InlineKeyboardButton(vacancy.title, callback_data=f"vacancy_select_{vacancy.id}")])

    buttons.append([InlineKeyboardButton("Загрузить новую вакансию", callback_data="upload_vacancy")])
    buttons.append([InlineKeyboardButton("Отмена", callback_data="cancel_action")])
    return InlineKeyboardMarkup(buttons)

# --- Cancel Keyboard ---
def cancel_keyboard() -> InlineKeyboardMarkup:
    """Генерирует клавиатуру с кнопкой 'Отмена'."""
    buttons = [[InlineKeyboardButton("Отмена", callback_data="cancel_action")]]
    return InlineKeyboardMarkup(buttons)

import logging
from telegram import Update
from telegram.ext import ContextTypes, CallbackQueryHandler

from bot import messages, keyboards
from .resume import AWAITING_RESUME_UPLOAD, AWAITING_VACANCY_UPLOAD, MAIN_MENU
from db import crud
from db.database import get_db

logger = logging.getLogger(__name__)


async def update_resume_request(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Обрабатывает нажатие кнопки "Обновить резюме".
    Переводит диалог в состояние ожидания нового резюме.
    """
    query = update.callback_query
    await query.answer()
    await query.edit_message_text(messages.ASK_FOR_RESUME, reply_markup=keyboards.cancel_keyboard())
    return AWAITING_RESUME_UPLOAD


async def upload_new_vacancy(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Обрабатывает нажатие кнопки "Загрузить новую вакансию" из главного меню.
    Переводит диалог в состояние ожидания вакансии.
    """
    query = update.callback_query
    await query.answer()
    await query.edit_message_text(messages.ASK_FOR_VACANCY, reply_markup=keyboards.cancel_keyboard())
    return AWAITING_VACANCY_UPLOAD


async def select_vacancy(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Обрабатывает нажатие кнопки "Выбрать другую вакансию".
    Показывает пользователю список его вакансий для выбора.
    """
    query = update.callback_query
    await query.answer()

    chat_id = update.effective_chat.id
    db_session_gen = get_db()
    db = next(db_session_gen)
    try:
        user = crud.get_or_create_user(db, chat_id=chat_id)
        vacancies = crud.get_user_vacancies(db, user_id=user.id)

        # Эта проверка на случай, если вакансии были удалены с момента последней отрисовки меню
        if not vacancies:
            # Сбрасываем выбранную вакансию, если она была
            context.user_data.pop('selected_vacancy_id', None)
            # Показываем обновленное главное меню
            await show_main_menu(update, context)
            return MAIN_MENU

        await query.edit_message_text(
            messages.CHOOSE_VACANCY_FOR_ACTION,
            reply_markup=keyboards.vacancy_selection_keyboard(vacancies)
        )
        return MAIN_MENU  # Остаемся в том же состоянии, но с другой клавиатурой
    finally:
        db.close()


from .main_menu_helpers import show_main_menu


async def on_vacancy_selected(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Обрабатывает выбор конкретной вакансии из списка.
    """
    query = update.callback_query
    await query.answer()

    vacancy_id = int(query.data.split('_')[-1])
    context.user_data['selected_vacancy_id'] = vacancy_id

    await show_main_menu(update, context)
    return MAIN_MENU

# --- Экспортируемые обработчики ---
update_resume_handler = CallbackQueryHandler(update_resume_request, pattern="^update_resume$")
upload_vacancy_handler = CallbackQueryHandler(upload_new_vacancy, pattern="^upload_vacancy$")
select_vacancy_handler = CallbackQueryHandler(select_vacancy, pattern="^select_vacancy$")
vacancy_selected_handler = CallbackQueryHandler(on_vacancy_selected, pattern="^vacancy_select_")

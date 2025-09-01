import logging
from telegram import Update
from telegram.ext import ContextTypes

from bot import messages, keyboards
from db import crud
from db.database import get_db
from .states import AWAITING_RESUME_UPLOAD

logger = logging.getLogger(__name__)

async def show_main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Отображает главное меню с учетом текущего состояния (выбранная вакансия и т.д.).
    """
    chat_id = update.effective_chat.id
    db_session_gen = get_db()
    db = next(db_session_gen)
    try:
        user = crud.get_or_create_user(db, chat_id=chat_id)
        resume = crud.get_user_resume(db, user_id=user.id)
        vacancies = crud.get_user_vacancies(db, user_id=user.id)
        selected_vacancy_id = context.user_data.get('selected_vacancy_id')

        message_text = ""
        keyboard = None

        if not resume:
            # Этого не должно происходить в нормальном потоке, но на всякий случай
            await update.effective_message.reply_text(messages.ASK_FOR_RESUME)
            return AWAITING_RESUME_UPLOAD

        resume_title = resume.title or "ваше резюме"

        if selected_vacancy_id:
            selected_vacancy = crud.get_vacancy_by_id(db, vacancy_id=selected_vacancy_id)
            if selected_vacancy:
                message_text = messages.MAIN_MENU_WITH_VACANCY_MESSAGE.format(
                    vacancy_title=selected_vacancy.title,
                    resume_title=resume_title
                )
                keyboard = keyboards.main_menu_keyboard(
                    vacancy_count=len(vacancies),
                    has_resume=True,
                    has_selected_vacancy=True
                )
            else:
                # Если ID вакансии есть, но вакансия не найдена, сбрасываем ID
                context.user_data.pop('selected_vacancy_id', None)
                selected_vacancy_id = None # Обновляем локальную переменную

        if not selected_vacancy_id:
            if vacancies:
                message_text = messages.MAIN_MENU_MESSAGE.format(resume_title=resume_title)
                keyboard = keyboards.main_menu_keyboard(
                    vacancy_count=len(vacancies),
                    has_resume=True,
                    has_selected_vacancy=False
                )
            else:
                message_text = messages.MAIN_MENU_NO_VACANCIES.format(resume_title=resume_title)
                # Клавиатура без действий, требующих вакансию
                keyboard = keyboards.main_menu_keyboard(
                    vacancy_count=0,
                    has_resume=True,
                    has_selected_vacancy=False
                )

        # Отправляем или редактируем сообщение
        query = update.callback_query
        if query:
            await query.edit_message_text(message_text, reply_markup=keyboard)
        else:
            await update.effective_message.reply_text(message_text, reply_markup=keyboard)

    finally:
        db.close()

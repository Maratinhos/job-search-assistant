import logging
from telegram import Update
from telegram.ext import ContextTypes

from db.database import get_db
from db import crud
from bot import messages, keyboards
from .resume import AWAITING_RESUME_UPLOAD, AWAITING_VACANCY_UPLOAD, MAIN_MENU

logger = logging.getLogger(__name__)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Точка входа в главный диалог.
    Проверяет состояние пользователя (наличие резюме/вакансий) и направляет его
    в соответствующее состояние конечного автомата (AWAITING_RESUME_UPLOAD, etc.).
    """
    chat_id = update.effective_chat.id
    logger.info(f"Conversation started for user {chat_id}")

    db_session_gen = get_db()
    db = next(db_session_gen)

    try:
        user = crud.get_or_create_user(db, chat_id=chat_id)
        resume = crud.get_user_resume(db, user_id=user.id)

        # 1. Если нет резюме, просим загрузить
        if not resume:
            await update.message.reply_text(messages.WELCOME_MESSAGE)
            await update.message.reply_text(messages.ASK_FOR_RESUME, reply_markup=keyboards.cancel_keyboard())
            return AWAITING_RESUME_UPLOAD

        # 2. Если есть резюме, но нет вакансий
        vacancies = crud.get_user_vacancies(db, user_id=user.id)
        if not vacancies:
            await update.message.reply_text(
                messages.MAIN_MENU_NO_VACANCIES.format(resume_title=resume.title),
            )
            await update.message.reply_text(messages.ASK_FOR_VACANCY, reply_markup=keyboards.cancel_keyboard())
            return AWAITING_VACANCY_UPLOAD

        # 3. Если все есть, переходим в главное меню
        vacancy_count = len(vacancies)
        # По умолчанию выбираем последнюю загруженную вакансию
        context.user_data['selected_vacancy_id'] = vacancies[0].id

        await update.message.reply_text(
            messages.MAIN_MENU_MESSAGE.format(resume_title=resume.title, vacancy_count=vacancy_count),
            reply_markup=keyboards.main_menu_keyboard(vacancy_count=vacancy_count, has_resume=True)
        )
        return MAIN_MENU

    finally:
        db.close()

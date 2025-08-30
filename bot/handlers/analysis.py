import logging
from telegram import Update
from telegram.ext import ContextTypes, CallbackQueryHandler

from .resume import MAIN_MENU
from bot import messages
from db import crud
from db.database import get_db
from ai.client import ai_client

logger = logging.getLogger(__name__)


async def _perform_analysis(update: Update, context: ContextTypes.DEFAULT_TYPE, action: str) -> int:
    """
    Общий обработчик для всех действий анализа из главного меню.
    """
    query = update.callback_query
    await query.answer()

    chat_id = update.effective_chat.id
    vacancy_id = context.user_data.get('selected_vacancy_id')

    if not vacancy_id:
        await query.message.reply_text(text=messages.CHOOSE_VACANCY_FOR_ACTION)
        return MAIN_MENU

    await query.message.reply_text(text="⏳ Выполняю ваш запрос... Это может занять некоторое время.")

    db_session_gen = get_db()
    db = next(db_session_gen)
    try:
        user = crud.get_or_create_user(db, chat_id=chat_id)
        resume = crud.get_user_resume(db, user_id=user.id)
        vacancy = crud.get_vacancy_by_id(db, vacancy_id=vacancy_id)

        if not resume or not vacancy:
            await query.message.reply_text(text=messages.ERROR_MESSAGE)
            return MAIN_MENU

        # Чтение текстов из файлов
        try:
            with open(resume.file_path, 'r', encoding='utf-8') as f:
                resume_text = f.read()
            with open(vacancy.file_path, 'r', encoding='utf-8') as f:
                vacancy_text = f.read()
        except FileNotFoundError:
            logger.error(f"Файл резюме или вакансии не найден для пользователя {chat_id}.")
            await query.message.reply_text(text=messages.ERROR_MESSAGE)
            return MAIN_MENU

        # Вызов AI и логирование
        response = {}
        header = ""
        if action == "analyze_match":
            header = messages.ANALYSIS_COMPLETE
            response = ai_client.analyze_match(resume_text, vacancy_text)
        elif action == "generate_letter":
            header = messages.COVER_LETTER_COMPLETE
            response = ai_client.generate_cover_letter(resume_text, vacancy_text)
        elif action == "generate_hr_plan":
            header = messages.HR_CALL_PLAN_COMPLETE
            response = ai_client.generate_hr_call_plan(resume_text, vacancy_text)
        elif action == "generate_tech_plan":
            header = messages.TECH_INTERVIEW_PLAN_COMPLETE
            response = ai_client.generate_tech_interview_plan(resume_text, vacancy_text)
        else:
            await query.message.reply_text(text=messages.NOT_IMPLEMENTED)
            return MAIN_MENU

        # Логирование использования AI
        usage = response.get("usage", {})
        crud.create_ai_usage_log(
            db,
            user_id=user.id,
            prompt_tokens=usage.get("prompt_tokens", 0),
            completion_tokens=usage.get("completion_tokens", 0),
            total_tokens=usage.get("total_tokens", 0),
        )

        response_text = response.get("text", "Не удалось получить ответ от AI.")
        await query.message.reply_text(text=f"{header}\n\n{response_text}")

    except Exception as e:
        logger.error(f"Ошибка во время выполнения действия '{action}' для пользователя {chat_id}: {e}", exc_info=True)
        await query.message.reply_text(text=messages.ERROR_MESSAGE)
    finally:
        db.close()

    return MAIN_MENU

# Создаем обработчики для каждой кнопки, используя лямбда-функцию для передачи названия действия
analyze_match_handler = CallbackQueryHandler(
    lambda u, c: _perform_analysis(u, c, "analyze_match"), pattern="^analyze_match$"
)
generate_letter_handler = CallbackQueryHandler(
    lambda u, c: _perform_analysis(u, c, "generate_letter"), pattern="^generate_letter$"
)
generate_hr_plan_handler = CallbackQueryHandler(
    lambda u, c: _perform_analysis(u, c, "generate_hr_plan"), pattern="^generate_hr_plan$"
)
generate_tech_plan_handler = CallbackQueryHandler(
    lambda u, c: _perform_analysis(u, c, "generate_tech_plan"), pattern="^generate_tech_plan$"
)

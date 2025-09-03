import logging
import os
import uuid
from telegram import Update
from telegram.ext import ContextTypes, CallbackQueryHandler

from .resume import MAIN_MENU
from bot import messages
from db import crud
from db.database import get_db
from ai.client import get_ai_client
from ai.actions import ACTION_REGISTRY

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

    db_session_gen = get_db()
    db = next(db_session_gen)
    try:
        user = crud.get_or_create_user(db, chat_id=chat_id)
        resume = crud.get_user_resume(db, user_id=user.id)
        vacancy = crud.get_vacancy_by_id(db, vacancy_id=vacancy_id)

        if not resume or not vacancy:
            await query.message.reply_text(text=messages.ERROR_MESSAGE)
            return MAIN_MENU

        analysis_result = crud.get_analysis_result(db, resume.id, vacancy.id)
        action_details = ACTION_REGISTRY.get(action)
        db_field = action_details.get("db_field")

        # Проверяем, есть ли уже результат для этого действия
        if analysis_result and hasattr(analysis_result, db_field) and getattr(analysis_result, db_field):
            response_text = getattr(analysis_result, db_field)
            logger.info(f"Найден кэшированный результат для action='{action}', user_id={user.id}")
        else:
            # Если кэша нет, запускаем полный анализ
            await query.message.reply_text(text=messages.ANALYSIS_IN_PROGRESS)

            try:
                with open(resume.file_path, 'r', encoding='utf-8') as f:
                    resume_text = f.read()
                with open(vacancy.file_path, 'r', encoding='utf-8') as f:
                    vacancy_text = f.read()
            except FileNotFoundError:
                logger.error(f"Файл резюме или вакансии не найден для пользователя {chat_id}.")
                await query.message.reply_text(text=messages.ERROR_MESSAGE)
                return MAIN_MENU

            ai_client = get_ai_client()
            response = ai_client.get_consolidated_analysis(resume_text, vacancy_text)

            if not response or not response.get("json"):
                logger.error(f"Ошибка при получении полного анализа от AI: {response}")
                await query.message.reply_text(text=messages.AI_ERROR_RESPONSE)
                return MAIN_MENU

            analysis_data = response["json"]
            crud.create_analysis_result(db, resume.id, vacancy.id, analysis_data)
            response_text = analysis_data.get(db_field)

            # Логирование использования AI
            usage = response.get("usage", {})
            crud.create_ai_usage_log(
                db=db, user_id=user.id,
                prompt_tokens=usage.get("prompt_tokens", 0),
                completion_tokens=usage.get("completion_tokens", 0),
                total_tokens=usage.get("total_tokens", 0),
                cost=usage.get("cost", 0.0),
                action="consolidated_analysis",
                resume_id=resume.id, vacancy_id=vacancy.id
            )

        # Отправка результата пользователю
        if response_text:
            header = action_details["response_header"]
            message_text = f"{header}\n\n{response_text}"
            message_text_parts = [message_text[i:i + 4000] for i in range(0, len(message_text), 4000)]
            for part in message_text_parts:
                await query.message.reply_text(text=part)
        else:
            logger.error(f"Не удалось получить текст для '{action}' после анализа.")
            await query.message.reply_text(text=messages.ERROR_MESSAGE)

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

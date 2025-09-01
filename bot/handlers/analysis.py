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

        # Проверяем кэш
        cached_result = crud.get_analysis_result(db, resume.id, vacancy.id, action)
        if cached_result:
            logger.info(f"Найден кэшированный результат для action='{action}', user_id={user.id}")
            try:
                with open(cached_result.file_path, 'r', encoding='utf-8') as f:
                    response_text = f.read()
                header = _get_header_for_action(action)
                message_text = f"{header}\n\n{response_text}"
                message_text_parts = [message_text[i:i+4000] for i in range(0, len(message_text), 4000)]
                for message_text_part in message_text_parts:
                    await query.message.reply_text(text=message_text_part)
                return MAIN_MENU
            except FileNotFoundError:
                logger.warning(f"Файл для кэшированного результата не найден: {cached_result.file_path}")
                # Если файл не найден, продолжаем как обычно, чтобы сгенерировать новый

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

        # Получаем клиент AI
        ai_client = get_ai_client()

        # Вызов AI и логирование
        response = _call_ai_for_action(ai_client, action, resume_text, vacancy_text)
        if not response:
            await query.message.reply_text(text=messages.NOT_IMPLEMENTED)
            return MAIN_MENU

        response_text = response.get("text", "Не удалось получить ответ от AI.")
        if not response.get("text"):
            # Если текста нет, вероятно, произошла ошибка, и мы уже уведомили пользователя.
            # Просто выходим, чтобы не сохранять пустой файл и не падать.
            logger.warning(f"Действие '{action}' не вернуло текст от AI. Ответ: {response}")
            # Отправляем сообщение об ошибке, если его еще не было
            if "error" in response:
                await query.message.reply_text(text=messages.ERROR_MESSAGE)
            return MAIN_MENU

        header = _get_header_for_action(action)

        # Сохранение результата анализа
        analysis_dir = "storage/analysis_results"
        os.makedirs(analysis_dir, exist_ok=True)
        file_name = f"{uuid.uuid4()}.txt"
        file_path = os.path.join(analysis_dir, file_name)
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(response_text)

        crud.create_analysis_result(
            db,
            resume_id=resume.id,
            vacancy_id=vacancy.id,
            action_type=action,
            file_path=file_path,
        )

        # Логирование использования AI
        usage = response.get("usage", {})
        crud.create_ai_usage_log(
            db=db,
            user_id=user.id,
            prompt_tokens=usage.get("prompt_tokens", 0),
            completion_tokens=usage.get("completion_tokens", 0),
            total_tokens=usage.get("total_tokens", 0),
            cost=usage.get("cost", 0.0),
            action=action,
            resume_id=resume.id,
            vacancy_id=vacancy.id,
        )

        message_text = f"{header}\n\n{response_text}"
        message_text_parts = [message_text[i:i+4000] for i in range(0, len(message_text), 4000)]
        for message_text_part in message_text_parts:
            await query.message.reply_text(text=message_text_part)

    except Exception as e:
        logger.error(f"Ошибка во время выполнения действия '{action}' для пользователя {chat_id}: {e}", exc_info=True)
        await query.message.reply_text(text=messages.ERROR_MESSAGE)
    finally:
        db.close()

    return MAIN_MENU


def _get_header_for_action(action: str) -> str:
    """Возвращает заголовок в зависимости от действия."""
    headers = {
        "analyze_match": messages.ANALYSIS_COMPLETE,
        "generate_letter": messages.COVER_LETTER_COMPLETE,
        "generate_hr_plan": messages.HR_CALL_PLAN_COMPLETE,
        "generate_tech_plan": messages.TECH_INTERVIEW_PLAN_COMPLETE,
    }
    return headers.get(action, "Результат готов")


def _call_ai_for_action(ai_client, action: str, resume_text: str, vacancy_text: str) -> dict:
    """Вызывает соответствующий метод AI в зависимости от действия."""
    if action == "analyze_match":
        return ai_client.analyze_match(resume_text, vacancy_text)
    elif action == "generate_letter":
        return ai_client.generate_cover_letter(resume_text, vacancy_text)
    elif action == "generate_hr_plan":
        return ai_client.generate_hr_call_plan(resume_text, vacancy_text)
    elif action == "generate_tech_plan":
        return ai_client.generate_tech_interview_plan(resume_text, vacancy_text)
    return {}

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

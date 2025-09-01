import logging
import json
from telegram import Update
from telegram.ext import ContextTypes
from sqlalchemy.orm import Session
from db import crud
from ai.client import get_ai_client
from bot.file_utils import save_text_to_file

logger = logging.getLogger(__name__)

async def process_document(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    db: Session,
    user_id: int,
    text: str,
    source: str,
    doc_type: str,
) -> tuple[bool, str | None]:
    """
    Универсальная функция для обработки документов (резюме и вакансий).

    :param update: Объект Update от Telegram.
    :param context: Объект Context от Telegram.
    :param db: Сессия базы данных.
    :param user_id: ID пользователя.
    :param text: Текст документа.
    :param source: Источник документа (имя файла или URL).
    :param doc_type: Тип документа ('resume' или 'vacancy').
    :return: Кортеж (успех, заголовок документа или None).
    """
    ai_client = get_ai_client()

    # 1. Определяем, какой метод AI и CRUD использовать
    if doc_type == "resume":
        verify_method = ai_client.verify_resume
        create_crud_method = crud.create_resume
        action_name = "verify_resume"
        folder_name = "resumes"
        json_key_check = "is_resume"
    elif doc_type == "vacancy":
        verify_method = ai_client.verify_vacancy
        create_crud_method = crud.create_vacancy
        action_name = "verify_vacancy"
        folder_name = "vacancies"
        json_key_check = "is_vacancy"
    else:
        logger.error(f"Unknown document type: {doc_type}")
        return False, None

    # 2. Валидация с помощью AI
    response_data = verify_method(text)

    # 3. Логирование использования AI
    usage = response_data.get("usage", {})
    crud.create_ai_usage_log(
        db=db,
        user_id=user_id,
        prompt_tokens=usage.get("prompt_tokens", 0),
        completion_tokens=usage.get("completion_tokens", 0),
        total_tokens=usage.get("total_tokens", 0),
        cost=usage.get("cost", 0.0),
        action=action_name,
    )

    # 4. Обработка ответа AI
    response_text = response_data.get("text", "{}")
    if not response_text or "error" in response_data:
        logger.error(f"AI verification failed for user {user_id}. Response: {response_data}")
        return False, None

    try:
        if isinstance(response_text, str):
            response_text = response_text.strip()
            if response_text.startswith("```json"):
                response_text = response_text[7:-4].strip()
            elif response_text.startswith("```"):
                response_text = response_text[3:-3].strip()
            response_json = json.loads(response_text)
        else:
            response_json = response_text

        is_valid_doc = response_json.get(json_key_check, False)
        title = response_json.get("title")
    except (json.JSONDecodeError, AttributeError, KeyError, IndexError, TypeError) as e:
        logger.error(f"Failed to parse AI response: {response_data}. Error: {e}")
        is_valid_doc = False
        title = None

    if not is_valid_doc:
        return False, None

    # 5. Сохранение файла
    file_path = save_text_to_file(text, folder_name)
    if not file_path:
        return False, None

    # 6. Сохранение в БД
    if doc_type == "resume":
        crud.create_resume(db, user_id=user_id, file_path=file_path, source=source, title=title)
    elif doc_type == "vacancy":
        vacancy = create_crud_method(db, user_id=user_id, title=title, file_path=file_path, source=source)
        # Сохраняем ID новой вакансии как выбранной по умолчанию
        context.user_data['selected_vacancy_id'] = vacancy.id


    return True, title

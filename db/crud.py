from typing import Optional
from sqlalchemy.orm import Session

from . import models


# User functions
def get_or_create_user(db: Session, chat_id: int) -> models.User:
    """
    Получает пользователя по chat_id или создает нового.
    Новому пользователю начисляется бесплатный тариф.
    """
    user = db.query(models.User).filter(models.User.chat_id == chat_id).first()
    if not user:
        user = models.User(chat_id=chat_id)
        db.add(user)
        db.commit()
        db.refresh(user)

        # Начисляем бесплатный тариф
        free_tariff = get_tariff_by_id(db, 1)
        if free_tariff:
            create_purchase(db, user_id=user.id, tariff_id=free_tariff.id)

    return user


# Tariff functions
def get_tariff_by_id(db: Session, tariff_id: int) -> Optional[models.Tariff]:
    """Получает тариф по ID."""
    return db.query(models.Tariff).filter(models.Tariff.id == tariff_id).first()


def get_tariffs(db: Session) -> list[models.Tariff]:
    """Возвращает список всех активных тарифов, кроме бесплатного."""
    return db.query(models.Tariff).filter(models.Tariff.is_active == True, models.Tariff.id != 1).all()


# Purchase functions
def create_purchase(db: Session, user_id: int, tariff_id: int) -> models.Purchase:
    """Создает новую покупку для пользователя и деактивирует старые."""
    # Деактивируем все предыдущие активные покупки пользователя
    db.query(models.Purchase).filter(
        models.Purchase.user_id == user_id,
        models.Purchase.is_active == True
    ).update({"is_active": False})

    tariff = get_tariff_by_id(db, tariff_id)
    if not tariff:
        raise ValueError("Tariff not found")

    new_purchase = models.Purchase(
        user_id=user_id,
        tariff_id=tariff_id,
        runs_total=tariff.runs_count,
        runs_left=tariff.runs_count,
        is_active=True
    )
    db.add(new_purchase)
    db.commit()
    db.refresh(new_purchase)
    return new_purchase


def get_active_purchase(db: Session, user_id: int) -> Optional[models.Purchase]:
    """Получает активную покупку пользователя."""
    return db.query(models.Purchase).filter(
        models.Purchase.user_id == user_id,
        models.Purchase.is_active == True
    ).first()


# Run functions
def create_run(db: Session, user_id: int, resume_id: int, vacancy_id: int) -> Optional[models.Run]:
    """
    Создает запись о прогоне и списывает один прогон у пользователя.
    Возвращает Run, если списание успешно, иначе None.
    """
    active_purchase = get_active_purchase(db, user_id)
    if not active_purchase or active_purchase.runs_left <= 0:
        return None  # Нет доступных прогонов

    # Проверяем, был ли уже такой прогон
    existing_run = get_run_by_resume_and_vacancy(db, resume_id, vacancy_id)
    if existing_run:
        return existing_run # Прогон уже был, ничего не списываем

    # Списываем прогон
    active_purchase.runs_left -= 1

    new_run = models.Run(
        user_id=user_id,
        purchase_id=active_purchase.id,
        resume_id=resume_id,
        vacancy_id=vacancy_id
    )
    db.add(new_run)
    db.commit()
    db.refresh(new_run)
    db.refresh(active_purchase)

    return new_run


def get_run_by_resume_and_vacancy(db: Session, resume_id: int, vacancy_id: int) -> Optional[models.Run]:
    """Проверяет, был ли уже прогон для данной пары резюме и вакансии."""
    return db.query(models.Run).filter_by(resume_id=resume_id, vacancy_id=vacancy_id).first()


# AI Usage Log functions
def create_ai_usage_log(
    db: Session,
    user_id: int,
    prompt_tokens: int,
    completion_tokens: int,
    total_tokens: int,
    cost: float,
    action: str,
    resume_id: Optional[int] = None,
    vacancy_id: Optional[int] = None,
) -> models.AIUsageLog:
    """Создает запись о использовании AI."""
    new_log = models.AIUsageLog(
        user_id=user_id,
        prompt_tokens=prompt_tokens,
        completion_tokens=completion_tokens,
        total_tokens=total_tokens,
        cost=cost,
        action=action,
        resume_id=resume_id,
        vacancy_id=vacancy_id,
    )
    db.add(new_log)
    db.commit()
    db.refresh(new_log)
    return new_log


# Resume functions
def get_user_resume(db: Session, user_id: int) -> Optional[models.Resume]:
    """Получает резюме пользователя."""
    return db.query(models.Resume).filter(models.Resume.user_id == user_id).first()


def create_resume(db: Session, user_id: int, file_path: str, source: str, title: str) -> models.Resume:
    """Создает или обновляет резюме пользователя."""
    # У пользователя может быть только одно резюме, поэтому удаляем старое, если оно есть
    existing_resume = get_user_resume(db, user_id)
    if existing_resume:
        db.delete(existing_resume)
        db.commit()

    new_resume = models.Resume(user_id=user_id, file_path=file_path, source=source, title=title)
    db.add(new_resume)
    db.commit()
    db.refresh(new_resume)
    return new_resume


# Vacancy functions
def get_user_vacancies(db: Session, user_id: int) -> list[models.Vacancy]:
    """Получает все вакансии пользователя."""
    return db.query(models.Vacancy).filter(models.Vacancy.user_id == user_id).order_by(models.Vacancy.id.desc()).all()


def get_vacancy_by_id(db: Session, vacancy_id: int) -> Optional[models.Vacancy]:
    """Получает вакансию по ее ID."""
    return db.query(models.Vacancy).filter(models.Vacancy.id == vacancy_id).first()


def create_vacancy(db: Session, user_id: int, file_path: str, source: str, title: Optional[str] = None) -> models.Vacancy:
    """Создает новую вакансию для пользователя."""
    new_vacancy = models.Vacancy(user_id=user_id, file_path=file_path, source=source, title=title)
    db.add(new_vacancy)
    db.commit()
    db.refresh(new_vacancy)
    return new_vacancy


# AnalysisResult functions
def get_analysis_result(db: Session, resume_id: int, vacancy_id: int) -> Optional[models.AnalysisResult]:
    """Получает результат анализа по ID резюме и вакансии."""
    return db.query(models.AnalysisResult).filter_by(resume_id=resume_id, vacancy_id=vacancy_id).first()


def create_analysis_result(db: Session, resume_id: int, vacancy_id: int, analysis_data: dict) -> models.AnalysisResult:
    """Создает или обновляет запись с результатами анализа."""
    existing_analysis = get_analysis_result(db, resume_id, vacancy_id)
    if existing_analysis:
        for key, value in analysis_data.items():
            setattr(existing_analysis, key, value)
        db.commit()
        db.refresh(existing_analysis)
        return existing_analysis
    else:
        new_analysis = models.AnalysisResult(
            resume_id=resume_id,
            vacancy_id=vacancy_id,
            **analysis_data,
        )
        db.add(new_analysis)
        db.commit()
        db.refresh(new_analysis)
        return new_analysis


# Survey functions
def get_active_survey(db: Session) -> Optional[models.Survey]:
    """Возвращает первый активный опрос."""
    return db.query(models.Survey).filter(models.Survey.is_active == True).first()


def create_survey(db: Session, question: str, options: list[str]) -> models.Survey:
    """Создает новый опрос и делает все остальные неактивными."""
    # Деактивируем все существующие опросы
    db.query(models.Survey).update({models.Survey.is_active: False})

    # Создаем новый активный опрос
    new_survey = models.Survey(
        question=question,
        options=",".join(options),  # Простое хранение через запятую
        is_active=True
    )
    db.add(new_survey)
    db.commit()
    db.refresh(new_survey)
    return new_survey


def create_survey_answer(db: Session, user_id: int, survey_id: int, answer: str) -> models.SurveyAnswer:
    """Создает ответ пользователя на опрос."""
    new_answer = models.SurveyAnswer(
        user_id=user_id,
        survey_id=survey_id,
        answer=answer
    )
    db.add(new_answer)
    db.commit()
    db.refresh(new_answer)
    return new_answer


# UTMTrack functions
def create_utm_track(db: Session, user_id: int, utm_source: str) -> models.UTMTrack:
    """Создает запись об источнике UTM."""
    new_track = models.UTMTrack(user_id=user_id, utm_source=utm_source)
    db.add(new_track)
    db.commit()
    db.refresh(new_track)
    return new_track

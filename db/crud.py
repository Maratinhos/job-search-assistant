from typing import Optional
from sqlalchemy.orm import Session

from . import models


# User functions
def get_or_create_user(db: Session, chat_id: int) -> models.User:
    """
    Получает пользователя по chat_id или создает нового.
    Новому пользователю начисляется приветственный баланс.
    """
    user = db.query(models.User).filter(models.User.chat_id == chat_id).first()
    if not user:
        user = models.User(chat_id=chat_id)
        db.add(user)
        db.commit()
        db.refresh(user)
        # Начисляем приветственные баллы
        get_or_create_balance(db, user_id=user.id, initial_balance=6)
    return user


# Balance and Transaction functions
def get_or_create_balance(db: Session, user_id: int, initial_balance: int = 0) -> models.UserBalance:
    """Получает или создает баланс для пользователя."""
    balance = db.query(models.UserBalance).filter_by(user_id=user_id).first()
    if not balance:
        balance = models.UserBalance(user_id=user_id, balance=initial_balance)
        db.add(balance)
        db.commit()
        db.refresh(balance)
        # Создаем транзакцию о начислении приветственных баллов
        if initial_balance > 0:
            create_transaction(
                db,
                user_id=user_id,
                type="deposit",
                amount=initial_balance,
                description="Приветственный бонус",
            )
    return balance


def get_user_balance(db: Session, user_id: int) -> Optional[models.UserBalance]:
    """Получает баланс пользователя."""
    return db.query(models.UserBalance).filter_by(user_id=user_id).first()


def update_user_balance(db: Session, user_id: int, amount: int, description: str, cost: Optional[float] = None) -> models.UserBalance:
    """
    Обновляет баланс пользователя и создает транзакцию.
    amount может быть положительным (пополнение) или отрицательным (списание).
    """
    balance = get_or_create_balance(db, user_id)
    balance.balance += amount

    transaction_type = "deposit" if amount > 0 else "withdrawal"

    create_transaction(
        db,
        user_id=user_id,
        type=transaction_type,
        amount=abs(amount),
        description=description,
        cost=cost,
    )

    db.commit()
    db.refresh(balance)
    return balance


def create_transaction(
    db: Session,
    user_id: int,
    type: str,
    amount: int,
    description: str,
    cost: Optional[float] = None,
    external_id: Optional[str] = None,
) -> models.Transaction:
    """Создает новую транзакцию."""
    transaction = models.Transaction(
        user_id=user_id,
        type=type,
        amount=amount,
        description=description,
        cost=cost,
        external_id=external_id,
    )
    db.add(transaction)
    db.commit()
    db.refresh(transaction)
    return transaction


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

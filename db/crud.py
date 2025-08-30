from typing import Optional
from sqlalchemy.orm import Session

from . import models


# User functions
def get_or_create_user(db: Session, chat_id: int) -> models.User:
    """Получает пользователя по chat_id или создает нового, если он не существует."""
    user = db.query(models.User).filter(models.User.chat_id == chat_id).first()
    if not user:
        user = models.User(chat_id=chat_id)
        db.add(user)
        db.commit()
        db.refresh(user)
    return user


# Resume functions
def get_user_resume(db: Session, user_id: int) -> Optional[models.Resume]:
    """Получает резюме пользователя."""
    return db.query(models.Resume).filter(models.Resume.user_id == user_id).first()


def create_resume(db: Session, user_id: int, text: str, source: str) -> models.Resume:
    """Создает или обновляет резюме пользователя."""
    # У пользователя может быть только одно резюме, поэтому удаляем старое, если оно есть
    existing_resume = get_user_resume(db, user_id)
    if existing_resume:
        db.delete(existing_resume)
        db.commit()

    new_resume = models.Resume(user_id=user_id, text=text, source=source)
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


def create_vacancy(db: Session, user_id: int, name: str, text: str, source: str) -> models.Vacancy:
    """Создает новую вакансию для пользователя."""
    new_vacancy = models.Vacancy(user_id=user_id, name=name, text=text, source=source)
    db.add(new_vacancy)
    db.commit()
    db.refresh(new_vacancy)
    return new_vacancy

import pytest
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from db.models import Base

# Используем in-memory SQLite базу данных для тестов, чтобы не затрагивать основную БД
# и обеспечить изоляцию тестов.
TEST_DATABASE_URL = "sqlite:///:memory:"


@pytest.fixture(scope="function")
def db_session():
    """
    Фикстура pytest для создания новой сессии БД для каждой тестовой функции.
    """
    # Создаем движок и таблицы для тестовой БД
    engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)

    # Создаем фабрику сессий
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    db = TestingSessionLocal()
    try:
        # Передаем сессию в тестовую функцию
        yield db
    finally:
        # Закрываем сессию и удаляем все таблицы после завершения теста
        db.close()
        Base.metadata.drop_all(bind=engine)

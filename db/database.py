from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from config import DB_NAME
from db.models import Base

# Строка подключения к базе данных SQLite
DATABASE_URL = f"sqlite:///{DB_NAME}"

# Создаем движок SQLAlchemy
engine = create_engine(
    DATABASE_URL,
    # connect_args необходим для SQLite для работы в многопоточном окружении (например, в боте)
    connect_args={"check_same_thread": False},
)

# Создаем класс для сессий
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def init_db():
    """
    Инициализирует базу данных.
    Создает все таблицы, определенные в моделях.
    """
    # Base.metadata.drop_all(bind=engine) # Раскомментируйте для удаления всех таблиц при перезапуске
    Base.metadata.create_all(bind=engine)


def get_db():
    """
    Функция-генератор для получения сессии базы данных.
    Обеспечивает правильное открытие и закрытие сессии.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

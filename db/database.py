from alembic import command
from alembic.config import Config
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
    Применяет миграции Alembic для обновления схемы до последней версии.
    """
    alembic_cfg = Config("alembic.ini")
    alembic_cfg.set_main_option("sqlalchemy.url", DATABASE_URL)
    command.upgrade(alembic_cfg, "head")


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

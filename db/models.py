from sqlalchemy import (
    Column,
    Integer,
    String,
    Text,
    ForeignKey,
    BigInteger,
    DateTime,
    Float,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship, declarative_base
from sqlalchemy.sql import func

Base = declarative_base()


class User(Base):
    """Модель пользователя."""

    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    chat_id = Column(BigInteger, unique=True, nullable=False, index=True)

    resumes = relationship("Resume", back_populates="user", cascade="all, delete-orphan")
    vacancies = relationship("Vacancy", back_populates="user", cascade="all, delete-orphan")
    ai_usage_logs = relationship("AIUsageLog", back_populates="user", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<User(id={self.id}, chat_id={self.chat_id})>"


class Resume(Base):
    """Модель резюме."""

    __tablename__ = "resumes"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    file_path = Column(String(255), nullable=False)
    source = Column(String(255), nullable=True)  # e.g., 'hh.ru', 'file.txt'
    title = Column(String(255), nullable=True)

    user = relationship("User", back_populates="resumes")
    analysis_results = relationship("AnalysisResult", back_populates="resume", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Resume(id={self.id}, user_id={self.user_id}, title='{self.title}')>"


class Vacancy(Base):
    """Модель вакансии."""

    __tablename__ = "vacancies"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    title = Column(String(255), nullable=True)  # The title of the vacancy
    file_path = Column(String(255), nullable=False)
    source = Column(String(255), nullable=True)

    user = relationship("User", back_populates="vacancies")
    analysis_results = relationship("AnalysisResult", back_populates="vacancy", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Vacancy(id={self.id}, title='{self.title}', user_id={self.user_id})>"


class AIUsageLog(Base):
    """Модель для логирования использования AI."""

    __tablename__ = "ai_usage_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    resume_id = Column(Integer, ForeignKey("resumes.id"), nullable=True)
    vacancy_id = Column(Integer, ForeignKey("vacancies.id"), nullable=True)
    action = Column(String(255), nullable=False)
    prompt_tokens = Column(Integer, nullable=False)
    completion_tokens = Column(Integer, nullable=False)
    total_tokens = Column(Integer, nullable=False)
    cost = Column(Float, nullable=True)  # Добавлено поле стоимости
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User", back_populates="ai_usage_logs")
    resume = relationship("Resume")
    vacancy = relationship("Vacancy")

    def __repr__(self):
        return f"<AIUsageLog(id={self.id}, user_id={self.user_id}, total_tokens={self.total_tokens})>"


class AnalysisResult(Base):
    """Модель для хранения результатов анализа."""

    __tablename__ = "analysis_results"

    id = Column(Integer, primary_key=True, index=True)
    resume_id = Column(Integer, ForeignKey("resumes.id"), nullable=False, index=True)
    vacancy_id = Column(Integer, ForeignKey("vacancies.id"), nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    match_analysis = Column(String(255), nullable=True)
    cover_letter = Column(String(255), nullable=True)
    hr_call_plan = Column(String(255), nullable=True)
    tech_interview_plan = Column(String(255), nullable=True)

    resume = relationship("Resume", back_populates="analysis_results")
    vacancy = relationship("Vacancy", back_populates="analysis_results")

    __table_args__ = (
        UniqueConstraint("resume_id", "vacancy_id", name="uq_resume_vacancy"),
    )

    def __repr__(self):
        return f"<AnalysisResult(id={self.id}, resume_id={self.resume_id}, vacancy_id={self.vacancy_id})>"

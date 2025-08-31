from .providers.gen_api import GenAPIProvider
from . import prompts

# Здесь можно легко переключить провайдера, изменив одну строку
# from .providers.openai import OpenAIProvider
AIProvider = GenAPIProvider


class AIClient:
    """
    Абстрактный клиент для работы с нейросетью.
    Использует выбранного провайдера для выполнения запросов.
    Возвращает полный ответ от провайдера, включая статистику по токенам.
    """

    def __init__(self):
        self.provider = AIProvider()

    def verify_resume(self, resume_text: str) -> dict:
        """Проверяет, является ли текст резюме."""
        return self.provider.verify_text(resume_text, prompts.VERIFY_RESUME_PROMPT)

    def verify_vacancy(self, vacancy_text: str) -> dict:
        """Проверяет, является ли текст вакансией."""
        return self.provider.verify_text(vacancy_text, prompts.VERIFY_VACANCY_PROMPT)

    def analyze_match(self, resume_text: str, vacancy_text: str) -> dict:
        """Анализирует соответствие резюме и вакансии."""
        return self.provider.analyze(
            prompts.ANALYZE_MATCH_PROMPT,
            resume_text=resume_text,
            vacancy_text=vacancy_text,
        )

    def generate_cover_letter(self, resume_text: str, vacancy_text: str) -> dict:
        """Генерирует сопроводительное письмо."""
        return self.provider.analyze(
            prompts.GENERATE_COVER_LETTER_PROMPT,
            resume_text=resume_text,
            vacancy_text=vacancy_text,
        )

    def generate_hr_call_plan(self, resume_text: str, vacancy_text: str) -> dict:
        """Генерирует план для созвона с HR."""
        return self.provider.analyze(
            prompts.GENERATE_HR_CALL_PLAN_PROMPT,
            resume_text=resume_text,
            vacancy_text=vacancy_text,
        )

    def generate_tech_interview_plan(self, resume_text: str, vacancy_text: str) -> dict:
        """Генерирует план для технического интервью."""
        return self.provider.analyze(
            prompts.GENERATE_TECH_INTERVIEW_PLAN_PROMPT,
            resume_text=resume_text,
            vacancy_text=vacancy_text,
        )


# Глобальная переменная для хранения синглтон-экземпляра
_ai_client_instance = None


def get_ai_client():
    """
    Возвращает синглтон-экземпляр AIClient.
    Создает экземпляр при первом вызове.
    """
    global _ai_client_instance
    if _ai_client_instance is None:
        _ai_client_instance = AIClient()
    return _ai_client_instance

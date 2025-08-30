from .providers.openai import OpenAIProvider
from . import prompts

# Здесь можно легко переключить провайдера, изменив одну строку
# from .providers.another_provider import AnotherProvider as AIProvider
AIProvider = OpenAIProvider


class AIClient:
    """
    Абстрактный клиент для работы с нейросетью.
    Использует выбранного провайдера для выполнения запросов.
    """

    def __init__(self):
        self.provider = AIProvider()

    def verify_resume(self, resume_text: str) -> bool:
        """Проверяет, является ли текст резюме."""
        return self.provider.verify_text(resume_text, prompts.VERIFY_RESUME_PROMPT)

    def verify_vacancy(self, vacancy_text: str) -> bool:
        """Проверяет, является ли текст вакансией."""
        return self.provider.verify_text(vacancy_text, prompts.VERIFY_VACANCY_PROMPT)

    def analyze_match(self, resume_text: str, vacancy_text: str) -> str:
        """Анализирует соответствие резюме и вакансии."""
        return self.provider.analyze(
            prompts.ANALYZE_MATCH_PROMPT,
            resume_text=resume_text,
            vacancy_text=vacancy_text,
        )

    def generate_cover_letter(self, resume_text: str, vacancy_text: str) -> str:
        """Генерирует сопроводительное письмо."""
        return self.provider.analyze(
            prompts.GENERATE_COVER_LETTER_PROMPT,
            resume_text=resume_text,
            vacancy_text=vacancy_text,
        )

    def generate_hr_call_plan(self, resume_text: str, vacancy_text: str) -> str:
        """Генерирует план для созвона с HR."""
        return self.provider.analyze(
            prompts.GENERATE_HR_CALL_PLAN_PROMPT,
            resume_text=resume_text,
            vacancy_text=vacancy_text,
        )

    def generate_tech_interview_plan(self, resume_text: str, vacancy_text: str) -> str:
        """Генерирует план для технического интервью."""
        return self.provider.analyze(
            prompts.GENERATE_TECH_INTERVIEW_PLAN_PROMPT,
            resume_text=resume_text,
            vacancy_text=vacancy_text,
        )


# Создаем единственный экземпляр клиента, который будет использоваться во всем приложении
ai_client = AIClient()

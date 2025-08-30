# bot/messages.py

WELCOME_MESSAGE = """
👋 Привет! Я ваш личный ассистент для поиска работы.

С моей помощью вы можете:
- Проанализировать соответствие вашего резюме и вакансии.
- Сгенерировать сопроводительное письмо.
- Подготовиться к собеседованиям.

Для начала, давайте загрузим ваше резюме.
"""

# Resume messages
ASK_FOR_RESUME = "Загрузите ваше резюме в формате .txt или отправьте ссылку на hh.ru."
RESUME_UPLOADED_SUCCESS = "✅ Ваше резюме успешно загружено и сохранено."
RESUME_INVALID_FORMAT = "❌ Пожалуйста, отправьте файл в формате .txt или корректную ссылку на hh.ru."
RESUME_VERIFICATION_FAILED = "❌ Текст не похож на резюме. Пожалуйста, попробуйте еще раз."
RESUME_PROCESSING = "⏳ Обрабатываю ваше резюме..."

# Vacancy messages
ASK_FOR_VACANCY = "Теперь загрузите вакансию, которая вас интересует (текстовым файлом .txt или ссылкой на hh.ru)."
VACANCY_UPLOADED_SUCCESS = "✅ Вакансия успешно добавлена."
VACANCY_INVALID_FORMAT = "❌ Пожалуйста, отправьте файл в формате .txt или корректную ссылку на hh.ru."
VACANCY_VERIFICATION_FAILED = "❌ Текст не похож на вакансию. Пожалуйста, попробуйте еще раз."
VACANCY_PROCESSING = "⏳ Обрабатываю вакансию..."

# Main menu
MAIN_MENU_MESSAGE = "У вас есть резюме «{resume_title}» и {vacancy_count} вакансий. Выберите действие:"
MAIN_MENU_NO_VACANCIES = "У вас есть резюме «{resume_title}», но нет сохраненных вакансий. Загрузите первую."

# Analysis messages
ANALYSIS_COMPLETE = "🔍 Анализ завершен:"
COVER_LETTER_COMPLETE = "📝 Сопроводительное письмо готово:"
HR_CALL_PLAN_COMPLETE = "📞 План для созвона с HR готов:"
TECH_INTERVIEW_PLAN_COMPLETE = "💻 План для технического интервью готов:"
CHOOSE_VACANCY_FOR_ACTION = "Выберите вакансию для действия:"

# General
ERROR_MESSAGE = "Что-то пошло не так. Попробуйте еще раз."
ACTION_CANCELED = "Действие отменено."
NOT_IMPLEMENTED = "Этот функционал еще в разработке."

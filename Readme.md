# Python Project

## Установка и запуск venv

1. Создать виртуальное окружение:
   python -m venv venv

2. Активировать виртуальное окружение Windows:
   .\venv\Scripts\activate

3. Установить зависимости:
   pip install -r requirements.txt

4. Запуск проекта:
   python main.py

5. Зафиксировать зависимости:
   pip freeze > requirements.txt



## Работа с Git

1. Инициализация:
   git init

2. Добавить и закоммитить изменения:
   git add .
   git commit -m "Комментарий к изменению"

3. Скопировать репо к себе
   git clone https://github.com/Maratinhos/job-search-assistant.git

4. Обновить репо у себя
   git pull

5. Отправить изменения в репо
   git push

## Работа с миграциями alembic

1. alembic upgrade head
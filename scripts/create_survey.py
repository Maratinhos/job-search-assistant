import argparse
import os
import sys

# Добавляем корневую директорию проекта в sys.path
# python .\scripts\create_survey.py -q "Какую фичу вы бы хотели в следующем обновлении?" -o "Новые тарифы (дешевле)" "Новые тарифы (новейшие нейросети)" "Тестирование (с проверкой при помощи ИИ)" "Другое"
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from db import crud
from db.database import get_db

def main():
    """
    Создает новый опрос в базе данных.
    Все предыдущие опросы помечаются как неактивные.
    """
    parser = argparse.ArgumentParser(description="Создать новый опрос.")
    parser.add_argument("-q", "--question", required=True, help="Текст вопроса для опроса.")
    parser.add_argument("-o", "--options", required=True, nargs='+', help="Варианты ответов (через пробел).")

    args = parser.parse_args()

    db_gen = get_db()
    db = next(db_gen)

    try:
        survey = crud.create_survey(db, question=args.question, options=args.options)
        print(f"Опрос успешно создан с ID: {survey.id}")
        print(f"  Вопрос: {survey.question}")
        print(f"  Варианты: {survey.options}")
        print(f"  Активен: {survey.is_active}")
    finally:
        db.close()

if __name__ == "__main__":
    main()

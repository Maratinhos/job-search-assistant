import sqlite3
import os

DB_FILENAME = "bot_database.sqlite"
NEW_REVISION = "4e1d175ddc79"

def fix_alembic_version():
    if not os.path.exists(DB_FILENAME):
        print(f"Ошибка: Файл базы данных '{DB_FILENAME}' не найден.")
        return

    try:
        conn = sqlite3.connect(DB_FILENAME)
        cursor = conn.cursor()

        # Принудительно устанавливаем нужную версию, удаляя старую
        cursor.execute("DELETE FROM alembic_version")
        cursor.execute("INSERT INTO alembic_version (version_num) VALUES (?)", (NEW_REVISION,))
        
        conn.commit()
        
        # Проверка
        cursor.execute("SELECT version_num FROM alembic_version")
        result = cursor.fetchone()
        conn.close()

        if result and result[0] == NEW_REVISION:
            print(f"Успешно! Версия миграции в БД обновлена на '{NEW_REVISION}'.")
            print("\nТеперь попробуйте снова сгенерировать миграцию:")
            print("alembic revision --autogenerate -m \"Add analysis results and update logs\"")
        else:
            print("Не удалось обновить версию миграции.")

    except sqlite3.Error as e:
        print(f"Произошла ошибка SQLite: {e}")
        print("Это может означать, что таблицы 'alembic_version' не существует, или БД не инициализирована.")

if __name__ == "__main__":
    fix_alembic_version()
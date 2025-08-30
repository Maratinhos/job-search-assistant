from db import crud, models

def test_get_or_create_user(db_session):
    """Тестирует получение или создание пользователя."""
    # 1. Создание нового пользователя
    chat_id = 12345
    user = crud.get_or_create_user(db_session, chat_id=chat_id)
    assert user is not None
    assert user.chat_id == chat_id
    assert user.id is not None

    # 2. Получение существующего пользователя
    user2 = crud.get_or_create_user(db_session, chat_id=chat_id)
    assert user2.id == user.id

def test_create_resume(db_session):
    """Тестирует создание и обновление (замену) резюме."""
    user = crud.get_or_create_user(db_session, chat_id=123)

    # 1. Создание первого резюме
    resume1 = crud.create_resume(db_session, user_id=user.id, file_path="/path/to/resume1.txt", source="file1.txt")
    assert resume1.file_path == "/path/to/resume1.txt"

    retrieved_resume = crud.get_user_resume(db_session, user_id=user.id)
    assert retrieved_resume is not None
    assert retrieved_resume.id == resume1.id

    # 2. Создание второго резюме (должно заменить первое)
    resume2 = crud.create_resume(db_session, user_id=user.id, file_path="/path/to/resume2.txt", source="file2.txt")
    assert resume2.file_path == "/path/to/resume2.txt"

    retrieved_resume_after_update = crud.get_user_resume(db_session, user_id=user.id)
    assert retrieved_resume_after_update is not None
    assert retrieved_resume_after_update.id == resume2.id
    # Эта проверка некорректна для in-memory SQLite, который может переиспользовать ID.
    # Главное, что контент обновился, что мы уже проверили через resume2.file_path.
    # assert retrieved_resume_after_update.id != resume1.id

    # Проверяем, что в БД осталась только одна запись резюме для этого пользователя
    all_resumes = db_session.query(models.Resume).filter_by(user_id=user.id).all()
    assert len(all_resumes) == 1

def test_create_and_get_vacancies(db_session):
    """Тестирует создание и получение вакансий."""
    user1 = crud.get_or_create_user(db_session, chat_id=123)
    user2 = crud.get_or_create_user(db_session, chat_id=456) # Другой пользователь

    # 1. Создаем несколько вакансий для user1
    crud.create_vacancy(db_session, user_id=user1.id, name="Vacancy 1", file_path="/path/to/v1.txt", source="s1")
    crud.create_vacancy(db_session, user_id=user1.id, name="Vacancy 2", file_path="/path/to/v2.txt", source="s2")
    # И одну для user2
    crud.create_vacancy(db_session, user_id=user2.id, name="Vacancy 3", file_path="/path/to/v3.txt", source="s3")

    # 2. Получаем все вакансии для user1
    vacancies_user1 = crud.get_user_vacancies(db_session, user_id=user1.id)
    assert len(vacancies_user1) == 2
    assert vacancies_user1[0].name == "Vacancy 2"  # Проверяем сортировку (последняя добавленная - первая в списке)
    assert vacancies_user1[1].name == "Vacancy 1"

    # 3. Получаем вакансии для user2
    vacancies_user2 = crud.get_user_vacancies(db_session, user_id=user2.id)
    assert len(vacancies_user2) == 1
    assert vacancies_user2[0].name == "Vacancy 3"

    # 4. Получаем вакансию по ID
    vacancy_to_get = vacancies_user1[0]
    retrieved_vacancy = crud.get_vacancy_by_id(db_session, vacancy_id=vacancy_to_get.id)
    assert retrieved_vacancy is not None
    assert retrieved_vacancy.id == vacancy_to_get.id
    assert retrieved_vacancy.name == "Vacancy 2"

def test_get_user_resume_no_resume(db_session):
    """Тестирует получение резюме для пользователя, у которого его нет."""
    user = crud.get_or_create_user(db_session, chat_id=999)
    resume = crud.get_user_resume(db_session, user_id=user.id)
    assert resume is None

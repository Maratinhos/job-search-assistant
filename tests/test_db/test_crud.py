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
    resume1 = crud.create_resume(db_session, user_id=user.id, file_path="/path/to/resume1.txt", source="file1.txt", title="Resume 1")
    assert resume1.file_path == "/path/to/resume1.txt"
    assert resume1.title == "Resume 1"

    retrieved_resume = crud.get_user_resume(db_session, user_id=user.id)
    assert retrieved_resume is not None
    assert retrieved_resume.id == resume1.id
    assert retrieved_resume.title == "Resume 1"

    # 2. Создание второго резюме (должно заменить первое)
    resume2 = crud.create_resume(db_session, user_id=user.id, file_path="/path/to/resume2.txt", source="file2.txt", title="Resume 2")
    assert resume2.file_path == "/path/to/resume2.txt"
    assert resume2.title == "Resume 2"

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
    crud.create_vacancy(db_session, user_id=user1.id, title="Vacancy 1", file_path="/path/to/v1.txt", source="s1")
    crud.create_vacancy(db_session, user_id=user1.id, title="Vacancy 2", file_path="/path/to/v2.txt", source="s2")
    # И одну для user2
    crud.create_vacancy(db_session, user_id=user2.id, title="Vacancy 3", file_path="/path/to/v3.txt", source="s3")

    # 2. Получаем все вакансии для user1
    vacancies_user1 = crud.get_user_vacancies(db_session, user_id=user1.id)
    assert len(vacancies_user1) == 2
    assert vacancies_user1[0].title == "Vacancy 2"  # Проверяем сортировку (последняя добавленная - первая в списке)
    assert vacancies_user1[1].title == "Vacancy 1"

    # 3. Получаем вакансии для user2
    vacancies_user2 = crud.get_user_vacancies(db_session, user_id=user2.id)
    assert len(vacancies_user2) == 1
    assert vacancies_user2[0].title == "Vacancy 3"

    # 4. Получаем вакансию по ID
    vacancy_to_get = vacancies_user1[0]
    retrieved_vacancy = crud.get_vacancy_by_id(db_session, vacancy_id=vacancy_to_get.id)
    assert retrieved_vacancy is not None
    assert retrieved_vacancy.id == vacancy_to_get.id
    assert retrieved_vacancy.title == "Vacancy 2"

def test_get_user_resume_no_resume(db_session):
    """Тестирует получение резюме для пользователя, у которого его нет."""
    user = crud.get_or_create_user(db_session, chat_id=999)
    resume = crud.get_user_resume(db_session, user_id=user.id)
    assert resume is None


def test_create_ai_usage_log_with_relations(db_session):
    """Тестирует создание лога использования AI с привязкой к резюме и вакансии."""
    user = crud.get_or_create_user(db_session, chat_id=789)
    resume = crud.create_resume(db_session, user_id=user.id, file_path="r.txt", source="s", title="T")
    vacancy = crud.create_vacancy(db_session, user_id=user.id, title="V", file_path="v.txt", source="s")

    log = crud.create_ai_usage_log(
        db=db_session,
        user_id=user.id,
        prompt_tokens=10,
        completion_tokens=20,
        total_tokens=30,
        cost=0.01,
        action="test_action",
        resume_id=resume.id,
        vacancy_id=vacancy.id,
    )

    assert log.id is not None
    assert log.user_id == user.id
    assert log.resume_id == resume.id
    assert log.vacancy_id == vacancy.id
    assert log.action == "test_action"
    assert log.total_tokens == 30


def test_create_analysis_result(db_session):
    """Тестирует создание и обновление записи о результате анализа."""
    user = crud.get_or_create_user(db_session, chat_id=101)
    resume = crud.create_resume(db_session, user_id=user.id, file_path="r.txt", source="s", title="T")
    vacancy = crud.create_vacancy(db_session, user_id=user.id, title="V", file_path="v.txt", source="s")

    # 1. Создание новой записи
    analysis_data_1 = {
        "match_analysis": "Match analysis text.",
        "cover_letter": "Cover letter text.",
    }
    analysis1 = crud.create_analysis_result(
        db_session,
        resume_id=resume.id,
        vacancy_id=vacancy.id,
        analysis_data=analysis_data_1,
    )

    assert analysis1.id is not None
    assert analysis1.resume_id == resume.id
    assert analysis1.vacancy_id == vacancy.id
    assert analysis1.match_analysis == "Match analysis text."
    assert analysis1.cover_letter == "Cover letter text."
    assert analysis1.hr_call_plan is None # Поле не было передано

    # 2. Обновление существующей записи
    analysis_data_2 = {
        "cover_letter": "Updated cover letter text.",
        "hr_call_plan": "HR call plan text.",
    }
    analysis2 = crud.create_analysis_result(
        db_session,
        resume_id=resume.id,
        vacancy_id=vacancy.id,
        analysis_data=analysis_data_2,
    )

    assert analysis2.id == analysis1.id  # Убедимся, что это та же самая запись
    assert analysis2.match_analysis == "Match analysis text." # Старое значение сохранилось
    assert analysis2.cover_letter == "Updated cover letter text." # Значение обновилось
    assert analysis2.hr_call_plan == "HR call plan text." # Новое значение добавилось

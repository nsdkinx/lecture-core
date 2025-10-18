import datetime
from pathlib import Path
from lecture_repository import LectureRepository, LectureType
from add_new_subject import create_subject

def main():
    lecture_repo_path = Path('.')

    create_subject(
        subject_name='Основы философии',
        subject_id='философия'
    )

    print(f"1. Инициализация репозитория в '{lecture_repo_path.resolve()}'")
    repo = LectureRepository(lecture_repo_path)

    print(f"   Найдено предметов: {len(repo.subjects)}")

    print("\n2. Создание нового объекта лекции...")
    try:
        new_lecture = repo.create_new_lecture(
            subject_id='философия',
            lecture_type=LectureType.PRACTICE,
            topic="Понятие философии, её смысл и предназначение",
            classroom='404',
            date=datetime.date(2025, 9, 1)
        )
        print(f"   Создана лекция: {new_lecture}")

        # 3. Добавление контента и сохранение
        print("\n3. Добавление контента и вызов .save()")
        new_lecture.content += "\n**Философия** — особая форма познания мира."
        new_lecture.save()

    except (FileNotFoundError, ValueError) as e:
        print(f"   Ошибка: {e}")

    print("\n4. Получение списка всех лекций...")
    all_my_lectures = repo.get_all_lectures()
    print(f"   Всего найдено лекций: {len(all_my_lectures)}")
    for lect in all_my_lectures:
        print(f"   - {lect.uid}: {lect.topic} ({lect.path.relative_to(lecture_repo_path)})")

    print("\n5. Редактирование лекции 'философия-пр-1'")
    target_lecture = repo.get_lecture_by_uid('философия-пр-1')
    if target_lecture:
        print(f"   Найдена лекция: {target_lecture.topic}")
        target_lecture.classroom = '501 (дистант)'
        target_lecture.topic = "Новая тема для старой лекции"
        print("   Аудитория и тема изменены. Сохранение...")
        target_lecture.save()
    else:
        print("   Лекция с UID 'философия-пр-1' не найдена.")

    print("\n6. Повторное получение всех лекций для проверки изменений...")
    all_my_lectures_after_edit = repo.get_all_lectures()
    for lect in all_my_lectures_after_edit:
        print(f"   - {lect.uid}: {lect.topic} (Аудитория: {lect.classroom})")


if __name__ == "__main__":
    main()

#!/usr/bin/python3
import argparse
import json
from pathlib import Path
import sys

repo_path = Path(__file__).parent.resolve()
subjects_file_path = repo_path / "subjects.json"

def create_subject(subject_name: str, subject_id: str):
    if subjects_file_path.exists():
        try:
            subjects_data = json.loads(
                subjects_file_path.read_text('utf-8')
            )
        except json.JSONDecodeError:
            print(f"Ошибка: Файл '{subjects_file_path}' поврежден или пуст. Инициализация нового хранилища.")
            subjects_data = {}
    else:
        print(f"Файл '{subjects_file_path.name}' не найден. Создание нового файла.")
        subjects_data = {}

    if subject_id in subjects_data:
        print(f"Ошибка: Предмет с ID '{subject_id}' уже существует. Прерывание операции.")
        sys.exit(1)

    if subject_name in subjects_data.values():
        print(f"Ошибка: Предмет с названием '{subject_name}' уже существует. Прерывание операции.")
        sys.exit(1)

    subjects_data[subject_id] = subject_name

    try:
        subjects_file_path.write_text(
            data=json.dumps(subjects_data, ensure_ascii=False, indent=4),
            encoding='utf-8'
        )
        print(f"Успешно: Предмет '{subject_name}' (ID: {subject_id}) добавлен в '{subjects_file_path.name}'.")
    except IOError as e:
        print(f"Ошибка записи в файл '{subjects_file_path}': {e}")
        sys.exit(1)

    subject_dir_path = repo_path / subject_name
    try:
        subject_dir_path.mkdir(exist_ok=True)
        print(f"Успешно: Создана директория для предмета: '{subject_dir_path.name}/'")
    except OSError as e:
        print(f"Ошибка создания директории '{subject_dir_path}': {e}")
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(
        description="Создает новый учебный предмет."
    )
    parser.add_argument(
        '--name',
        type=str,
        required=True,
        help='Полное, официальное название предмета (например, "Основы философии").'
    )
    parser.add_argument(
        '--id',
        type=str,
        required=True,
        help='Короткий, уникальный ID предмета в нижнем регистре (например, "философия").'
    )

    args = parser.parse_args()

    if not args.id.islower() or ' ' in args.id:
        print(f"Предупреждение: ID '{args.id}' должен быть в нижнем регистре и не содержать пробелов.")

    create_subject(subject_name=args.name, subject_id=args.id)


if __name__ == "__main__":
    main()

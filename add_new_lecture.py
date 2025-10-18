#!/usr/bin/python3
# -*- coding: utf-8 -*-
"""
Скрипт для создания новой лекции с использованием модуля lecture_repository.
"""
import argparse
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path

# Импортируем необходимые классы из модуля управления репозиторием
from lecture_repository import LectureRepository, LectureType


def open_file_in_editor(filepath: Path):
    """
    Открывает указанный файл в редакторе по умолчанию в зависимости от ОС.
    """
    filepath_str = str(filepath)
    try:
        if sys.platform == "win32":
            os.startfile(filepath_str)
        elif sys.platform == "darwin":  # macOS
            subprocess.run(["open", filepath_str], check=True)
        else:  # Linux и другие Unix-like
            # Пытаемся использовать xdg-open или переменную окружения $EDITOR
            try:
                subprocess.run(["xdg-open", filepath_str], check=True, stderr=subprocess.DEVNULL)
            except (subprocess.CalledProcessError, FileNotFoundError):
                editor = os.environ.get('EDITOR')
                if editor:
                    subprocess.run([editor, filepath_str], check=True)
                else:
                    print(f"\nНе удалось определить редактор (переменная $EDITOR не установлена).")
                    print(f"Пожалуйста, откройте файл вручную: {filepath_str}")
    except Exception as e:
        print(f"\nНе удалось автоматически открыть файл: {e}")
        print(f"Пожалуйста, откройте его вручную: {filepath_str}")


def main():
    """
    Обрабатывает аргументы командной строки и создает новую лекцию через LectureRepository.
    """
    parser = argparse.ArgumentParser(
        description="Создать новую запись о лекции, используя LectureRepository.",
        epilog='Пример: python3 add_new_lecture_refactored.py -s обп -t пр -r 312 -i 4 "Система 5S и визуализация"'
    )

    parser.add_argument('-s', '--subject-id', type=str, required=True, help='Короткий ID предмета (например, "обп").')
    parser.add_argument('-t', '--lecture-type', type=str, required=True, choices=['л', 'пр'], help='Тип занятия ("л" - лекция, "пр" - практика).')
    parser.add_argument('-r', '--classroom', type=str, required=True, help='Номер или название аудитории.')
    parser.add_argument('-i', '--absolute-lecture-id', type=int, required=True, help='Номер пары по расписанию звонков.')
    parser.add_argument('--relative-lecture-id', type=int, help='Порядковый номер пары за день. По умолчанию равен absolute-lecture-id.')
    parser.add_argument('-d', '--date', type=str, help='Дата занятия в формате ГГГГ-ММ-ДД. По умолчанию - сегодня.')
    parser.add_argument('-o', '--open', action='store_true', help='Открыть созданный файл в редакторе по умолчанию.')
    parser.add_argument('--repo-path', type=str, default='.', help='Путь к корневой папке репозитория.')

    # Позиционный аргумент для названия темы
    parser.add_argument('topic', nargs='?', type=str, default=None, help='Полное название темы. Если не указано, будет запрошено интерактивно.')

    args = parser.parse_args()

    # Если relative_lecture_id не указан, он принимает значение absolute_lecture_id
    relative_lecture_id = args.relative_lecture_id if args.relative_lecture_id is not None else args.absolute_lecture_id

    lecture_topic = args.topic
    # Если название не было передано как аргумент, запрашиваем его
    if not lecture_topic:
        try:
            lecture_topic = input("Введите название лекции/практики: ")
            if not lecture_topic.strip():
                print("Название не может быть пустым.", file=sys.stderr)
                sys.exit(1)
        except KeyboardInterrupt:
            print("\nОперация отменена.", file=sys.stderr)
            sys.exit(0)

    # Определяем дату
    lecture_date = None
    if args.date:
        try:
            lecture_date = datetime.strptime(args.date, '%Y-%m-%d').date()
        except ValueError:
            print(f"Ошибка: неверный формат даты '{args.date}'. Используйте ГГГГ-ММ-ДД.", file=sys.stderr)
            sys.exit(1)

    try:
        # 1. Инициализация репозитория
        repo_root = Path(args.repo_path)
        repo = LectureRepository(repo_root)

        # 2. Создание нового объекта лекции в памяти
        # Порядковый номер (class_id) будет вычислен автоматически
        new_lecture = repo.create_new_lecture(
            subject_id=args.subject_id,
            lecture_type=LectureType(args.lecture_type),
            topic=lecture_topic,
            classroom=args.classroom,
            date=lecture_date,  # Может быть None, тогда используется дата по умолчанию
            absolute_lecture_id=args.absolute_lecture_id,
            relative_lecture_id=relative_lecture_id
        )

        # 3. Сохранение лекции в файл.
        # Метод .save() сам создаст нужные папки и файлы.
        new_lecture.save()

        # 4. Если указан флаг --open, открываем созданный файл
        if args.open:
            open_file_in_editor(new_lecture.path)

    except (FileNotFoundError, ValueError) as e:
        print(f"Ошибка выполнения: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Произошла непредвиденная ошибка: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    # Для корректной работы этого скрипта, файл lecture_repository.py
    # должен находиться в той же директории или быть доступным в PYTHONPATH.
    main()

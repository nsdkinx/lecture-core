#!/usr/bin/python3
import argparse
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path

from lecture_repository import LectureRepository, LectureType


def _open_file_in_editor(file: Path):
    file = str(file.resolve())
    try:
        if sys.platform == "win32":
            os.startfile(file)
        elif sys.platform == "darwin":
            subprocess.run(["open", file], check=True)
        else:
            try:
                subprocess.run(["xdg-open", file], check=True, stderr=subprocess.DEVNULL)
            except (subprocess.CalledProcessError, FileNotFoundError):
                editor = os.environ.get('EDITOR')
                if editor:
                    subprocess.run([editor, file], check=True)
                else:
                    print(f"\nНе удалось определить редактор (переменная $EDITOR не установлена).")
                    print(f"Пожалуйста, откройте файл вручную: {file}")
    except Exception as e:
        print(f"\nНе удалось автоматически открыть файл: {e}")
        print(f"Пожалуйста, откройте его вручную: {file}")


def main():
    parser = argparse.ArgumentParser(
        description="Создание новой лекции",
        epilog='Пример: python3 add_new_lecture.py -s обп -t пр -r 312 -i 4 "Система 5S и визуализация"'
    )

    parser.add_argument('-s', '--subject-id', type=str, required=True, help='Короткий ID предмета (например, "обп").')
    parser.add_argument('-t', '--lecture-type', type=str, required=True, choices=['л', 'пр'], help='Тип занятия ("л" - лекция, "пр" - практика).')
    parser.add_argument('-r', '--classroom', type=str, required=True, help='Номер или название аудитории.')
    parser.add_argument('-i', '--absolute-lecture-id', type=int, required=True, help='Номер пары по расписанию звонков.')
    parser.add_argument('--relative-lecture-id', type=int, help='Порядковый номер пары за день. По умолчанию равен absolute-lecture-id.')
    parser.add_argument('-d', '--date', type=str, help='Дата занятия в формате ГГГГ-ММ-ДД. По умолчанию - сегодня.')
    parser.add_argument('-o', '--open', action='store_true', help='Открыть созданный файл в редакторе по умолчанию.')
    parser.add_argument('--repo-path', type=str, default='.', help='Путь к корневой папке репозитория.')

    parser.add_argument('topic', nargs='?', type=str, default=None, help='Полное название темы. Если не указано, будет запрошено интерактивно.')

    args = parser.parse_args()

    # Если relative_lecture_id не указан, он принимает значение absolute_lecture_id
    relative_lecture_id = args.relative_lecture_id if args.relative_lecture_id is not None else args.absolute_lecture_id

    lecture_topic = args.topic
    if not lecture_topic:
        try:
            lecture_topic = input("Введите название лекции/практики: ")
            if not lecture_topic.strip():
                print("Название не может быть пустым.", file=sys.stderr)
                sys.exit(1)
        except KeyboardInterrupt:
            print("\nОперация отменена.", file=sys.stderr)
            sys.exit(0)

    lecture_date = None
    if args.date:
        try:
            lecture_date = datetime.strptime(args.date, '%Y-%m-%d').date()
        except ValueError:
            print(f"Ошибка: неверный формат даты '{args.date}'. Используйте ГГГГ-ММ-ДД.", file=sys.stderr)
            sys.exit(1)

    try:
        repo_root = Path(args.repo_path)
        repo = LectureRepository(repo_root)

        new_lecture = repo.create_new_lecture(
            subject_id=args.subject_id,
            lecture_type=LectureType(args.lecture_type),
            topic=lecture_topic,
            classroom=args.classroom,
            date=lecture_date,  # Может быть None, тогда используется дата по умолчанию
            absolute_lecture_id=args.absolute_lecture_id,
            relative_lecture_id=relative_lecture_id
        )

        new_lecture.save()

        if args.open:
            _open_file_in_editor(new_lecture.path)

    except (FileNotFoundError, ValueError) as e:
        print(f"Ошибка хранилища: {e}", file=sys.stderr)
        sys.exit(1)

    except Exception as e:
        print(f"Произошла непредвиденная ошибка: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()

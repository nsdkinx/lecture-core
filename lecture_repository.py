# -*- coding: utf-8 -*-
"""
Этот модуль предоставляет инструментарий для управления хранилищем учебных конспектов,
основанным на файловой структуре Markdown-файлов с YAML-метаданными.

Основные возможности:
- Класс `LectureRepository` для управления всем хранилищем.
- Модель данных `Lecture` для представления конспекта.
- Сериализация и десериализация лекций из/в .md файлы.
- Методы для поиска, создания и сохранения лекций в репозитории.
- Валидация типов данных и структуры.
"""
from __future__ import annotations

import datetime
import json
import re
import shutil
from dataclasses import dataclass, field, asdict
from enum import StrEnum
from pathlib import Path
from typing import List, Dict, Optional

import yaml


class LectureType(StrEnum):
    """Тип занятия (лекция или практика)."""
    LECTURE = 'л'
    PRACTICE = 'пр'


# --- Модель данных ---

@dataclass
class Lecture:
    """
    Представление одной лекции (или практического занятия) в репозитории.
    Этот объект должен создаваться через экземпляр `LectureRepository`.
    """
    # Связь с репозиторием
    repository: 'LectureRepository' = field(repr=False)

    # Метаданные из YAML Front Matter
    subject_name: str
    subject_id: str
    date: datetime.date
    type: LectureType
    class_id: int
    absolute_lecture_id: int
    relative_lecture_id: int
    classroom: str

    # Содержимое и файловая информация
    content: str = field(repr=False)
    path: Path = field(repr=False)
    topic: str = field(init=False)
    uid: str = field(init=False) # Уникальный идентификатор: subject_id-type-class_id

    def __post_init__(self):
        """
        Вычисляет производные поля после инициализации объекта.
        """
        self.uid = f"{self.subject_id}-{self.type.value}-{self.class_id}"
        self.topic = self._extract_topic_from_path()

    def _extract_topic_from_path(self) -> str:
        """Извлекает и очищает название темы из имени файла/папки."""
        name_part = self.path.stem
        match = re.search(r'\d{4}-\d{2}-\d{2}\.[лпр]{1,2}-\d+\.(.*)', name_part)
        if match:
            return match.group(1).replace('_', ' ')
        return "Без темы"

    @staticmethod
    def _sanitize_topic(topic: str) -> str:
        """Очищает название темы для использования в имени файла."""
        s = topic.replace(' ', '_').replace('.', '_')
        s = re.sub(r'[^\w\-_]', '', s)
        return re.sub(r'__+', '_', s)

    @property
    def expected_filename(self) -> str:
        """Генерирует ожидаемое имя файла на основе текущих атрибутов."""
        date_str = self.date.strftime('%Y-%m-%d')
        sanitized_topic = self._sanitize_topic(self.topic)
        return f"{date_str}.{self.type.value}-{self.class_id}.{sanitized_topic}"

    @classmethod
    def from_file(cls, file_path: Path, repository: 'LectureRepository') -> 'Lecture':
        """
        Десериализует (загружает) лекцию из markdown-файла.
        """
        if not file_path.exists():
            raise FileNotFoundError(f"Файл конспекта не найден: {file_path}")

        with open(file_path, 'r', encoding='utf-8') as f:
            content_parts = f.read().split('---', 2)

            if len(content_parts) < 3:
                raise ValueError(f"Некорректный формат файла: отсутствует YAML Front Matter в {file_path}")

            metadata_raw = content_parts[1]
            content = content_parts[2].strip()

            try:
                metadata = yaml.safe_load(metadata_raw)
                metadata['date'] = datetime.datetime.strptime(metadata['date'], '%Y-%m-%d').date()
                metadata['type'] = LectureType(metadata['type'])
            except (yaml.YAMLError, KeyError, ValueError) as e:
                raise ValueError(f"Ошибка парсинга метаданных в файле {file_path}: {e}")

        return cls(
            repository=repository,
            path=file_path,
            content=content,
            **metadata
        )

    def save(self):
        """
        Сохраняет лекцию в файл. Обновляет имя файла и папки, если
        ключевые атрибуты (дата, id, тема) были изменены.
        """
        metadata_dict = asdict(self)
        for key in ['repository', 'content', 'path', 'topic', 'uid']:
            metadata_dict.pop(key, None)

        metadata_dict['date'] = self.date.strftime('%Y-%m-%d')
        metadata_dict['type'] = self.type.value

        try:
            yaml_front_matter = yaml.dump(metadata_dict, allow_unicode=True, sort_keys=False)
        except yaml.YAMLError as e:
            raise IOError(f"Ошибка при формировании YAML для {self.uid}: {e}")

        full_content = f"---\n{yaml_front_matter}---\n\n{self.content}"

        new_filename_base = self.expected_filename
        new_folder_path = self.repository.root_path / self.subject_name / new_filename_base
        new_file_path = new_folder_path / f"{new_filename_base}.md"

        original_folder_path = self.path.parent

        if new_file_path != self.path:
            new_folder_path.mkdir(parents=True, exist_ok=True)

            if original_folder_path.exists() and original_folder_path != new_folder_path:
                for item in original_folder_path.iterdir():
                    shutil.move(str(item), str(new_folder_path / item.name))
                try:
                    original_folder_path.rmdir()
                except OSError:
                    print(f"Предупреждение: не удалось удалить старую папку {original_folder_path}")

            self.path = new_file_path
            if (new_folder_path / original_folder_path.name).exists():
                 (new_folder_path / original_folder_path.name).rename(new_file_path)

        self.path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.path, 'w', encoding='utf-8') as f:
            f.write(full_content)

        print(f"Лекция '{self.uid}' успешно сохранена в {self.path}")


# --- Класс для управления репозиторием ---

class LectureRepository:
    """
    Класс для управления хранилищем лекций.
    Инициализируется путем к корневой папке репозитория.
    """
    def __init__(self, repo_root: Path):
        self.root_path = repo_root
        self.subjects_file = self.root_path / 'subjects.json'
        self.subjects = self._load_subjects()

    def _load_subjects(self) -> Dict[str, str]:
        """Загружает словарь предметов из `subjects.json`."""
        if not self.subjects_file.exists():
            raise FileNotFoundError(f"Файл 'subjects.json' не найден в {self.root_path}")
        with open(self.subjects_file, 'r', encoding='utf-8') as f:
            return json.load(f)

    def get_all_lectures(self) -> List[Lecture]:
        """Сканирует репозиторий и возвращает список всех найденных лекций."""
        lectures: List[Lecture] = []
        for subject_name in self.subjects.values():
            subject_path = self.root_path / subject_name
            if not subject_path.is_dir():
                continue

            for md_file in subject_path.glob('*/*.md'):
                try:
                    lectures.append(Lecture.from_file(md_file, repository=self))
                except (ValueError, FileNotFoundError) as e:
                    print(f"Ошибка при загрузке лекции из {md_file}: {e}")
        return lectures

    def get_lecture_by_uid(self, uid: str) -> Optional[Lecture]:
        """Находит лекцию по её уникальному идентификатору (uid)."""
        for lecture in self.get_all_lectures():
            if lecture.uid == uid:
                return lecture
        return None

    def create_new_lecture(
        self,
        subject_id: str,
        lecture_type: LectureType,
        topic: str,
        classroom: str,
        date: Optional[datetime.date] = None,
        absolute_lecture_id: int = 1,
        relative_lecture_id: int = 1
    ) -> Lecture:
        """
        Создает новый объект лекции в памяти (без сохранения в файл).
        """
        if subject_id not in self.subjects:
            raise ValueError(f"Предмет с ID '{subject_id}' не найден в subjects.json")
        subject_name = self.subjects[subject_id]

        all_lectures = self.get_all_lectures()
        max_id = 0
        for lect in all_lectures:
            if lect.subject_id == subject_id and lect.type == lecture_type:
                if lect.class_id > max_id:
                    max_id = lect.class_id
        new_class_id = max_id + 1

        if date is None:
            date = datetime.date.today()

        temp_filename_base = f"{date.strftime('%Y-%m-%d')}.{lecture_type.value}-{new_class_id}.{Lecture._sanitize_topic(topic)}"
        temp_path = self.root_path / subject_name / temp_filename_base / f"{temp_filename_base}.md"

        new_lecture = Lecture(
            repository=self,
            subject_name=subject_name,
            subject_id=subject_id,
            date=date,
            type=lecture_type,
            class_id=new_class_id,
            absolute_lecture_id=absolute_lecture_id,
            relative_lecture_id=relative_lecture_id,
            classroom=classroom,
            content=f"# {topic}\n\n",
            path=temp_path
        )
        new_lecture.topic = topic
        return new_lecture


if __name__ == '__main__':
    # --- Пример использования ---

    # 1. Инициализация репозитория
    lecture_repo_path = Path('./repo')
    lecture_repo_path.mkdir(exist_ok=True)

    subjects_data = {
        "философия": "Основы философии",
        "обп": "Основы бережливого производства"
    }
    with open(lecture_repo_path / 'subjects.json', 'w', encoding='utf-8') as f:
        json.dump(subjects_data, f, ensure_ascii=False, indent=4)

    print(f"1. Инициализация репозитория в '{lecture_repo_path.resolve()}'")
    repo = LectureRepository(lecture_repo_path)
    print(f"   Найдено предметов: {repo.subjects}")

    # 2. Создание новой лекции через репозиторий
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

    # 4. Получение всех лекций из хранилища
    print("\n4. Получение списка всех лекций...")
    all_my_lectures = repo.get_all_lectures()
    print(f"   Всего найдено лекций: {len(all_my_lectures)}")
    for lect in all_my_lectures:
        print(f"   - {lect.uid}: {lect.topic} ({lect.path.relative_to(lecture_repo_path)})")

    # 5. Получение лекции по UID и её редактирование
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

    # 6. Проверка результата после редактирования
    print("\n6. Повторное получение всех лекций для проверки изменений...")
    all_my_lectures_after_edit = repo.get_all_lectures()
    for lect in all_my_lectures_after_edit:
        print(f"   - {lect.uid}: {lect.topic} (Аудитория: {lect.classroom})")


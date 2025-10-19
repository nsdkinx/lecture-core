# -*- coding: utf-8 -*-
"""
This module provides an API for managing a LectureCore repository.

- LectureRepository class to manage the entire repository.
- Lecture model representing a single lecture note.
- Serialization and deserialization of lectures from/to .md files.
- Methods for finding, creating, and saving lectures.
- Validation of data types and structure.
"""
import datetime
import json
import re
import shutil
import os


def load_yaml(yaml_string):
    # type: (str) -> dict[str, str|int]
    data = {}
    lines = yaml_string.strip().split('\n')
    for line in lines:
        # Ensure there is a colon and it's not just a blank line
        if ':' in line:
            key, value = line.split(':', 1)
            key = key.strip()
            value = value.strip()

            # Remove quotes from string values
            if (value.startswith("'") and value.endswith("'")) or \
               (value.startswith('"') and value.endswith('"')):
                value = value[1:-1]
            else:
                # If a value is not quoted, try to convert it to an integer
                try:
                    value = int(value)
                except ValueError:
                    # If it fails, keep it as a string (e.g., for dates)
                    pass

            data[key] = value
    return data


def dump_yaml(data_dict):
    # type: (dict[str, str|int]) -> str
    lines = []
    for key, value in data_dict.items():
        # Format strings with single quotes for consistency
        if isinstance(value, str):
            # Escape single quotes within the string itself
            value = value.replace("'", "''")
            value_str = "'{}'".format(value)
        else:
            value_str = str(value)

        lines.append("{}: {}".format(key, value_str))
    # Join lines and add a trailing newline for clean formatting
    return '\n'.join(lines) + '\n'


class LectureType:
    """A simple Enum-like class for lecture types.
    Made to be compatible with older Python versions."""
    LECTURE = 'л'
    PRACTICE = 'пр'

    def __init__(self, value):
        if value not in [self.LECTURE, self.PRACTICE]:
            raise ValueError("Invalid lecture type: {}".format(value))
        self.value = value

    def __str__(self):
        return self.value

    def __eq__(self, other):
        if isinstance(other, LectureType):
            return self.value == other.value
        return self.value == other


class Lecture:
    """
    Represents a single lecture (or practice) in the repository.
    This object should be created through a LectureRepository instance.
    """
    def __init__(
            self,
            repository,  # type: LectureRepository
            subject_name,  # type: str
            subject_id,  # type: str
            date,  # type: datetime.date
            lecture_type,  # type: LectureType
            class_id,  # type: int
            absolute_lecture_id,  # type: int
            relative_lecture_id,  # type: int
            classroom,  # type: str
            content,  # type: str
            path  # type: str
    ):
        self.repository = repository
        self.subject_name = subject_name
        self.subject_id = subject_id
        self.date = date
        self.type = lecture_type
        self.class_id = class_id
        self.absolute_lecture_id = absolute_lecture_id
        self.relative_lecture_id = relative_lecture_id
        self.classroom = classroom
        self.content = content
        self.path = path

        # These are derived attributes, set after initialization.
        self.uid = "{}-{}-{}".format(self.subject_id, self.type.value, self.class_id)
        self.topic = self._extract_topic_from_path()

    def _extract_topic_from_path(self):
        """Extracts a human-readable topic from the file name."""
        # Get the base filename without the '.md' extension
        # e.g., "2005-10-19.л-1.Основы_философии"
        full_lecture_name, _ = os.path.splitext(
            os.path.basename(self.path)
        )

        parts = full_lecture_name.split('.', 2)

        # If the split gives us exactly 3 parts, the third one is the topic.
        if len(parts) == 3:
            topic_with_underscores = parts[2]
            return topic_with_underscores.replace('_', ' ')

        return "Без темы"

    @staticmethod
    def sanitize_topic(topic):
        # type: (str) -> str
        """Removes characters from topic that are invalid in file names."""
        s = topic.replace(' ', '_').replace('.', '_')
        s = re.sub(r'[^\w\-_]', '', s)
        return re.sub(r'__+', '_', s)

    @property
    def expected_filename(self):
        # type: () -> str
        """Generates the expected file name based on current attributes."""
        date_str = self.date.strftime('%Y-%m-%d')
        sanitized_topic = self.sanitize_topic(self.topic)
        return "{}.{}-{}.{}".format(
            date_str,
            self.type.value,
            self.class_id,
            sanitized_topic
        )

    @classmethod
    def from_file(cls, file_path, repository):
        # type: (str, LectureRepository) -> Lecture
        """Deserializes a lecture from a markdown file."""
        if not os.path.exists(file_path):
            raise FileNotFoundError(
                "Lecture note file not found: {}".format(file_path)
            )

        with open(file_path, 'r', encoding='utf-8') as f:
            file_content_parts = f.read().split('---', 2)

            if len(file_content_parts) < 3:
                raise ValueError(
                    "Invalid file format: missing YAML Front Matter in {}".format(file_path)
                )

            raw_yaml_metadata = file_content_parts[1]
            lecture_content = file_content_parts[2].strip()

            try:
                metadata = load_yaml(raw_yaml_metadata)
                # Serialize to datetime.date
                metadata['date'] = datetime.datetime.strptime(  # noqa
                    metadata['date'],
                    '%Y-%m-%d'
                ).date()
                metadata['type'] = LectureType(metadata['type'])  # noqa
                # Rename key to avoid conflict with built-in `type`
                metadata['lecture_type'] = metadata.pop('type')
            except (KeyError, ValueError) as e:
                raise ValueError("Error parsing metadata in file {}: {}".format(file_path, e))

        return cls(
            repository=repository,
            path=file_path,
            content=lecture_content,
            **metadata
        )

    def save(self):
        """
        Saves the lecture to a file. Updates the file and folder name
        if key attributes (date, id, topic) have been changed.
        """
        metadata_dict = {
            'subject_name': self.subject_name,
            'subject_id': self.subject_id,
            'date': self.date.strftime('%Y-%m-%d'),
            'type': self.type.value,
            'class_id': self.class_id,
            'absolute_lecture_id': self.absolute_lecture_id,
            'relative_lecture_id': self.relative_lecture_id,
            'classroom': self.classroom,
        }
        try:
            yaml_front_matter = dump_yaml(metadata_dict)
        except Exception as e:
            raise IOError(f"Error creating YAML for {self.uid}: {e}")

        full_content = f"---\n{yaml_front_matter}---\n\n{self.content}"

        new_filename_base = self.expected_filename
        new_folder_path = os.path.join(
            self.repository.repo_root,
            self.subject_name,
            new_filename_base
        )
        new_file_path = os.path.join(new_folder_path, f"{new_filename_base}.md")

        # Use a placeholder for the original path if it's a new file
        original_file_path = self.path or ""
        original_folder_path = os.path.dirname(original_file_path) if original_file_path else ""

        # 3. Handle file/folder moves before writing
        # Case 1: Path has changed.
        if (
                new_file_path != original_file_path
                and os.path.exists(original_folder_path)
        ):
            if new_folder_path != original_folder_path:
                # Case 1a: The entire folder needs to be renamed.
                # Abort if the destination folder already exists.
                if os.path.exists(new_folder_path):
                    raise IOError(f"Cannot move lecture: destination folder '{new_folder_path}' already exists.")

                print(f"Renaming lecture folder from '{original_folder_path}' to '{new_folder_path}'")
                shutil.move(original_folder_path, new_folder_path)

            elif os.path.exists(original_file_path):
                # Case 1b: Only the filename inside the folder needs to be renamed.
                # This check is needed if the old markdown file exists at the original_file_path.
                print(f"Renaming lecture file from '{original_file_path}' to '{new_file_path}'")
                os.rename(original_file_path, new_file_path)

        os.makedirs(new_folder_path, exist_ok=True)

        try:
            with open(new_file_path, 'w', encoding='utf-8') as f:
                f.write(full_content)

            self.path = new_file_path
            print(f"Lecture '{self.uid}' successfully saved to {self.path}")

        except IOError as e:
            print(f"Error: Failed to write file to {new_file_path}: {e}")

        return None


class _LectureFinder:
    """
    Scans the repository file structure to find lecture-related paths.
    This class is responsible for the "how" of finding files.
    """
    def __init__(self, repo_root, subjects_dict):
        # type: (str, dict) -> None
        self._repo_root = repo_root
        self._subjects = subjects_dict

    def find_all_files(self):
        """Yields the path to every valid .md file by chaining helpers."""
        for lecture_folder in self._get_lecture_folders():
            for file_name in os.listdir(lecture_folder):
                if file_name.endswith('.md'):
                    yield os.path.join(lecture_folder, file_name)

    def _get_lecture_folders(self):
        """Yields the path to every valid lecture folder."""
        for subject_path in self._get_subject_paths():
            for item_name in os.listdir(subject_path):
                item_path = os.path.join(subject_path, item_name)
                if os.path.isdir(item_path):
                    yield item_path

    def _get_subject_paths(self):
        """Yields the path to every valid subject directory."""
        for subject_name in self._subjects.values():
            subject_path = os.path.join(self._repo_root, subject_name)
            if os.path.isdir(subject_path):
                yield subject_path


class LectureRepository:
    def __init__(self, repo_root):
        self._repo_root = repo_root
        self._subjects_file = os.path.join(self._repo_root, 'subjects.json')
        self._subjects = self._load_subjects()
        self._finder = _LectureFinder(self._repo_root, self._subjects)

    @property
    def subjects(self):
        return self._subjects

    @property
    def repo_root(self):
        return self._repo_root

    def _load_subjects(self):
        if not os.path.exists(self._subjects_file):
            raise FileNotFoundError(
                "File 'subjects.json' not found in {}".format(self._repo_root)
            )
        with open(self. _subjects_file, 'r', encoding='utf-8') as f:
            return json.load(f)

    def get_all_lectures(self):
        # type: () -> list[Lecture]
        """Returns a list of all lectures found."""
        lectures = []
        for md_file_path in self._finder.find_all_files():
            try:
                lectures.append(
                    Lecture.from_file(md_file_path, repository=self)
                )
            except (ValueError, FileNotFoundError) as e:
                print(
                    "Error loading lecture from {}: {}".format(md_file_path, e)
                )
        return lectures

    def get_lecture_by_uid(self, uid):
        # type: (str) -> Lecture | None
        """Finds a lecture by its unique identifier (subject_id-type-class_id)."""
        for lecture in self.get_all_lectures():
            if lecture.uid == uid:
                return lecture
        return None

    def create_new_lecture(
            self,
            subject_id,  # type: str
            lecture_type,  # type: LectureType
            topic,  # type: str
            classroom,  # type: str
            date=None,  # type: datetime.date | None
            absolute_lecture_id=1,  # type: int
            relative_lecture_id=1  # type: int
    ):
        """
        Creates a new lecture object.
        """
        if subject_id not in self._subjects:
            raise ValueError(
                "Subject with ID '{}' not found in subjects.json".format(subject_id)
            )

        subject_name = self._subjects[subject_id]

        all_lectures = self.get_all_lectures()
        max_id = 0
        for lecture in all_lectures:
            if lecture.subject_id == subject_id and lecture.type == lecture_type:
                if lecture.class_id > max_id:
                    max_id = lecture.class_id
        new_class_id = max_id + 1

        if date is None:
            date = datetime.date.today()

        temp_filename_base = "{}.{}-{}.{}".format(
            date.strftime('%Y-%m-%d'),
            lecture_type.value,
            new_class_id,
            Lecture.sanitize_topic(topic)
        )

        # Use os.path.join for cross-platform path construction
        temp_path = os.path.join(
            self._repo_root,
            subject_name,
            temp_filename_base,
            "{}.md".format(temp_filename_base)
        )

        new_lecture = Lecture(
            repository=self,
            subject_name=subject_name,
            subject_id=subject_id,
            date=date,
            lecture_type=lecture_type,
            class_id=new_class_id,
            absolute_lecture_id=absolute_lecture_id,
            relative_lecture_id=relative_lecture_id,
            classroom=classroom,
            content="# {}\n\n".format(topic),
            path=temp_path  # noqa
        )
        new_lecture.topic = topic
        return new_lecture

#!/usr/bin/python3
# -*- coding: utf-8 -*-
"""
This script adds a new lecture or practical session to the repository.
It interacts with the LectureRepository to create the necessary files
and metadata.
"""
import argparse
import os
import subprocess
import sys
from datetime import datetime

from lecture_repository import LectureRepository, LectureType


def _open_file_in_editor(file_path):
    """
    Tries to open the specified file in the default editor for the OS.
    This is a cross-platform helper function.

    Args:
        file_path (str): A string path to the file.
    """
    abs_file_path = os.path.abspath(file_path)
    try:
        if sys.platform == "win32":
            os.startfile(abs_file_path)

        elif sys.platform == "darwin":  # macOS
            if subprocess.call(["open", abs_file_path]) != 0:
                raise OSError("The 'open' command failed to execute.")

        else:
            try:
                if subprocess.call(["xdg-open", abs_file_path]) != 0:
                    raise OSError
            except (OSError, FileNotFoundError):
                editor = os.environ.get('EDITOR')
                if editor:
                    if subprocess.call([editor, abs_file_path]) != 0:
                        raise OSError("The editor exited with an error code.")
                else:
                    print("\nCould not determine the default editor (the $EDITOR variable is not set).")
                    print("Please open the file manually: {}".format(abs_file_path))

    except Exception as e:
        print("\nFailed to open the file automatically: {}".format(e))
        print("Please open it manually: {}".format(abs_file_path))


def main():
    parser = argparse.ArgumentParser(
        description="Create a new lecture note.",
        epilog='Example: python3 add_new_lecture.py -s obp -t пр -r 312 -i 4 "The 5S System"'
    )

    parser.add_argument('-s', '--subject-id', type=str, required=True, help='Short ID of the subject (e.g., "philosophy").')
    parser.add_argument('-t', '--lecture-type', type=str, required=True, choices=['л', 'пр'], help='Type of session ("л" for lecture, "пр" for practice).')
    parser.add_argument('-r', '--classroom', type=str, required=True, help='Classroom number or location.')
    parser.add_argument('-i', '--absolute-lecture-id', type=int, required=True, help='The official scheduled class number for the day.')
    parser.add_argument('--relative-lecture-id', type=int, help='The actual class number for the day. Defaults to the absolute ID.')
    parser.add_argument('-d', '--date', type=str, help='Date of the lecture in YYYY-MM-DD format. Defaults to today.')
    parser.add_argument('-o', '--open', action='store_true', help='Open the created file in the default editor.')
    parser.add_argument('--repo-path', type=str, default='.', help='Path to the root of the lecture repository.')
    parser.add_argument('topic', nargs='?', type=str, default=None, help='The full topic of the lecture. Will be prompted if not provided.')

    args = parser.parse_args()

    relative_id = args.relative_lecture_id if args.relative_lecture_id is not None else args.absolute_lecture_id

    lecture_topic = args.topic
    if not lecture_topic:
        try:
            lecture_topic = input("Enter the lecture/practice topic: ")
            if not lecture_topic.strip():
                print("Error: The topic cannot be empty.", file=sys.stderr)
                sys.exit(1)
        except KeyboardInterrupt:
            print("\nOperation cancelled by user.", file=sys.stderr)
            sys.exit(0)

    lecture_date = None
    if args.date:
        try:
            lecture_date = datetime.strptime(args.date, '%Y-%m-%d').date()
        except ValueError:
            print("Error: Invalid date format '{}'. Please use YYYY-MM-DD.".format(args.date), file=sys.stderr)
            sys.exit(1)

    try:
        repo_root = args.repo_path
        repo = LectureRepository(repo_root)

        new_lecture = repo.create_new_lecture(
            subject_id=args.subject_id,
            lecture_type=LectureType(args.lecture_type),
            topic=lecture_topic,
            classroom=args.classroom,
            date=lecture_date,  # This can be None; the method will use today's date
            absolute_lecture_id=args.absolute_lecture_id,
            relative_lecture_id=relative_id
        )

        new_lecture.save()

        if args.open:
            _open_file_in_editor(new_lecture.path)

    except (FileNotFoundError, ValueError) as e:
        print("Repository Error: {}".format(e), file=sys.stderr)
        sys.exit(1)

    except Exception as e:
        print("An unexpected error occurred: {}".format(e), file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()

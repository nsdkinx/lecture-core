#!/usr/bin/python3
# -*- coding: utf-8 -*-
"""
This script adds a new subject to the lecture repository.
It creates a new entry in the 'subjects.json' file and a corresponding
directory for the lecture notes.
"""
import argparse
import json
import os
import sys

REPO_PATH = os.path.dirname(os.path.abspath(__file__))
SUBJECTS_FILE_PATH = os.path.join(REPO_PATH, "subjects.json")


def create_subject(subject_name, subject_id):
    # type: (str, str) -> None
    """
    Loads the subjects file, adds a new subject, and saves the file.
    Also creates a directory for the new subject.

    Args:
        subject_name (str): The full, official name of the subject.
        subject_id (str): A short, unique identifier for the subject.
    """
    if os.path.exists(SUBJECTS_FILE_PATH):
        try:
            with open(SUBJECTS_FILE_PATH, 'r', encoding='utf-8') as f:
                subjects_data = json.load(f)
        except (ValueError, UnicodeDecodeError):
            print(
                "Error: The file '{}' is corrupted or empty. Initializing a new one.".format(SUBJECTS_FILE_PATH)
            )
            subjects_data = {}
    else:
        print(
            "File '{}' not found. Creating a new one.".format(os.path.basename(SUBJECTS_FILE_PATH))
        )
        subjects_data = {}

    if subject_id in subjects_data:
        print("Error: A subject with the ID '{}' already exists. Aborting.".format(subject_id))
        sys.exit(1)

    if subject_name in subjects_data.values():
        print("Error: A subject with the name '{}' already exists. Aborting.".format(subject_name))
        sys.exit(1)

    subjects_data[subject_id] = subject_name

    try:
        with open(SUBJECTS_FILE_PATH, 'w', encoding='utf-8') as f:
            json.dump(subjects_data, f, ensure_ascii=False, indent=4)

        print("Success: Subject '{}' (ID: {}) was added to '{}'.".format(
            subject_name, subject_id, os.path.basename(SUBJECTS_FILE_PATH)
        ))
    except IOError as e:
        print("Error writing to file '{}': {}".format(SUBJECTS_FILE_PATH, e))
        sys.exit(1)

    subject_dir_path = os.path.join(REPO_PATH, subject_name)
    try:
        os.makedirs(subject_dir_path, exist_ok=True)
        print("Success: Created directory for the subject: '{}'".format(os.path.basename(subject_dir_path)))
    except OSError as e:
        print("Error creating directory '{}': {}".format(subject_dir_path, e))
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(
        description="Creates a new subject in the lecture repository."
    )
    parser.add_argument(
        '--name',
        type=str,
        required=True,
        help='The full, official name of the subject (e.g., "Introduction to Philosophy").'
    )
    parser.add_argument(
        '--id',
        type=str,
        required=True,
        help='A short, unique, lowercase ID for the subject (e.g., "philosophy").'
    )

    args = parser.parse_args()

    if not args.id.islower() or ' ' in args.id:
        print("Warning: The ID '{}' should be lowercase and contain no spaces.".format(args.id))

    create_subject(subject_name=args.name, subject_id=args.id)


if __name__ == "__main__":
    main()

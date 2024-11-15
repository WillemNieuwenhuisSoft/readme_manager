import datetime
import logging
import os
from pathlib import Path

log = logging.getLogger(__name__)


def needs_backup(filename: Path) -> bool:
    '''Check if the file needs a backup.
      A backup is needed if the last modification was not done today'''
    today = datetime.date.today()
    backup_date = os.path.getmtime(filename)
    backup_date = datetime.date.fromtimestamp(backup_date)
    return backup_date != today


def rotate_backups_for(filename: Path) -> None:
    log.info(f"Issued backup rotation for {filename}")
    for i in range(4, 0, -1):
        old_backup = filename.with_suffix(f'.txt.{i}')  # f"{filename}.{i}"
        new_backup = filename.with_suffix(f'.txt.{i+1}')  # f"{filename}.{i+1}"
        if i == 4 and os.path.exists(new_backup):
            os.remove(new_backup)
        if os.path.exists(old_backup):
            os.rename(old_backup, new_backup)

        # Turn current file into a new backup file with version number 1
        backup_filename = filename.with_suffix('.txt.1')  # f"{filename}.1"
        os.rename(filename, backup_filename)


def save_readme_changes(filename: Path, text: str) -> None:
    '''Save the changes to the readme file and create a backup
      of the previous version.
      Rename existing backup files by incrementing their version number'''
    if needs_backup(filename):
        rotate_backups_for(filename)

    # Save the current changes to the file
    with open(filename, 'w', encoding='utf-8') as file:
        file.write(text)

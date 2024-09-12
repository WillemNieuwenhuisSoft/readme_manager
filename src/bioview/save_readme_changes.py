import logging
import os
import datetime

log = logging.getLogger(__name__)


def save_readme_changes(filename: str, text: str) -> None:
    '''Save the changes to the readme file and create a backup
      of the previous version.'''
    today = datetime.date.today()
    backup_date = os.path.getmtime(filename)
    backup_date = datetime.date.fromtimestamp(backup_date)
    if backup_date != today:
        # first change today: create a new backup
        # Rename existing backup files by incrementing their version number
        log.info(f"Issued backup rotation for {filename}")
        for i in range(4, 0, -1):
            old_backup = f"{filename}.{i}"
            new_backup = f"{filename}.{i+1}"
            if i == 4 and os.path.exists(new_backup):
                os.remove(new_backup)
            if os.path.exists(old_backup):
                os.rename(old_backup, new_backup)

        # Create a new backup file with version number 1
        backup_filename = f"{filename}.1"
        os.rename(filename, backup_filename)

    # Save the current changes to the file
    with open(filename, 'w', encoding='utf-8') as file:
        file.write(text)

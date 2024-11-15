import os
import datetime
from pathlib import Path
from unittest import mock
import pytest
from bioview.save_readme_changes import save_readme_changes


@pytest.fixture
def mock_os():
    with mock.patch('os.path.getmtime') as mock_getmtime, \
            mock.patch('os.path.exists') as mock_exists, \
            mock.patch('os.remove') as mock_remove, \
            mock.patch('os.rename') as mock_rename:
        yield mock_getmtime, mock_exists, mock_remove, mock_rename


@pytest.fixture
def mock_open():
    with mock.patch('builtins.open', mock.mock_open()) as mock_open:
        yield mock_open


def test_save_readme_changes_new_backup(mock_os, mock_open):
    mock_getmtime, mock_exists, mock_remove, mock_rename = mock_os
    mock_getmtime.return_value = (
        datetime.datetime.now() - datetime.timedelta(days=1)).timestamp()
    mock_exists.side_effect = lambda x: (x.suffix == '.1')

    filename = Path('readme.txt')
    text = 'New content'

    save_readme_changes(filename, text)

    mock_rename.assert_any_call(filename, filename.with_suffix('.txt.1'))
    mock_open.assert_called_once_with(filename, 'w', encoding='utf-8')
    mock_open().write.assert_called_once_with(text)


def test_save_readme_changes_no_backup_needed(mock_os, mock_open):
    mock_getmtime, mock_exists, mock_remove, mock_rename = mock_os
    mock_getmtime.return_value = datetime.datetime.now().timestamp()

    filename = Path('readme.txt')
    text = 'New content'

    save_readme_changes(filename, text)

    mock_rename.assert_not_called()
    mock_open.assert_called_once_with(filename, 'w', encoding='utf-8')
    mock_open().write.assert_called_once_with(text)


def test_save_readme_changes_backup_rotation(mock_os, mock_open):
    mock_getmtime, mock_exists, mock_remove, mock_rename = mock_os
    mock_getmtime.return_value = (
        datetime.datetime.now() - datetime.timedelta(days=1)).timestamp()
    mock_exists.side_effect = lambda x: x.suffix == '.1' or x.suffix == '.2' or x.suffix == '.3' or x.suffix == '.4' or x.suffix == '.5'

    filename = Path('readme.txt')
    text = 'New content'

    save_readme_changes(filename, text)

    mock_remove.assert_called_once_with(filename.with_suffix(".txt.5"))
    mock_rename.assert_any_call(filename.with_suffix(
        ".txt.4"), filename.with_suffix(".txt.5"))
    mock_rename.assert_any_call(filename.with_suffix(
        ".txt.3"), filename.with_suffix(".txt.4"))
    mock_rename.assert_any_call(filename.with_suffix(
        ".txt.2"), filename.with_suffix(".txt.3"))
    mock_rename.assert_any_call(filename.with_suffix(
        ".txt.1"), filename.with_suffix(".txt.2"))
    mock_rename.assert_any_call(filename, filename.with_suffix(".txt.1"))
    mock_open.assert_called_once_with(filename, 'w', encoding='utf-8')
    mock_open().write.assert_called_once_with(text)

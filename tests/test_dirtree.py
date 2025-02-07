import pytest
from unittest import mock
from pathlib import Path
import tkinter as tk
from bioview.dirtree import DirTree


@pytest.fixture(scope='module')
def dir_tree():
    win = tk.Tk()
    return DirTree(win)


@mock.patch('bioview.dirtree.Path.exists')
@mock.patch('bioview.dirtree.Path.iterdir')
def test_safe_iterdir_success(mock_iterdir, mock_exists, dir_tree):
    # Mock the path.exists() to return True
    mock_exists.return_value = True
    # Mock the path.iterdir() to return a list of Path objects
    files = [Path('/path/to/file1'), Path('/path/to/file2')]
    mock_iterdir.return_value = files

    result = dir_tree._safe_iterdir(Path('/path/to/dir'))

    assert len(result) == 2
    for p, q in zip(result, files):
        assert p == q
    mock_exists.assert_called_once()
    mock_iterdir.assert_called_once()


@mock.patch('bioview.dirtree.Path.exists')
def test_safe_iterdir_path_not_exists(mock_exists, dir_tree):
    # Mock the path.exists() to return False
    mock_exists.return_value = False

    result = dir_tree._safe_iterdir(Path('/path/to/dir'))
    assert len(result) == 0
    mock_exists.assert_called_once()


@mock.patch('bioview.dirtree.Path.exists')
@mock.patch('bioview.dirtree.Path.iterdir')
def test_safe_iterdir_permission_error(mock_iterdir, mock_exists, dir_tree):
    # Mock the path.exists() to return True
    mock_exists.return_value = True
    # Mock the path.iterdir() to raise PermissionError
    mock_iterdir.side_effect = PermissionError

    result = dir_tree._safe_iterdir(Path('/path/to/dir'))
    assert len(result) == 0
    mock_exists.assert_called_once()
    mock_iterdir.assert_called_once()


def test_insert_manually(dir_tree):
    '''Test that inserting an item manually returns a valid ID'''
    id = dir_tree.insert_item(name='readme.txt', path=Path('/path/to/dir'), position=0)
    assert id is not None
    assert type(id) == str
    assert id.startswith('I0')


def test_insert_manually_twice(dir_tree):
    '''Test that inserting the same item twice returns the same ID'''
    id0 = dir_tree.insert_item(name='readme.txt', path=Path('/path/to/dir'), position=0)
    id = dir_tree.insert_item(name='readme.txt', path=Path('/path/to/dir'), position=0)
    assert id is not None
    assert id == id0

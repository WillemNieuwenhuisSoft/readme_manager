from pathlib import Path
from bioview.pretty_print_paths import pretty_print, pretty_print_name
from bioview.load_readme import read_file_contents


def test_pretty_print_with_short_path():
    path = Path("C:\\Users\\John\\Documents\\file.txt")   # length == 32
    max_length = 30
    expected_output = Path("C:\\Users\\John\\D\\file.txt")  # length == 24
    assert pretty_print(path, max_length) == expected_output


def test_pretty_print_with_long_path():
    path = Path("C:\\Users\\John\\Documents\\Folder1\\Folder2\\Folder3\\file.txt")
    max_length = 30
    expected_output = Path("C:\\Users\\John\\D\\F\\F\\F\\file.txt")
    assert pretty_print(path, max_length) == expected_output


def test_pretty_print_name():
    path = Path("C:\\Users\\John\\Documents\\file.txt")
    max_length = 30
    expected_output = Path("file.txt")
    assert pretty_print_name(path, max_length) == expected_output

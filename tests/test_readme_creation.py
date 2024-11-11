from pathlib import Path
from unittest import mock
from mock import call
import pytest
from bioview.readme_creation import ReadmeCreator, ReadmeContent
from bioview.dirtree import DirTree

# FILE: src/bioview/test_readme_creation.py


@pytest.fixture
def dir_tree():
    return mock.Mock(spec=DirTree)


@pytest.fixture
def readme_creator(dir_tree):
    return ReadmeCreator(dir_tree)


@mock.patch('builtins.open')
@mock.patch('bioview.readme_creation.files')
def test_copy_from_template(mock_files, mock_open, readme_creator):
    template_content = [
        "Header\n",
        "File list:\n",
        "Footer\n"
    ]
    mock_files.return_value.joinpath.return_value = Path("readme_template.txt")
    mock_open.return_value.__enter__.return_value.readlines.return_value = template_content

    file_mock = mock.Mock()
    file_list = [Path(f"/path/to/file{i}.txt") for i in range(3)]

    readme_creator.copy_from_template(file_mock, file_list)

    file_mock.write.assert_any_call("Header\n")
    file_mock.write.assert_any_call("File list:\n")
    for f in file_list:
        file_mock.write.assert_any_call(f"{f.name}\n")
    file_mock.write.assert_any_call("Footer\n")


@mock.patch('builtins.open')
@mock.patch('bioview.readme_creation.files')
def test_copy_from_template_no_file_list(mock_files, mock_open, readme_creator):
    template_content = [
        "Header\n",
        "Footer\n"
    ]
    mock_files.return_value.joinpath.return_value = Path("readme_template.txt")
    mock_open.return_value.__enter__.return_value.readlines.return_value = template_content

    file_mock = mock.Mock()
    file_list = []

    readme_creator.copy_from_template(file_mock, file_list)

    file_mock.write.assert_has_calls([call("Header\n"), call("Footer\n")])

from pathlib import Path
import mock
import bioview.load_readme as load_readme


@mock.patch('builtins.open')
@mock.patch('bioview.load_readme.Path.stat')
@mock.patch('bioview.load_readme.CharsetDetector.get_charset')
def test_loadReadmeFile_with_valid_encoding(mock_get_charset, mock_stat, mock_open):
    # Mock the file contents and encoding
    file_contents = "This is a test file."
    encoding = "utf-8-sig"
    mock_get_charset.return_value = encoding
    mock_stat.return_value.st_size = 20
    mock_open.return_value.__enter__.return_value.read.return_value = file_contents

    # Call the method
    actual_contents = load_readme.read_file_contents(Path("test_file.txt"))

    # Assert that the textfield contains the expected contents
    assert actual_contents == file_contents


@mock.patch('builtins.open')
@mock.patch('bioview.load_readme.Path.stat')
@mock.patch('bioview.load_readme.CharsetDetector.get_charset')
def test_loadReadmeFile_with_invalid_encoding(mock_get_charset, mock_stat, mock_open):
    # Mock the file contents and encoding
    file_contents = "This is a test file."
    encoding = None
    mock_open.return_value.__enter__.return_value.read.return_value = file_contents
    mock_get_charset.return_value = encoding
    mock_stat.return_value.st_size = 20

    # Call the method
    actual_contents = load_readme.read_file_contents(Path("test_file.txt"))

    # Assert that the textfield contains the error message
    expected_contents = "Error: Unable to decode file."
    assert actual_contents == expected_contents

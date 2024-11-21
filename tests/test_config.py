import json
from pathlib import Path
from unittest import mock
import pytest
from bioview.config import Config, CONFIG_FILE


@pytest.fixture
def config_data():
    return {
        "WorkFolder": str(Path("/path/to/workfolder")),
        "MRU": [str(Path(f"/path/to/recent{i}")) for i in range(5)],
        "active_template": (Path("/path/to/active_template.txt")).name
    }


@mock.patch('builtins.open')
@mock.patch.object(Path, 'exists', return_value=True)
def test_load_with_existing_config(mock_exists, mock_open, config_data):
    mock_open.return_value.__enter__.return_value.read.return_value = json.dumps(
        config_data)

    config = Config(WorkFolder=Path("/default/workfolder"))

    assert config.WorkFolder == Path(config_data["WorkFolder"])
    assert config.MRU == [Path(p) for p in config_data["MRU"]]
    assert config.active_template == config_data["active_template"]


@mock.patch('builtins.open')
@mock.patch.object(Path, 'exists', return_value=False)
def test_load_with_no_config(mock_exists, mock_open):
    config = Config(WorkFolder=Path("/default/workfolder"))

    assert config.WorkFolder == Path("/default/workfolder")
    assert config.MRU == [Path() for _ in range(5)]
    assert config.active_template == config.all_templates[0]

from dataclasses import dataclass, field, asdict
from importlib.resources import files
import json
from pathlib import Path
from typing import List

CONFIG_FILE = Path.home() / 'bioview.json'


@dataclass
class Config:
    WorkFolder: Path
    MRU: List[Path] = field(default_factory=lambda: [Path() for _ in range(5)])
    active_template: Path = 'readme_template.txt'
    all_templates: List[str] = field(
        default_factory=lambda: [f.name for f in files(
            'animations').iterdir() if f.suffix == '.txt'])

    def __post_init__(self):
        self.load()

    def load(self):
        if CONFIG_FILE.exists():
            with open(CONFIG_FILE, 'r', encoding='utf-8') as file:
                data = json.load(file)
                self.WorkFolder = Path(data.get('WorkFolder'))
                self.MRU = [Path(p) for p in data.get('MRU')]
                template = data.get('active_template')
                if template:
                    self.active_template = files('animations').joinpath(template)
                else:
                    self.set_active_template(self.all_templates[0])

    def save(self):
        with open(CONFIG_FILE, 'w', encoding='utf-8') as file:
            json.dump(asdict(self), file, indent=4, default=str)

    def set_work_folder(self, path: Path):
        self.WorkFolder = path
        self.save()

    def set_active_template(self, path: Path):
        self.active_template = path.name
        self.save()

    def add_to_mru(self, path: Path):
        if path in self.MRU:
            self.MRU.remove(path)
        self.MRU.insert(0, path)
        self.MRU = self.MRU[:5]  # Keep only the 5 most recent entries
        self.save()

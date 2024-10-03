from dataclasses import dataclass, field, asdict
import json
from pathlib import Path
from typing import List

CONFIG_FILE = Path.home() / 'bioview.json'


@dataclass
class Config:
    WorkFolder: Path
    MRU: List[Path] = field(default_factory=lambda: [Path() for _ in range(5)])

    def __post_init__(self):
        self.load()

    def load(self):
        if CONFIG_FILE.exists():
            with open(CONFIG_FILE, 'r', encoding='utf-8') as file:
                data = json.load(file)
                self.WorkFolder = Path(data['WorkFolder'])
                self.MRU = [Path(p) for p in data['MRU']]

    def save(self):
        with open(CONFIG_FILE, 'w', encoding='utf-8') as file:
            json.dump(asdict(self), file, indent=4, default=str)

    def set_work_folder(self, path: Path):
        self.WorkFolder = path
        self.save()

    def add_to_mru(self, path: Path):
        if path in self.MRU:
            self.MRU.remove(path)
        self.MRU.insert(0, path)
        self.MRU = self.MRU[:5]  # Keep only the 5 most recent entries
        self.save()

# Example usage


# def main():
#     config = Config(WorkFolder=Path.home())
#     print(f"Initial WorkFolder: {config.WorkFolder}")
#     print(f"Initial MRU: {config.MRU}")

#     # Simulate changing the work folder
#     new_work_folder = Path(__file__).parent / 'new' / 'work' / 'folder'
#     config.set_work_folder(new_work_folder)
#     print(f"Updated WorkFolder: {config.WorkFolder}")

#     # Simulate adding paths to MRU
#     config.add_to_mru(Path('/path/to/recent/file1'))
#     config.add_to_mru(Path('/path/to/recent/file2'))
#     print(f"Updated MRU: {config.MRU}")


# if __name__ == '__main__':
#     main()

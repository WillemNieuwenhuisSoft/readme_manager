from datetime import date
from enum import Enum
from importlib.resources import files
import logging
import os
from pathlib import Path
from tkinter import Menu, filedialog
from typing import TextIO
from bioview.dirtree import DirTree


class ReadmeContent(Enum):
    EMPTY = 1
    WITH_FILE_LIST = 2
    TEMPLATE = 3
    TEMPLATE_WITH_FILE_LIST = 4


logger = logging.getLogger(__name__)


class ReadmeCreator:
    def __init__(self, directory_tree: DirTree):
        self.dir_tree = directory_tree

    def create_file_list(self, folder: Path) -> list[Path]:
        return folder.iterdir()

    def create_readme_context_menu(self):
        # Create the create-readme context menu
        self.context_menu = Menu(self.dir_tree.treeview, tearoff=0)
        self.context_menu.add_command(
            label="Create empty README",
            command=lambda f=ReadmeContent.EMPTY: self.create_readme(f))
        self.context_menu.add_command(
            label="Create README with file list",
            command=lambda f=ReadmeContent.WITH_FILE_LIST: self.create_readme(f))
        self.context_menu.add_command(
            label="Create README from template",
            command=lambda f=ReadmeContent.TEMPLATE: self.create_readme(f))
        self.context_menu.add_command(
            label="Create README from template/file list",
            command=lambda f=ReadmeContent.TEMPLATE_WITH_FILE_LIST: self.create_readme(f))

        return self.context_menu

    def init_readme_file(self) -> Path | None:
        selected_path = self.dir_tree.get_selected_path()
        readme_file = "readme.txt"
        file = filedialog.asksaveasfile(
            initialfile=readme_file,
            initialdir=selected_path,
            defaultextension=".txt",
            filetypes=[("Readme files", "*.txt"), ("All files", "*.*")]
        )
        if not file:
            return None

        file.close()

        return Path(file.name)

    def write_header(self, file: TextIO) -> None:
        user = os.getlogin()
        file.write(f"This {file.name} file was generated on {
            date.today().strftime('%Y-%m-%d')} by {user}\n\n")

    def write_file_list(self, file: TextIO, file_list: list[Path]) -> None:
        for f in file_list:
            file.write(f"{f.name}\n")
        file.write("\n")

    def copy_from_template(self, file: TextIO, file_list: list[Path]):
        template_name = files('animations').joinpath('readme_template.txt')
        with open(template_name, 'r') as template:
            template_content = template.readlines()
            for line in template_content:
                file.write(f"{line}")
                if line.lower().startswith('file list'):
                    self.write_file_list(file, file_list)

    def create_readme(self, content: ReadmeContent) -> None:
        file_path = self.init_readme_file()
        if not file_path:
            return

        file_list = []
        if content in [ReadmeContent.WITH_FILE_LIST, ReadmeContent.TEMPLATE_WITH_FILE_LIST]:
            file_list = self.create_file_list(self.dir_tree.get_selected_path())

        with open(file_path, 'w') as file:
            self.write_header(file)
            if content in [ReadmeContent.TEMPLATE, ReadmeContent.TEMPLATE_WITH_FILE_LIST]:
                self.copy_from_template(file, file_list)
            elif content == ReadmeContent.WITH_FILE_LIST:
                self.write_file_list(file, file_list)

        folder_id = self.dir_tree.get_selected_id()
        self.dir_tree.insert_item(file_path.name, file_path, folder_id, position=0)
        logger.info(f"{file_path.name} created at {file_path}")

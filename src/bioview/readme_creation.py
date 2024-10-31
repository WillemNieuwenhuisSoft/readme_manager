from datetime import date
from importlib.resources import files
import logging
import os
from pathlib import Path
from tkinter import Menu, filedialog
from bioview.dirtree import DirTree


INCLUDE_FILES: bool = True
NO_FILE_LIST: bool = False

logger = logging.getLogger(__name__)


class ReadmeCreator:
    def __init__(self, directory_tree: DirTree):
        self.dir_tree = directory_tree

    def create_readme_context_menu(self):
        # Create the create-readme context menu
        self.context_menu = Menu(self.dir_tree.treeview, tearoff=0)
        self.context_menu.add_command(
            label="Create empty README", command=lambda f=NO_FILE_LIST: self.create_readme(f))
        self.context_menu.add_command(
            label="Create README with file list", command=lambda f=INCLUDE_FILES: self.create_readme(f))
        self.context_menu.add_command(
            label="Create README from template", command=lambda f=NO_FILE_LIST: self.create_readme_template(f))
        self.context_menu.add_command(
            label="Create README from template/file list", command=lambda f=INCLUDE_FILES: self.create_readme_template(f))

        return self.context_menu

    def create_readme(self, include_file_list: bool = False) -> Path | bool:
        selected_path = self.dir_tree.get_selected_path()
        readme_path = selected_path / "readme.txt"

        file = filedialog.asksaveasfile(
            initialfile=readme_path,
            defaultextension=".txt",
            filetypes=[("Readme files", "*.txt"), ("All files", "*.*")]
        )
        if not file:
            return False

        user = os.getlogin()
        file_path = Path(file.name)
        file.write(f"This {file_path.name} file was generated on {
                   date.today().strftime('%Y-%m-%d')} by {user}\n\n")
        if include_file_list:
            files = file_path.parent.iterdir()
            for f in files:
                file.write(f"{f.name}\n")
        file.close()

        folder_id = self.dir_tree.get_selected_id()
        self.dir_tree.insert_item(file_path.name, file_path, folder_id, position=0)
        logger.info(f"{file_path.name} created at {file_path}")

        return file_path

    def create_readme_template(self, include_file_list: bool = False) -> bool:
        # do not add file list yet, it will be added later
        new_file = self.create_readme(include_file_list=False)
        if not new_file:
            return False

        template = files('animations').joinpath('readme_template.txt')

        files_in_folder = []
        if include_file_list:
            files_in_folder = new_file.parent.iterdir()

        with open(template, 'r') as f:
            template_content = f.readlines()
            with open(new_file, 'a') as new_f:
                for line in template_content:
                    new_f.write(f"{line}")
                    if line.lower().startswith('file list'):
                        for f in files_in_folder:
                            new_f.write(f"{f.name}\n")
                        new_f.write("\n")

            logger.info(f"Readme template copied to {new_file}")
            folder_id = self.dir_tree.get_selected_id()
            self.dir_tree.insert_item("readme.txt", new_file, folder_id, position=0)

        return True

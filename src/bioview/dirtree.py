from datetime import date
from importlib.resources import files
import logging
import shutil
import sys
import tkinter as tk
from pathlib import Path
from tkinter import ttk, Menu
from PIL import ImageTk
from bioview.tree_follower import Tree


logger = logging.getLogger(__name__)


class DirTree(ttk.Frame, Tree):

    def __init__(self, window: tk.Tk | tk.Toplevel, root_path: Path = None) -> None:
        ttk.Frame.__init__(self, window)
        Tree.__init__(self)
        # show="tree" removes the column header, since we
        # are not using the table feature.
        self.treeview = ttk.Treeview(self, show="tree")
        self.treeview.grid(row=0, column=0, sticky="nsew")

        # Create the create-readme context menu
        self.context_menu = Menu(self.treeview, tearoff=0)
        self.context_menu.add_command(label="Create README", command=self.create_readme)
        self.context_menu.add_command(
            label="Create README from template", command=self.create_readme_template)

        # Bind right-click to show context menu
        self.treeview.bind("<Button-3>", self.show_context_menu)
        # Call the item_opened() method each item an item is expanded.
        self.treeview.tag_bind(
            "fstag", "<<TreeviewOpen>>", self.item_opened)

        # Make sure the treeview widget follows the window when resizing.
        for w in (self, window):
            w.rowconfigure(0, weight=1)
            w.columnconfigure(0, weight=1)

        self.grid(row=0, column=0, sticky="nsew")
        # This dictionary maps the treeview items IDs with the
        # path of the file or folder.
        self.fsobjects: dict[str, Path] = {}
        self.file_image = ImageTk.PhotoImage(
            file=files('animations').joinpath('file.ico'))
        self.folder_image = ImageTk.PhotoImage(
            file=files('animations').joinpath('folder.ico'))
        # Load the root directory.
        if root_path is None:
            root_path = Path(Path(sys.executable).anchor)
        self.load_tree(root_path)

    def show_context_menu(self, event):
        # Select the item under the cursor
        iid = self.treeview.identify_row(event.y)
        if iid:
            self.treeview.selection_set(iid)
            selected_path = self.fsobjects[iid]
            if selected_path.is_dir():
                self.context_menu.post(event.x_root, event.y_root)

    def create_readme(self):
        selected_item = self.treeview.selection()[0]
        selected_path = self.fsobjects[selected_item]
        readme_path = selected_path / "readme.txt"

        if not readme_path.exists():
            with open(readme_path, 'w') as f:
                f.write(
                    f"This <DATASETNAME>_readme.txt file was generated on {date.today().strftime('%Y-%m-%d')} by <NAME>\n\n")
            self.insert_item("readme.txt", readme_path, selected_item, position=0)
            logger.info(f"readme.txt created at {readme_path}")
        else:
            logger.warning(f"readme.txt already exists at {readme_path}")

    def create_readme_template(self):
        selected_item = self.treeview.selection()[0]
        selected_path = self.fsobjects[selected_item]
        readme_path = selected_path / "readme.txt"

        template = files('animations').joinpath('readme_template.txt')

        if not readme_path.exists():
            shutil.copyfile(template, readme_path)
            logger.info(f"Readme template copied to {readme_path}")
            self.insert_item("readme.txt", readme_path, selected_item, position=0)
        else:
            logger.warning(f"readme.txt already exists at {readme_path}")

    def safe_iterdir(self, path: Path) -> tuple[Path, ...] | tuple[()]:
        """
        Like `Path.iterdir()`, but do not stop on permission errors.
        """
        try:
            return tuple(path.iterdir())
        except PermissionError:
            logger.error("You don't have permission to read", path)
            return ()

    def get_icon(self, path: Path) -> tk.PhotoImage:
        """
        Return a folder icon if `path` is a directory and
        a file icon otherwise.
        """
        return self.folder_image if path.is_dir() else self.file_image

    def insert_item(self, name: str, path: Path, parent: str = "", position=tk.END) -> str:
        """
        Insert a file or folder into the treeview and return the item ID.
        """
        iid = self.treeview.insert(
            parent, position, text=name, tags=("fstag",),
            image=self.get_icon(path))
        self.fsobjects[iid] = path
        if not path.exists():
            self.notify("item_added", path)
        return iid

    def load_tree(self, path: Path) -> None:
        # insert top-level item
        iid = self.insert_item(path.name, path)
        self.load_subtree(path, parent=iid)

    def load_subtree(self, path: Path, parent: str = "") -> None:
        """
        Load the contents of `path` into the treeview.
        """
        for fsobj in self.safe_iterdir(path):
            fullpath = path / fsobj
            child = self.insert_item(fsobj.name, fullpath, parent)
            # Preload the content of each directory within `path`.
            # This is necessary to make the folder item expandable.
            if fullpath.is_dir():
                for sub_fsobj in self.safe_iterdir(fullpath):
                    self.insert_item(sub_fsobj.name, fullpath / sub_fsobj, child)

    def load_subitems(self, iid: str) -> None:
        """
        Load the content of each folder inside the specified item
        into the treeview.
        """
        for child_iid in self.treeview.get_children(iid):
            if self.fsobjects[child_iid].is_dir():
                self.load_subtree(self.fsobjects[child_iid],
                                  parent=child_iid)

    def item_opened(self, _event: tk.Event) -> None:
        """
        Handler invoked when a folder item is expanded.
        """
        # Get the expanded item.
        iid = self.treeview.selection()[0]
        # If it is a folder, loads its content.
        self.load_subitems(iid)

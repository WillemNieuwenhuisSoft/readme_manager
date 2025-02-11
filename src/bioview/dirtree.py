from importlib.resources import files
import logging
import sys
import tkinter as tk
from pathlib import Path
from tkinter import ttk, Menu
from PIL import ImageTk
from bioview.tree_follower import Tree

CONTEXT_BUTTON = '<Button-3>'

logger = logging.getLogger(__name__)


class DirTree(ttk.Frame, Tree):

    def __init__(self, window: tk.Tk | tk.Toplevel, root_path: Path = None) -> None:
        ttk.Frame.__init__(self, window)
        Tree.__init__(self)
        # show="tree" removes the column header, since we
        # are not using the table feature.
        self.treeview = ttk.Treeview(self, show="tree")
        self.treeview.grid(row=0, column=0, sticky="nsew")

        # Call the item_opened() method each item an item is expanded.
        self.treeview.tag_bind(
            "fstag", "<<TreeviewOpen>>", self._item_opened)
        self.treeview.bind("<ButtonRelease-1>", self._view_readme)

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

    def set_context_menu(self, context_menu: Menu):
        self.context_menu = context_menu
        # Bind right-click to show context menu
        self.treeview.bind(CONTEXT_BUTTON, self._show_context_menu)

    def _show_context_menu(self, event):
        # Select the item under the cursor
        iid = self.treeview.identify_row(event.y)
        if iid:
            self.treeview.selection_set(iid)
            selected_path = self.fsobjects[iid]
            if selected_path.is_dir():
                self.context_menu.post(event.x_root, event.y_root)

    def get_selected_id(self) -> str:
        return self.treeview.selection()[0]

    def get_selected_path(self) -> Path:
        selected_item = self.treeview.selection()[0]
        return self.fsobjects[selected_item]

    def get_item_id(self, path: Path) -> str:
        """Get the Treeview item ID corresponding to the given path."""
        for k, v in self.fsobjects.items():
            if v == path:
                return k
        return ''

    def highlight_filenames(self, folder: Path, filenames: list[str]) -> None:
        """Highlight or select all names in the open Treeview branch where the current file is located."""
        if folder is None:
            return

        folder_id = self.get_item_id(folder)
        if not folder_id:
            return

        self.treeview.item(folder_id, open=True)

        # Highlight or select matching items
        for child_id in self.treeview.get_children(folder_id):
            item_text = self.treeview.item(child_id, 'text')
            if item_text in filenames:
                self.treeview.selection_add(child_id)
                self.treeview.item(child_id, tags='highlight')

        # Configure the highlight tag
        self.treeview.tag_configure('highlight', background='red', foreground='black')

    def clear_selection(self) -> None:
        """Deselect all items in the Treeview."""
        for item in self.treeview.selection():
            self.treeview.selection_remove(item)

    def _safe_iterdir(self, path: Path) -> tuple[Path, ...] | tuple[()]:
        """
        Like `Path.iterdir()`, but do not stop on permission errors.
        """
        try:
            if path.exists():
                return tuple(path.iterdir())
            logger.warning(f"Could not locate folder: {path}")
            return ()
        except PermissionError:
            logger.error(f"You don't have permission to read {path}")
            return ()

    def _get_icon(self, path: Path) -> tk.PhotoImage:
        """
        Return a folder icon if `path` is a directory and
        a file icon otherwise.
        """
        return self.folder_image if path.is_dir() else self.file_image

    def insert_item(self, name: str, path: Path, parent: str = "", position=tk.END) -> str:
        """
        Insert a file or folder into the treeview and return the item ID.
        If position == 0, it means that the item is added manually by the user
        In that case a check is made whether the item is already in the tree (this
        can happen only when trying to create a new readme file that already exists)
        """
        if position == 0:
            for child in self.treeview.get_children(parent):
                if self.fsobjects[child] == path:
                    return child
            self.notify("item_added", path)
        iid = self.treeview.insert(
            parent, position, text=name, tags=("fstag",),
            image=self._get_icon(path))
        self.fsobjects[iid] = path
        return iid

    def clear_tree(self) -> None:
        self.fsobjects.clear()
        self.treeview.delete(*self.treeview.get_children())

    def load_tree(self, path: Path) -> None:
        # insert top-level item
        iid = self.insert_item(path.name, path)
        self._load_subtree(path, parent=iid)

    def _load_subtree(self, path: Path, parent: str = "") -> None:
        """
        Load the contents of `path` into the treeview.
        """
        if not path.exists():
            logger.warning(f"Could not locate folder: {path}")
            return

        for fsobj in self._safe_iterdir(path):
            fullpath = path / fsobj
            child = self.insert_item(fsobj.name, fullpath, parent)
            # Preload the content of each directory within `path`.
            # This is necessary to make the folder item expandable.
            # if fullpath.is_dir():
            #     for sub_fsobj in self._safe_iterdir(fullpath):
            #         self.insert_item(sub_fsobj.name, fullpath / sub_fsobj, child)

    def _load_subitems(self, iid: str) -> None:
        """
        Load the content of each folder inside the specified item
        into the treeview.
        """
        for child_iid in self.treeview.get_children(iid):
            if self.fsobjects[child_iid].is_dir():
                self._load_subtree(self.fsobjects[child_iid],
                                   parent=child_iid)

    def _item_opened(self, _event: tk.Event) -> None:
        """
        Handler invoked when a folder item is expanded.
        """
        # Get the expanded item.
        iid = self.treeview.selection()[0]
        # If it is a folder, loads its content.
        self._load_subitems(iid)

    def _view_readme(self, _event: tk.Event) -> None:
        """
        Handler invoked when a left-click is made on an item.
        """
        selected_path = self.get_selected_path()
        if selected_path.is_file():
            self.notify("readme_clicked", selected_path)

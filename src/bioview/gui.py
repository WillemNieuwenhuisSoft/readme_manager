from abc import ABC, abstractmethod
from importlib.resources import files
import logging
import tkinter as tk
from tkinter import ttk
from tkinter import filedialog
from tkinter import WORD, CHAR, NONE
import subprocess
from pathlib import Path
import pandas as pd
from bioview.config import Config
from bioview.load_readme import read_file_contents
from bioview.load_readme_list import load_list_from_text
from bioview.readme_creation import ReadmeCreator
from bioview.save_readme_changes import save_readme_changes
from bioview.scan_readmefiles import scan_readme_files
from bioview.progress_window import ProgressPopup
from bioview.calback_thread import CallbackThread
from bioview.dirtree import DirTree

config = Config(WorkFolder=Path.home())
LIST_FILE = Path('all_readme_files.lst')
FOLDER_ICON_LOCATION = files('animations').joinpath('folder.ico')
FILE_ICON_LOCATION = files('animations').joinpath('file.ico')

logger = logging.getLogger(__name__)


class TreeFollowerObserver(ABC):
    @abstractmethod
    def update(self, event: str, item_id: Path):
        pass


def pretty_print(path: str, max_length: int) -> Path:
    # full folder names
    parts = Path(path).parts
    # only first letters
    short_parts = list(map(lambda part: part.lstrip()[0], parts))

    # since we show drive and file fully
    length_remaining = max_length - len(parts[0]) - len(parts[-1]) - 1
    short_start = 1
    short_end = len(parts) - 1

    # try to fit as many full names as possible in the remaining length
    while short_start < short_end and len(parts[short_start]) < length_remaining:
        length_remaining -= (len(parts[short_start]) + 1)
        short_start += 1

    # first print drive, then full names
    pretty = parts[0] + "\\".join(parts[1:short_start])
    # then short names (if needed)
    if short_end - short_start > 0:
        pretty += "\\" + "\\".join(short_parts[short_start:short_end])
    # then file name
    return Path(pretty + "\\" + parts[-1])


def pretty_print_name(path: str, max_length: int) -> Path:
    ''' Pretty print a path, showing only the name part
    '''
    # full folder names
    parts = Path(path).parts

    # extract the name only
    pretty = parts[-1]
    return Path(pretty)


class MainWindow(TreeFollowerObserver):

    current_filename: Path = None
    progress = None
    folder_icon = None
    file_icon = None

    def onExit(self):
        exit()

    def __init__(self):
        pass

    def build_menu(self):
        self.menubar = tk.Menu(self.top)
        self.fileMenu = tk.Menu(self.menubar)

        self.fileMenu.add_command(label='Switch to folder',
                                  command=lambda f=None, window=self: switch_to_folder(window, f))
        self.fileMenu.add_command(label='Open filename listfile',
                                  command=self.open_text_file)
        self.fileMenu.add_command(label='Scan for readme files',
                                  command=self.rescan_readme_files)
        self.fileMenu.add_separator()
        # Add "Recent" submenu
        self.recent_menu = tk.Menu(self.fileMenu, tearoff=0)
        self.fileMenu.add_cascade(label="Recent", menu=self.recent_menu)
        self.update_recent_menu()
        self.fileMenu.add_separator()
        self.fileMenu.add_command(label='Exit', command=self.onExit)
        self.menubar.add_cascade(menu=self.fileMenu, label='File')
        self.top['menu'] = self.menubar

    def build_left_frame(self, parent_frame: tk.Frame):
        self.project_folder_label = tk.Label(
            parent_frame, text="", fg='white', background='red', justify='left')
        self.project_folder_label.pack(fill='x')

        paned_window = ttk.PanedWindow(parent_frame, orient=tk.VERTICAL)
        paned_window.pack(fill='both', expand=True)
        top_frame = tk.Frame(paned_window)
        top_frame.pack(fill='both', expand=True)
        bottom_frame = tk.Frame(paned_window)
        bottom_frame.pack(fill='both', expand=True)

        self.listbox = tk.Listbox(
            top_frame, selectmode=tk.EXTENDED, exportselection=False)

        self.scrollbar_list = tk.Scrollbar(top_frame, orient="vertical")
        self.scrollbar_list_horizontal = tk.Scrollbar(top_frame, orient="horizontal")

        # Configure the listbox to use scrollbars
        self.listbox.config(yscrollcommand=self.scrollbar_list.set,
                            xscrollcommand=self.scrollbar_list_horizontal.set)
        self.scrollbar_list.config(command=self.listbox.yview)
        self.scrollbar_list_horizontal.config(command=self.listbox.xview)

        self.dirtree = DirTree(bottom_frame, root_path=config.WorkFolder)
        self.readme_creator = ReadmeCreator(self.dirtree)
        dir_context_menu = self.readme_creator.create_readme_context_menu()
        self.dirtree.set_context_menu(dir_context_menu)

        paned_window.add(top_frame, weight=1)
        paned_window.add(bottom_frame, weight=1)

        # Create a context menu for the listbox
        self.context_menu = tk.Menu(self.listbox, tearoff=0)
        self.context_menu.add_command(
            label="Open in Explorer", command=self.open_in_explorer)
        self.context_menu.add_command(
            label="Save selected items", command=self.save_selection, state=tk.DISABLED)

        # setup the layout
        self.project_folder_label.pack(side="top", fill="x")
        self.scrollbar_list.pack(side="right", fill="y")
        self.listbox.pack(side="top", fill="both", expand=True)
        self.scrollbar_list_horizontal.pack(side="bottom", fill="x")
        self.dirtree.pack(side="bottom", fill="both", expand=True)
        self.dirtree.attach(self)

    def build_edit_button_bar(self, right_frame: tk.Frame):
        self.button_bar = tk.Frame(right_frame)
        self.button_bar.pack(side="top", fill="x")

        # Add a button to toggle textfield wrap option
        self.toggle_wrap_button = tk.Button(
            self.button_bar, text="Wrapping: Off", command=self.toggle_wrap)
        self.toggle_edit_button = tk.Button(
            self.button_bar, text="Edit: Disabled", command=self.toggle_edit_event)
        self.save_changes_button = tk.Button(
            self.button_bar, text="Save Changes", command=self.save_changes_event, state=tk.DISABLED)
        self.toggle_wrap_button.pack(side="left")
        self.toggle_edit_button.pack(side="left")
        self.save_changes_button.pack(side="left")

    def build_right_frame(self, right_frame: tk.Frame):
        # Create a label for the filename
        self.filename_label = tk.Label(
            right_frame, text="", fg='white', background='red', justify='left')
        self.filename_label.pack(side="top", fill="x")

        # Create a frame for the button bar
        self.build_edit_button_bar(right_frame)

        self.textfield = tk.Text(right_frame, wrap=NONE, undo=True, exportselection=False,
                                 autoseparators=True, state='disabled')

        # Create scrollbars for the textfield
        self.scrollbar_text = tk.Scrollbar(right_frame, orient="vertical")
        self.scrollbar_text_hor = tk.Scrollbar(right_frame, orient="horizontal")
        self.scrollbar_text_hor.pack(side="bottom", fill="x")
        self.textfield.pack(side="left", fill="both", expand=True)
        self.scrollbar_text.pack(side="right", fill="y")

        # Configure the textfield to use the scrollbar
        self.textfield.config(yscrollcommand=self.scrollbar_text.set,
                              xscrollcommand=self.scrollbar_text_hor.set)

        self.scrollbar_text.config(command=self.textfield.yview)
        self.scrollbar_text_hor.config(command=self.textfield.xview)

    def bind_all_events(self):
        self.textfield.bind("<<Modified>>", self.modified_flag_changed)
        self.textfield.bind("<Control-s>", self.save_changes_event)
        self.textfield.bind("<FocusOut>", self.focusout_event)
        # Bind right-click to show context menu
        self.listbox.bind("<Button-3>", self.show_context_menu)
        self.listbox.bind('<<ListboxSelect>>', self.onListboxSelect)

    def build_gui(self):
        self.top = tk.Tk()

        self.top.title('BioSpace')
        self.top.geometry("1200x700")

        self.top.grid_columnconfigure(0, weight=1)
        self.top.grid_rowconfigure(0, weight=1)

        self.top.option_add('*tearOff', False)

        self.build_menu()

        # Create a PanedWindow
        main_paned_window = ttk.PanedWindow(self.top, orient=tk.HORIZONTAL)
        main_paned_window.grid(row=0, column=0, sticky='nsew')

        left_frame = ttk.Frame(main_paned_window, width=500)
        left_frame.grid(row=0, column=0, sticky='new')
        right_frame = ttk.Frame(main_paned_window)
        right_frame.grid(row=0, column=1, sticky='new')

        self.build_left_frame(left_frame)

        self.build_right_frame(right_frame)

        # Add frames to the PanedWindow
        main_paned_window.add(left_frame, weight=1)
        main_paned_window.add(right_frame, weight=1)

        # Configure the frames to expand with the window
        left_frame.grid_rowconfigure(0, weight=1)
        left_frame.grid_columnconfigure(0, weight=1)
        right_frame.grid_rowconfigure(0, weight=1)
        right_frame.grid_columnconfigure(0, weight=1)

        self.bind_all_events()

    def initialize(self):
        folder = config.WorkFolder
        self.project_folder_label.config(text=folder)
        self.update_recent_menu()
        if (folder / LIST_FILE).exists():
            filenames = load_list_from_text(folder / LIST_FILE)
            self.populate_listbox(filenames)
            self.clear_editor()

    # Observer callback
    def update(self, event: str, item_id: Path):
        if event == "item_added":
            new_readme = pd.Series(str(item_id))
            filenames = pd.concat([new_readme, self.filenames])
            self.populate_listbox(filenames)
            self.listbox.selection_set(0)   # select the new readme file

            logger.info(f"{event}: {item_id}")
        if event == "readme_clicked":
            self.loadReadmeFile(item_id)

    # File menu event handlers
    # --------------------------
    def update_recent_menu(self):
        self.recent_menu.delete(0, tk.END)
        for folder in config.MRU:
            if folder == Path('.'):
                continue
            self.recent_menu.add_command(
                label=str(folder), command=lambda f=folder, window=self: switch_to_folder(window, f))

    def open_text_file(self) -> None:
        file_path = filedialog.askopenfilename(
            filetypes=[("List files", "*.lst"), ("All files", "*.*")]
        )
        if file_path:
            self.populate_listbox(load_list_from_text(Path(file_path)))

    def reload_readme_list(self) -> None:
        self.progress.stop_animation()
        self.populate_listbox(load_list_from_text(config.WorkFolder / LIST_FILE))

    def rescan_readme_files(self) -> None:
        self.progress = ProgressPopup(self.top)
        self.progress.update_text("Scanning for readme files. This can take some time")
        self.progress.start_animation()

        # rescan for readme files
        t = CallbackThread(target=scan_readme_files,
                           args=(config.WorkFolder, config.WorkFolder / LIST_FILE),
                           callback=self.reload_readme_list)
        t.start()

    # Textfield event handlers
    # --------------------------
    def clear_editor(self):
        # clear edit window
        current_state = self.textfield.cget("state")
        self.textfield.config(state='normal')    # allow insert if editor R/O
        self.filename_label.config(text="")
        self.textfield.delete('1.0', tk.END)
        self.textfield.edit_modified(False)
        self.textfield.config(state=current_state)  # restore state

    def modified_flag_changed(self, event) -> None:
        if self.textfield.edit_modified():
            self.changed_file = self.current_filename
            self.save_changes_button.config(state=tk.NORMAL)
        else:
            self.save_changes_button.config(state=tk.DISABLED)

    def toggle_wrap(self) -> None:
        '''Toggle the wrap option of the textfield
        '''
        current_wrap = self.textfield.cget("wrap")
        new_wrap = NONE if current_wrap == WORD else WORD
        new_wrap_ui = "Off" if current_wrap == WORD else "On"
        self.textfield.config(wrap=new_wrap)
        self.toggle_wrap_button.config(text=f"Wrapping: {new_wrap_ui.upper()}")

    def focusout_event(self, event) -> None:
        logger.info("focus_out event")
        # TODO: optionally ask user to save changes
        if self.textfield.edit_modified():
            self.save_changes_event()

    def save_changes_event(self, event=None) -> None:
        logger.info("Save changes event")

        if not self.current_filename:
            return

        save_readme_changes(self.current_filename, self.textfield.get('1.0', tk.END))
        self.textfield.edit_modified(False)
        return

    def toggle_edit_event(self) -> None:
        '''Toggle the state of the textfield between read-only and editable
        '''
        current_state = self.textfield.cget("state")
        new_state = "normal" if current_state == "disabled" else "disabled"
        self.textfield.config(state=new_state)
        self.toggle_edit_button.config(
            text="Edit: Disabled" if new_state == "disabled" else "Edit: Enabled")

    # Listbox event handlers
    # ------------------------
    def populate_listbox(self, filenames: pd.Series) -> None:
        if filenames is None:
            return

        self.filenames = filenames
        # Clear the listbox first
        self.listbox.delete(0, tk.END)

        # Populate listbox with filenames
        for filename in self.filenames:
            self.listbox.insert(tk.END, pretty_print_name(filename, 50))

    def onListboxSelect(self, event) -> None:
        self.top.after_idle(self.handle_listbox_select)

    def handle_listbox_select(self) -> None:
        logger.info("Listbox selection processed")

        selection = self.listbox.curselection()
        if not selection:
            return

        if len(selection) == 1:
            self.current_filename = Path(self.filenames.array[selection])
            if self.current_filename.exists():
                self.loadReadmeFile(self.current_filename)
            else:
                self.clear_editor()
                self.filename_label.config(text=f'''Could not find "{
                                           self.current_filename}"''')

    def loadReadmeFile(self, filename: Path) -> None:
        '''Load the contents of the readme file with name filename into the textfield.
           It is checked for different possible encodings 
        '''
        file_contents = read_file_contents(filename)
        current_state = self.textfield.cget("state")
        self.textfield.configure(state='normal')    # allow insert if editor R/O
        self.clear_editor()
        self.filename_label.config(text=filename)
        self.textfield.insert(tk.END, file_contents)
        self.textfield.configure(state=current_state)
        self.textfield.edit_modified(False)

    # Context menu event handlers
    def show_context_menu(self, event) -> None:
        selected_items = self.listbox.curselection()
        if len(selected_items) > 1:
            self.context_menu.entryconfig("Save selected items", state=tk.NORMAL)
        else:
            self.context_menu.entryconfig("Save selected items", state=tk.DISABLED)

        try:
            self.context_menu.tk_popup(event.x_root, event.y_root)
        finally:
            self.context_menu.grab_release()

    def open_in_explorer(self) -> None:
        selected_index = self.listbox.curselection()
        if selected_index:
            selected_filename = self.filenames.array[selected_index]
            selected_filename = selected_filename.replace('/', '\\')  # windows specific
            cmd = f'explorer /select,"{selected_filename}"'
            subprocess.Popen(cmd)

    def save_selection(self):
        '''Save the selected items in the listbox to a text file'''
        selected_items = self.listbox.curselection()
        file_path = filedialog.asksaveasfilename(
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")]
        )
        if file_path:
            with open(file_path, 'w', encoding='utf-8') as file:
                for index in selected_items:
                    file.write(self.filenames.array[index] + '\n')


def switch_to_folder(mw: MainWindow, new_folder: Path = None) -> None:
    curfol = config.WorkFolder
    if new_folder is None:
        new_folder = filedialog.askdirectory(initialdir=curfol)
    if new_folder:
        mw.project_folder_label.config(text=new_folder)
        config.add_to_mru(curfol)
        config.set_work_folder(Path(new_folder))
        mw.update_recent_menu()
        mw.dirtree.clear_tree()
        mw.dirtree.load_tree(new_folder)
        if (new_folder / LIST_FILE).exists():
            filenames = load_list_from_text(new_folder / LIST_FILE)
            mw.populate_listbox(filenames)
            mw.clear_editor()


def main():
    mw = MainWindow()
    mw.build_gui()
    mw.top.wait_visibility()
    mw.initialize()
    mw.top.mainloop()


if __name__ == '__main__':
    main()

import tkinter as tk
from tkinter.constants import BOTH
from tkinter import ttk
from tkinter import filedialog
from tkinter import WORD, CHAR, NONE
import threading
import subprocess
from pathlib import Path
import pandas as pd
from bioview.config import Config
from bioview.load_readme import read_file_contents
from bioview.load_readme_list import load_list_from_text
from bioview.save_readme_changes import save_readme_changes
from bioview.scan_readmefiles import scan_readme_files
from bioview.progress_window import ProgressPopup
from bioview.calback_thread import CallbackThread

config = Config(WorkFolder=Path.home())
LIST_FILE = Path('all_readme_files.lst')

mw = None


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


class MainWindow:

    current_filename: Path = None
    progress = None

    def onExit(self):
        exit()

    def __init__(self):
        pass

    def build_gui(self):
        self.top = tk.Tk()

        self.top.title('BioSpace')
        self.top.geometry("1200x700")

        self.top.grid_columnconfigure(0, weight=1)
        self.top.grid_rowconfigure(0, weight=1)

        self.top.option_add('*tearOff', False)
        self.menubar = tk.Menu(self.top)
        self.fileMenu = tk.Menu(self.menubar)

        self.fileMenu.add_command(label='Switch to folder',
                                  command=lambda f=None, window=self: switch_to_folder(window, f))
        self.fileMenu.add_command(label='Open filename listfile',
                                  command=self.open_text_file)
        self.fileMenu.add_command(label='Rescan for readme files',
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

        # Create a PanedWindow
        main_paned_window = ttk.PanedWindow(self.top, orient=tk.HORIZONTAL)
        main_paned_window.pack(expand=True, fill="both")

        # Create left and right frames
        left_frame = ttk.Frame(main_paned_window, width=500)
        right_frame = ttk.Frame(main_paned_window)

        # Add frames to the PanedWindow
        main_paned_window.add(left_frame, weight=1)
        main_paned_window.add(right_frame, weight=1)

        # Add widgets to the frames
        # Create a label for the project folder
        self.project_folder_label = tk.Label(
            left_frame, text="", fg='white', background='red', justify='left')
        self.project_folder_label.pack(side="top", fill="x")

        self.listbox = tk.Listbox(left_frame, selectmode=tk.EXTENDED)

        # Create scrollbars for the listbox
        self.scrollbar_list = tk.Scrollbar(left_frame, orient="vertical")
        self.scrollbar_list_horizontal = tk.Scrollbar(left_frame, orient="horizontal")

        self.scrollbar_list_horizontal.pack(side="bottom", fill="x")
        self.listbox.pack(side="left", fill="both", expand=True)
        self.scrollbar_list.pack(side="right", fill="y")

        # Configure the listbox to use scrollbars
        self.listbox.config(yscrollcommand=self.scrollbar_list.set,
                            xscrollcommand=self.scrollbar_list_horizontal.set)
        self.scrollbar_list.config(command=self.listbox.yview)
        self.scrollbar_list_horizontal.config(command=self.listbox.xview)

        # Create a label for the filename
        self.filename_label = tk.Label(
            right_frame, text="", fg='white', background='red', justify='left')
        self.filename_label.pack(side="top", fill="x")

        # Create a frame for the button bar
        self.button_bar = tk.Frame(right_frame)
        self.button_bar.pack(side="top", fill="x")

        # Add a button to toggle textfield wrap option
        self.toggle_wrap_button = tk.Button(
            self.button_bar, text="Wrapping: Off", command=self.toggle_wrap)
        self.toggle_edit_button = tk.Button(
            self.button_bar, text="Enable Edit", command=self.toggle_edit_event)
        self.save_changes_button = tk.Button(
            self.button_bar, text="Save Changes", command=self.save_changes_event)
        self.toggle_wrap_button.pack(side="left")
        self.toggle_edit_button.pack(side="left")
        self.save_changes_button.pack(side="left")

        self.textfield = tk.Text(right_frame, wrap=NONE, undo=True,
                                 autoseparators=True, state='disabled')
        self.textfield.bind("<<Modified>>", self.modified_flag_changed)
        self.textfield.bind("<Control-s>", self.save_changes_event)

        # Create scrollbars for the textfield
        self.scrollbar_text = tk.Scrollbar(right_frame, orient="vertical")
        self.scrollbar_text_hor = tk.Scrollbar(right_frame, orient="horizontal")
        self.scrollbar_text_hor.pack(side="bottom", fill="x")
        self.textfield.pack(side="left", fill="both", expand=True)
        self.scrollbar_text.pack(side="right", fill="y")

        # Configure the yextfield to use the scrollbar
        self.textfield.config(yscrollcommand=self.scrollbar_text.set,
                              xscrollcommand=self.scrollbar_text_hor.set)

        self.scrollbar_text.config(command=self.textfield.yview)
        self.scrollbar_text_hor.config(command=self.textfield.xview)

        # Create a context menu for the listbox
        self.context_menu = tk.Menu(self.listbox, tearoff=0)
        self.context_menu.add_command(
            label="Open in Explorer", command=self.open_in_explorer)
        self.context_menu.add_command(
            label="Save selected items", command=self.save_selection, state=tk.DISABLED)

        # Bind right-click to show context menu
        self.listbox.bind("<Button-3>", self.show_context_menu)
        self.listbox.bind('<<ListboxSelect>>', self.onListboxSelect)

    def initialize(self):
        folder = config.WorkFolder
        mw.project_folder_label.config(text=folder)
        mw.update_recent_menu()
        if (folder / LIST_FILE).exists():
            filenames = load_list_from_text(folder / LIST_FILE)
            mw.populate_listbox(filenames)
            mw.clear_editor()

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
        self.filename_label.config(text="")
        self.textfield.delete('1.0', tk.END)
        self.textfield.edit_modified(False)

    def modified_flag_changed(self, event) -> None:
        if self.textfield.edit_modified():
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

    def save_changes_event(self, event=None) -> str:
        if not self.textfield.edit_modified:
            return "break"

        # keep backups and save changes
        save_readme_changes(self.current_filename, self.textfield.get('1.0', tk.END))
        self.textfield.edit_modified(False)
        return "break"  # Prevent the default behavior

    def toggle_edit_event(self) -> None:
        '''Toggle the state of the textfield between read-only and editable
        '''
        current_state = self.textfield.cget("state")
        new_state = "normal" if current_state == "disabled" else "disabled"
        self.textfield.config(state=new_state)
        self.toggle_edit_button.config(
            text="Enable Edit" if new_state == "disabled" else "Disable Edit")

    # Listbox event handlers
    # ------------------------

    def populate_listbox(self, filenames: list[Path]) -> None:
        if filenames is None:
            return

        self.filenames = filenames
        # Clear the listbox first
        self.listbox.delete(0, tk.END)

        # Populate listbox with filenames
        for filename in self.filenames:
            self.listbox.insert(tk.END, pretty_print_name(filename, 50))

    def onListboxSelect(self, _) -> None:
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

    # Callback for "save selection..."
    def save_selection(self):
        selected_items = self.listbox.curselection()
        # Implement the logic to save the selected items
        # print(f"Saving selected items: {selected_items}")
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
        if (new_folder / LIST_FILE).exists():
            filenames = load_list_from_text(new_folder / LIST_FILE)
            mw.populate_listbox(filenames)
            mw.clear_editor()


def main():
    global mw
    mw = MainWindow()
    mw.build_gui()
    mw.top.wait_visibility()
    mw.initialize()
    mw.top.mainloop()


if __name__ == '__main__':
    main()

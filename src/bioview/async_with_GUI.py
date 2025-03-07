import datetime
import os
import threading
import queue
import time
import tkinter as tk
from tkinter import Listbox, END
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler


class FileChangeHandler(FileSystemEventHandler):
    def __init__(self, event_queue):
        """
        Initialize the handler with a thread-safe queue to send file events.
        :param event_queue: A queue to communicate file events to the GUI.
        """
        self.event_queue = event_queue

    def on_created(self, event):
        if not event.is_directory:
            self.event_queue.put(("created", event.src_path))

    def on_deleted(self, event):
        if not event.is_directory:
            self.event_queue.put(("deleted", event.src_path))

    def on_modified(self, event):
        if not event.is_directory:
            self.event_queue.put(("modified", event.src_path))

    def on_moved(self, event):
        if not event.is_directory:
            self.event_queue.put(("moved", event.src_path, event.dest_path))


class FolderMonitorThread(threading.Thread):
    def __init__(self, folder_to_monitor, event_queue):
        """
        Initialize the monitoring thread.
        :param folder_to_monitor: The folder to monitor.
        :param event_queue: A queue to communicate file events to the GUI.
        """
        super().__init__(daemon=True)
        self.folder_to_monitor = folder_to_monitor
        self.event_queue = event_queue
        self.observer = Observer()

    def run(self):
        event_handler = FileChangeHandler(self.event_queue)
        self.observer.schedule(
            event_handler, path=self.folder_to_monitor, recursive=True)
        self.observer.start()
        try:
            while True:
                time.sleep(10)  # Keep thread alive
        except KeyboardInterrupt:
            self.observer.stop()
        self.observer.join()

    def stop(self):
        self.observer.stop()


class FileMonitorApp(tk.Tk):
    def __init__(self, folder_to_monitor):
        super().__init__()
        self.title("File Monitor")
        self.geometry("600x400")

        # GUI Components
        self.listbox = Listbox(self, width=160, height=20)
        self.listbox.pack(pady=10)

        # Queue for thread-safe communication
        self.event_queue = queue.Queue()

        # Start monitoring thread
        self.monitor_thread = FolderMonitorThread(folder_to_monitor, self.event_queue)
        self.monitor_thread.start()

        # Periodically check the queue for file events
        self.check_for_updates()

        # Initialize with current files
        begin = datetime.datetime.now()
        print(f'started:{begin}')
        self.update_listbox(self.get_all_files(folder_to_monitor))
        end = datetime.datetime.now()
        print(f'ended:{end}')
        print(f'duration:{end - begin}')
        print('folder_to_monitor:', folder_to_monitor)

    def get_all_files(self, folder):
        """
        Retrieve all files in the folder and its subfolders.
        """
        return [
            os.path.join(dirpath, filename)
            for dirpath, _, filenames in os.walk(folder)
            for filename in filenames  # if 'readme' in filename.lower()
        ]

    def update_listbox(self, files):
        """
        Update the Listbox with the given list of files.
        """
        self.listbox.delete(0, END)
        for file in sorted(files):
            self.listbox.insert(END, file)

    def check_for_updates(self):
        """
        Periodically checks the event queue and updates the Listbox.
        """
        try:
            while not self.event_queue.empty():
                event = self.event_queue.get_nowait()
                self.handle_file_event(event)
        except queue.Empty:
            pass
        self.after(500, self.check_for_updates)  # Schedule next check

    def handle_file_event(self, event):
        """
        Handle a file event from the monitoring thread.
        """
        action = event[0]
        if action == "created":
            print(f"File created: {event[1]}")
            self.listbox.insert(END, event[1])
        elif action == "deleted":
            print(f"File deleted: {event[1]}")
            self.remove_file_from_listbox(event[1])
        elif action == "modified":
            print(f"File modified: {event[1]}")
        elif action == "moved":
            print(f"File moved from {event[1]} to {event[2]}")
            self.remove_file_from_listbox(event[1])
            self.listbox.insert(END, event[2])

    def remove_file_from_listbox(self, filepath):
        """
        Remove a file from the Listbox.
        """
        for idx in range(self.listbox.size()):
            if self.listbox.get(idx) == filepath:
                self.listbox.delete(idx)
                break

    def on_closing(self):
        """
        Stop the monitoring thread and close the application.
        """
        self.monitor_thread.stop()
        self.destroy()


if __name__ == "__main__":
    # folder_to_monitor = "./example_folder"
    folder_to_monitor = 'P:/ITC/Projects2/BioSpace'

    # Ensure the folder exists
    if not os.path.exists(folder_to_monitor):
        os.makedirs(folder_to_monitor)

    app = FileMonitorApp(folder_to_monitor)
    app.protocol("WM_DELETE_WINDOW", app.on_closing)
    app.mainloop()

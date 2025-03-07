import os
import time
import asyncio
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler


class FileChangeHandler(FileSystemEventHandler):
    def __init__(self, tracked_files):
        """
        Initialize the handler with a set of tracked filenames.
        :param tracked_files: A set of filenames to monitor.
        """
        self.tracked_files = set(tracked_files)

    def on_created(self, event):
        if not event.is_directory:
            print(f"File created: {event.src_path}")
            self.tracked_files.add(event.src_path)

    def on_deleted(self, event):
        if not event.is_directory:
            print(f"File deleted: {event.src_path}")
            self.tracked_files.discard(event.src_path)

    def on_modified(self, event):
        if not event.is_directory:
            print(f"File modified: {event.src_path}")

    def on_moved(self, event):
        if not event.is_directory:
            print(f"File moved: from {event.src_path} to {event.dest_path}")
            self.tracked_files.discard(event.src_path)
            self.tracked_files.add(event.dest_path)


async def get_initial_files(root_folder):
    """
    Asynchronously retrieves the list of all files in the folder and its subfolders.
    :param root_folder: The root folder to scan.
    :return: A set of file paths.
    """
    print(f"Initializing file scan for {root_folder}...")
    await asyncio.sleep(1)  # Simulate delay for asynchronous behavior
    initial_files = {
        os.path.join(dirpath, filename)
        for dirpath, _, filenames in os.walk(root_folder)
        for filename in filenames
    }
    print("Initial file scan completed.")
    return initial_files


async def monitor_folder_with_subfolders(root_folder):
    """
    Asynchronously monitors the specified folder and its subfolders for file changes.

    :param root_folder: The folder to monitor.
    """
    initial_files = await get_initial_files(root_folder)

    event_handler = FileChangeHandler(initial_files)
    observer = Observer()
    observer.schedule(event_handler, path=root_folder,
                      recursive=True)  # Enable recursive monitoring
    observer.start()
    print(f"Monitoring changes in {root_folder} and its subfolders...")

    try:
        while True:
            await asyncio.sleep(1)  # Keep the loop running asynchronously
    except asyncio.CancelledError:
        observer.stop()
        print("Stopped monitoring.")
    observer.join()


async def main():
    root_folder = "./example_folder"

    # Create the folder if it doesn't exist
    if not os.path.exists(root_folder):
        os.makedirs(root_folder)

    # Start monitoring the folder
    await monitor_folder_with_subfolders(root_folder)


if __name__ == "__main__":
    asyncio.run(main())

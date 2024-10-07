from pathlib import Path
from typing import List


def scan_readme_files(folder: Path, output_file: Path, silent: bool = True) -> None:
    """
    Recursively scan for filenames that contain 'readme' and have a '.txt' extension
    starting at the folder passed as a parameter. The resulting list of files is
    written to disk.

    :param folder: The root folder to start scanning from.
    :param output_file: The file to write the list of readme files to.
    :param silent: If True, no confirmation is asked and output file will be
      overwritten if it already exist. If False, a confirmation is asked if needed.
    """
    gen = folder.glob('**/*readme*.txt')
    files = [str(file) for file in gen]

    if not silent:
        if output_file.exists():
            print(f"File {output_file} already exists. Overwrite? [y/n]")
            overwrite = input()
            if overwrite.lower() != 'y':
                return

    with open(output_file, 'w') as file:
        for f in files:
            file.write(f + '\n')

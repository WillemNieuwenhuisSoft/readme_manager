from pathlib import Path
import pandas as pd


def load_list_from_text(file_path: Path) -> pd.Series:
    """
    Load a list readme file locations from a text file.

    Args:
        file_path (str): The path to the text file.

    Returns:
        series: a pandas Series containing the file locations of all readme files.
    """
    # Load the text file
    lines = None
    with open(file_path, 'r') as file:
        lines = file.read().splitlines()

    return pd.Series(lines)

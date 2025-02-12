from pathlib import Path


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

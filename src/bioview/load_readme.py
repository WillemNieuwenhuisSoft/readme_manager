import locale
import logging
from pathlib import Path
from bioview.charset_detector import CharsetDetector

log = logging.getLogger(__name__)


def read_file_contents(filename: Path) -> str:
    '''Read the contents of the file with name filename.
       Check for different possible encodings.
    '''
    encod = None
    if filename.stat().st_size == 0:
        return ''

    with open(filename, 'rb') as file:
        encod = CharsetDetector.get_charset(file)

    if not encod:
        log.error(f'Unable to decode file "{filename}".')
        return "Error: Unable to decode file."
    else:
        try:
            with open(filename, 'r', encoding=encod) as file:
                return file.read()
        except UnicodeDecodeError:
            log.warning(
                f'File "{filename}" is not utf-8 encoded. Defaulting to system locale.')
            encod = locale.getencoding()
            with open(filename, 'r', encoding=encod) as file:
                return file.read()

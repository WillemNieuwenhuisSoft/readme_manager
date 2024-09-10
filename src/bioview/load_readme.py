import locale
import logging
from bioview.charset_detector import CharsetDetector

log = logging.getLogger(__name__)


def read_file_contents(filename):
    '''Read the contents of the file with name filename.
       Check for different possible encodings.
    '''
    encod = None
    with open(filename, 'rb') as file:
        encod = CharsetDetector.get_charset(file)

    if not encod:
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

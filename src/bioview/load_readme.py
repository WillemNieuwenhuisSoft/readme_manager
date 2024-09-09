from bioview.charset_detector import CharsetDetector


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
        with open(filename, 'r', encoding=encod) as file:
            return file.read()

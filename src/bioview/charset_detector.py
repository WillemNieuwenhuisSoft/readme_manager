import io
import os


class CharsetDetector:

    @staticmethod
    def get_charset(stream):
        encoding = None
        b4 = bytearray(4)
        count = stream.readinto(b4)
        if count == 4:
            encoding = CharsetDetector.get_encoding_name(b4, count)
        return encoding

    @staticmethod
    def get_encoding_name(b4, count):
        if count < 2:
            return "UTF-8"

        b0, b1 = b4[0], b4[1]
        if b0 == 0xFE and b1 == 0xFF:
            return "UTF-16"
        if b0 == 0xFF and b1 == 0xFE:
            return "UTF-16"

        if count < 3:
            return "UTF-8"

        b2 = b4[2]
        # UTF-8 BOM, windows specific
        if b0 == 0xEF and b1 == 0xBB and b2 == 0xBF:
            return "UTF-8-SIG"

        if count < 4:
            return "UTF-8"

        b3 = b4[3]
        if b0 == 0x00 and b1 == 0x00 and b2 == 0x00 and b3 == 0x3C:
            return "ISO-10646-UCS-4"
        if b0 == 0x3C and b1 == 0x00 and b2 == 0x00 and b3 == 0x00:
            return "ISO-10646-UCS-4"
        if b0 == 0x00 and b1 == 0x00 and b2 == 0x3C and b3 == 0x00:
            return "ISO-10646-UCS-4"
        if b0 == 0x00 and b1 == 0x3C and b2 == 0x00 and b3 == 0x00:
            return "ISO-10646-UCS-4"
        if b0 == 0x00 and b1 == 0x3C and b2 == 0x00 and b3 == 0x3F:
            return "UTF-16BE"
        if b0 == 0x3C and b1 == 0x00 and b2 == 0x3F and b3 == 0x00:
            return "UTF-16LE"
        if b0 == 0x4C and b1 == 0x6F and b2 == 0xA7 and b3 == 0x94:
            return "CP037"

        return "UTF-8"

    @staticmethod
    def get_buffered_reader(file_name):
        charset_name = CharsetDetector.get_charset(
            CharsetDetector.get_input_stream(file_name))
        if charset_name:
            return io.open(file_name, 'r', encoding=charset_name)
        else:
            return io.open(file_name, 'r')

    @staticmethod
    def get_input_stream(file_name):
        if os.path.exists(file_name):
            return open(file_name, 'rb')
        else:
            raise FileNotFoundError(f"'{file_name}' not found on file system.")

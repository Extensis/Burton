import re

import stringextractor

class RC(stringextractor.Base):
    def __init__(self):
        stringextractor.Base.__init__(self)

    def extract_strings_from_filename(self, filename):
        return_values = set([])

        block = "BLOCK"
        value = "VALUE"
        string_file_info = '"StringFileInfo"'

        string_file_info_regex = re.compile(block + " " + string_file_info)

        file = self._open_file(filename)

        in_string_file_info = False
        for line in file.readlines():
            line = line.lstrip()

            if not in_string_file_info:
                if string_file_info_regex.search(line) is not None:
                    in_string_file_info  = True

            else:
                if line.startswith(value):
                    string = line.split()[1]
                    string = string.strip(",")
                    string = string[1:-1]
                    return_values.add(string)

        return return_values

    def _open_file(self, filename):
        return open(filename, "r")

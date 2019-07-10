import codecs
import os
import re
import subprocess
import types
import unicodedata

import burton
from .base import Base
from .util import detect_encoding

class Strings(Base):
    def __init__(self):
        Base.__init__(self)
        self.baseLocalizationRegex = re.compile(
            '\w{3}-\w{2}-\w{3}\.(placeholder|text|title|normalTitle)'
        )

    def extract_strings_from_filename(self, filename):
        return_values = set([])

        def _add_key(key, value):
            if key and key[0] == '"':
                key = key[1:-1]

            if self.baseLocalizationRegex.match(key):
                key = value

            if key and key[0] == '"':
                key = key[1:-1]

            return_values.add(key)

        self._parse(filename, _add_key)

        return return_values

    def extract_mapping_from_filename(self, filename, strip_keys = True):
        string_mapping = burton.StringMapping(filename = filename)

        def _add_mapping(key, value):
            if strip_keys and key and key[0] == '"':
                key = key[1:-1]

            if value and value[0] == '"':
                value = value[1:-1]

            if self.baseLocalizationRegex.match(key):
                key = value

            string_mapping.add_mapping(key, value)

        self._parse(filename, _add_mapping)

        return string_mapping

    def _parse(self, filename, func):
        file, encoding = self._open_file(filename)
        contents = self._strip_comments(file.read())

        in_string_file_info  = False
        incomplete_line      = None

        for line in re.split("\r|\n", contents):
            key   = None
            value = None
            line  = line.rstrip("\r\n")

            assert type(line) is str

            if incomplete_line is not None:
                if incomplete_line.strip().endswith("\\"):
                    line = incomplete_line.strip().rstrip("\\") + line
                else:
                    line = incomplete_line + "\\n" + line

                incomplete_line = None

            if line.strip().endswith("\\"):
                incomplete_line = line
            elif line and not line.strip().endswith(";"):
                incomplete_line = line
            else:
                in_string     = False
                in_variable   = False
                escaping      = 0
                current_token = ""

                for c in line:
                    if in_string or in_variable:
                        current_token = current_token + c

                    if c == '"':
                        if escaping == 0:
                            in_string = not in_string

                            if in_variable:
                                current_token = ""
                                in_variable = False

                            if not in_string:
                                if current_token[-1] != '"':
                                    current_token += '"'

                                if key is None:
                                    key = current_token
                                else:
                                    value = current_token
                                current_token = ""
                            else:
                                current_token = '"'

                    elif c == ";":
                        if not in_string:
                            if key is not None and value is None:
                                value = key

                    elif c == "\\" and escaping == 0:
                        escaping = 2

                    elif self._is_unicode_whitespace(c):
                        if in_variable:
                            if key is None:
                                key = current_token[:-1]
                            current_token = ""
                            in_variable = False

                    elif not in_variable and not in_string and key is None:
                        current_token = c
                        in_variable = True

                    if escaping > 0:
                        escaping -= 1

            if key is not None and value is not None:
                key = key
                value = value
                func(key, value)

        file.close()

    def write_mapping(self, file, mapping):
        sorted_keys = list(mapping.keys())
        sorted_keys.sort()

        for key in sorted_keys:
            if key is not None and mapping[key] is not None:
                value = self._encode(mapping[key])

                quote_key = False
                if key and key[0] == '"':
                    quote_key = True
                    key = key[1:-1]

                key = self._encode(key)

                if quote_key:
                    key = '"' + key + '"'

                file.write(key + ' = "' + value + '";\n')

    def _open_file(self, filename):
        encoding = detect_encoding(open(filename, "rb"))

        # Strings files should always be unicode of some sort.
        # Sometimes chardet guesses UTF-8 wrong.
        if encoding is None or not encoding.lower().startswith("utf"):
            encoding = "utf-8"

        return codecs.open(filename, "r", encoding), encoding

    def _strip_comments(self, contents):
        output                 = u""
        in_string              = False
        in_comment             = False
        in_slash               = False
        in_asterisk            = False
        in_single_line_comment = False
        in_multiline_comment   = False

        for c in contents:
            if c == '"' and not in_comment:
                in_string = not in_string

            elif c == '/' and not in_string:
                if in_slash:
                    in_single_line_comment = True
                    in_comment             = True
                    in_slash               = False
                elif in_asterisk:
                    in_multiline_comment   = False
                    in_comment             = False
                else:
                    in_slash               = True

            elif c == '*' and not in_string:
                if in_comment:
                    in_asterisk            = True
                elif in_slash:
                    in_multiline_comment   = True
                    in_comment             = True
                    in_slash               = False

            elif c in "\r\n" and in_single_line_comment:
                in_single_line_comment     = False
                in_comment                 = False

            if not in_comment:
                if in_slash and c != '/':
                    output += '/'
                    in_slash = False

                if in_asterisk:
                    in_asterisk = False
                elif not in_slash:
                    output += c

        return output

    def _encode(self, str):
        return str.encode('unicode-escape')\
            .decode('utf8')\
            .replace("\"", "\\\"")\
            .replace("\\x", "\\U00")\
            .replace("\\u", "\\U")\
            .replace("\\\\", "\\") # Reverse earlier double-escaping

    def _is_unicode_whitespace(self, c):
        category = unicodedata.category(c)
        return category == "Zs" or category == "Cc"

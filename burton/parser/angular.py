import codecs
import logging
import os
import re
import subprocess
import types
import unicodedata

import burton
from .base import Base
from .util import detect_encoding

class Angular(Base):
    REGEX_PATTERN = re.compile("'\[([^\]]+)\]'\s*:\s*'(.+)'")

    def __init__(self):
        Base.__init__(self)

    def extract_strings_from_filename(self, filename):
        return_values = set([])

        def _add_key(key, value):
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

            string_mapping.add_mapping(key, value)

        self._parse(filename, _add_mapping)

        return string_mapping

    def _parse(self, filename, func):
        file, encoding = self._open_file_for_reading(filename)
        contents = file.read()

        for line in re.split("\r|\n", contents):
            key   = None
            value = None
            line  = line.rstrip("\r\n")

            assert type(line) is str

            results = Angular.REGEX_PATTERN.search(line)

            if results is not None:
                func(results.group(1), results.group(2))

        file.close()

    def translate(
        self,
        input_filename,
        output_directory,
        mapping,
        language,
        language_code,
        should_use_vcs,
        vcs_class,
        proj_file
    ):
        logger = logging.getLogger(burton.logger_name)
        logger.debug("Localizing " + input_filename + " into " + language)

        output_filename = os.path.join(
            output_directory,
            input_filename.replace("english", language.lower()),
        )

        created_file = False

        if not os.path.exists(output_filename):
            created_file = True

        output_file = self._open_file_for_writing(output_filename)

        input_file, encoding = self._open_file_for_reading(input_filename)
        contents = input_file.read()
        input_file.close()

        for line in re.split("\r|\n", contents):
            results = Angular.REGEX_PATTERN.search(line)
            if results is not None:
                key = results.group(1)
                value = results.group(2)
                if value in mapping:
                    value = mapping[value]

                if key is not None and value is not None:
                    line = re.sub(r"'\[[^\]]+\]'", "'[" + self._encode(key) + "]'", line)
                    sub_value = (": '" + self._encode(value) + "'").replace("\\x", "\\\\x").replace("\\u", "\\\\u")
                    line = re.sub(r": '[^\[].+[^\]]'", sub_value, line)
            else:
                line = line.replace(
                    "$translateProvider.translations('en', strings);",
                    "$translateProvider.translations('" + language_code + "', strings);"
                )

            output_file.write(line + "\n")

        output_file.close()

        if should_use_vcs:
            vcs_class.add_file(output_filename)

    def _open_file_for_reading(self, filename):
        encoding = detect_encoding(open(filename, "rb"))

        # Strings files should always be unicode of some sort.
        # Sometimes chardet guesses UTF-8 wrong.
        if encoding is None or not encoding.lower().startswith("utf"):
            encoding = "utf-8"

        return codecs.open(filename, "r", encoding), encoding

    def _open_file_for_writing(self, filename):
        return open(filename, "w")

    def _encode(self, str):
        str = str.encode('unicode-escape').decode('utf8').replace("'", "\\'")
        return str

import codecs
import logging
import os
import re
import types

import burton
from .base import Base

class Properties(Base):
    def __init__(self):
        Base.__init__(self)

    def extract_strings_from_filename(self, filename):
        return_values = set([])

        def _add_key(key, value):
            return_values.add(key)

        self._parse(filename, _add_key)

        return return_values

    def extract_mapping_from_filename(self, filename):
        string_mapping = burton.StringMapping(filename = filename)

        def _add_mapping(key, value):
            string_mapping.add_mapping(key, value)

        self._parse(filename, _add_mapping)

        return string_mapping

    def _parse(self, filename, func):
        file = self._open_file_for_reading(filename)
        sep_regex = re.compile(":|=")

        incomplete_line     = None
        for line in file.readlines():
            key   = None
            value = None
            line  = line.rstrip("\r\n")

            if incomplete_line is not None:
                if incomplete_line.endswith("\\"):
                    line = incomplete_line.rstrip("\\") + line

                incomplete_line = None

            if line.endswith("\\"):
                incomplete_line = line
            elif line.lstrip().startswith("#") or line.lstrip().startswith("!"):
                pass
            else:
                parts = line.split(None, 1)
                if len(parts) < 2 or sep_regex.search(parts[0]) is not None:
                    parts = re.split(" |:|=", line, 1)
                else:
                    parts[0] = parts[0].rstrip(":=")
                    parts[1] = parts[1].lstrip(":=")

                if len(parts) == 2:
                    key   = parts[0].rstrip()
                    value = parts[1].lstrip()
            if key is not None and value is not None:
                func(key, value)

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

        output_directory = os.path.join(output_directory, language_code)
        if not os.path.exists(output_directory):
            os.mkdir(output_directory)
            logger.error("Created new directory " + output_directory)

        output_filename = None
        if input_filename.endswith(".properties"):
            input_mapping = \
              self.extract_string_mapping_from_files(
                [ input_filename ]
              ).string_mapping_dict

            output_filename = os.path.join(
                output_directory,
                os.path.basename(input_filename)
            )

            output_file_mapping = { }

            for key in input_mapping:
                if input_mapping[key] is not None and \
                  input_mapping[key] in mapping:
                    output_file_mapping[key] = mapping[input_mapping[key]]
                else:
                    output_file_mapping[key] = input_mapping[key]

            file = self._open_file_for_writing(output_filename)
            self.write_mapping(file, output_file_mapping)

            file.close()

            if should_use_vcs:
                vcs_class.add_file(output_filename)

        return output_filename

    def write_mapping(self, file, mapping):
        for key in mapping:
            if key is not None and mapping[key] is not None:
                value = mapping[key]
                file.write(key + ' ' + value + '\n')

    def _open_file_for_reading(self, filename):
        return codecs.open(filename, "r", "utf-8")

    def _open_file_for_writing(self, filename):
        return codecs.open(filename, "w", "utf-8")

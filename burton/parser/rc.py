import codecs
import logging
import os
import re
import types

import burton
from .base import Base
from .util import detect_encoding

class RC(Base):
    string_table_token = "STRINGTABLE"
    begin_token        = "BEGIN"
    end_token          = "END"
    value_token        = "VALUE"

    tokens_with_localizable_strings = { "AUTO3STATE", "AUTOCHECKBOX",
        "AUTORADIOBUTTON", "CAPTION", "CHECKBOX", "CONTROL", "CTEXT",
        "DEFPUSHBUTTON", "GROUPBOX", "ICON", "LTEXT", "MENUITEM", "PUSHBOX",
        "PUSHBUTTON", "RADIOBUTTON", "RTEXT", "STATE3",
    }

    string_file_infos = { "Comments", "CompanyName",
        "FileDescription", "FileVersion", "InternalName", "LegalCopyright",
        "LegalTrademarks", "LegalTrademarks", "OriginalFilename",
        "PrivateBuild", "ProductName", "ProductVersion", "SpecialBuild",
    }

    version_strings = { "LegalCopyright", "FileVersion", "ProductVersion", }

    def __init__(self):
        Base.__init__(self)

    def _filter_filenames(self, filenames):
        filtered_files = []

        for filename in filenames:
            parts = os.path.basename(filename).split(".")
            if len(parts) <= 2:
                filtered_files.append(filename)

        return filtered_files

    def extract_strings_from_filename(self, filename):
        return set(
            self.extract_mapping_from_filename(filename).\
            string_mapping_dict.keys()
        )

    def extract_mapping_from_filename(self, filename):
        string_mapping = burton.StringMapping(filename = filename)

        def _add_mapping(key, value, line):
            if key is not None and value is not None and \
              key not in RC.string_file_infos:
                string_mapping.add_mapping(key, value)

        self._parse(filename, _add_mapping)

        return string_mapping

    def _parse(self, filename, func):
        file, encoding = self._open_file(filename)

        in_string_table = False
        begin_level     = 0
        incomplete_line = None

        # We can't use codecs or readlines() due to a bug in Python's handling
        # of UTF-16 files on Windows
        lines = file.read().replace("\r\n", "\n").split("\n")
        for line in lines:
            orig_line = line
            line = line.lstrip()
            key   = None
            value = None
            line  = line.rstrip("\r\n")

            if not (line.startswith("#") or line.startswith("//")):
                assert(type(line) == str)

                if incomplete_line is not None:
                    line = incomplete_line + line
                    incomplete_line = None

                if line.strip().endswith("\\"):
                    incomplete_line = line.strip().rstrip("\\")
                elif in_string_table and \
                  line not in ( RC.begin_token, RC.end_token ) and \
                  len(line.split(None,  1)) == 1:
                    incomplete_line = line + " "
                else:
                    line = line.replace('""', '\\"')

                    parts = line.split(None, 1)
                    if len(parts) == 2:
                        if in_string_table:
                            key = parts[0]
                            value = self._parse_string(parts[1])
                        elif parts[0] in RC.tokens_with_localizable_strings:
                            key = self._parse_string(parts[1])
                            value = key
                        elif parts[0] == RC.value_token:
                            key = self._parse_string(parts[1])
                            if key in RC.string_file_infos:
                                parts[1] = \
                                    parts[1][len(key) + 2:].lstrip(",").strip()
                                value = self._parse_string(parts[1])

                    elif len(parts) == 1:
                        if line == RC.string_table_token:
                            in_string_table = True
                        elif in_string_table:
                            if line == RC.begin_token:
                                begin_level += 1
                            elif line == RC.end_token:
                                begin_level -= 1
                                if begin_level == 1:
                                    in_string_table = False

            func(key, value, orig_line)

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
        parts = os.path.basename(input_filename).split(".")
        if len(parts) > 2:
            return input_filename

        logger = logging.getLogger(burton.logger_name)
        logger.debug("Localizing " + input_filename + " into " + language)

        output_filename = None

        if not os.path.exists(output_directory):
            os.mkdir(output_directory)

        if input_filename.endswith(".rc"):
            input_keys = self.extract_strings_from_filename(
                input_filename
            )

            output_filename = os.path.splitext(
                os.path.basename(input_filename)
            )[0]
            output_filename = os.path.join(
                output_directory,
                output_filename + "." + language_code + ".rc"
            )

            created_file = False

            if not os.path.exists(output_filename):
                created_file = True

            output_file = self._open_file_for_writing(output_filename)

            def _print_line(key, value, line):
                if value is not None and value in mapping and \
                  mapping[value] is not None:
                    line = line.replace('""', '"')
                    translation = mapping[value].replace('"', '\\"')
                    line = line.replace(
                        '"' + value + '"',
                        '"' + translation + '"'
                    )

                output_file.write(self._encode(line.rstrip()) + "\r\n")

            self._parse(input_filename, _print_line)

            output_file.close()

            if should_use_vcs:
                vcs_class.add_file(output_filename)

        return output_filename

    def _parse_string(self, str):
        return_value = ""
        last_token = ""
        for current_token in str:
            if last_token == "":
                if current_token != '"':
                    return None
                else:
                    last_token = current_token
            elif current_token == '"':
                if last_token != "\\":
                    return return_value
                else:
                    return_value += "\""
                last_token = current_token
            elif current_token == "\\":
                if last_token == "\\":
                    return_value += "\\"
                    last_token = "\\\\"
                else:
                    last_token = "\\"
            else:
                if last_token == "\\":
                    return_value += last_token
                return_value += current_token
                last_token = current_token

        return None

    def _encode(self, str):
        str = str.replace('\\"', '""')
        return str

    def _open_file(self, filename):
        encoding = detect_encoding(open(filename, "rb"))
        return open(filename, "r"), encoding

    def _open_file_for_writing(self, filename):
        return codecs.open(filename, "w", "utf_16")

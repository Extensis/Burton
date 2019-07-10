import logging
import lxml.etree
import os

import burton
from .base import Base
from .util import filter_string

class StringsDict(Base):
    plist_tag  = 'plist'
    key_tag    = 'key'
    dict_tag   = 'dict'
    string_tag = 'string'
    valid_keys = [ 'zero', 'one', 'two', 'few', 'many', 'other' ]

    def __init__(self):
        Base.__init__(self)

    def extract_strings_from_filename(self, filename):
        return set(
            self.extract_mapping_from_filename(filename).\
            string_mapping_dict.keys()
        )

    def extract_mapping_from_filename(self, filename):
        string_mapping = burton.StringMapping(filename = filename)

        tree = lxml.etree.fromstring(self._read_file(filename))

        def _add_mapping(str, category, node):
            string_mapping.add_mapping(str, str)

        self._parse(tree, _add_mapping)

        return string_mapping

    def _parse(self, tree, func):
        for node in tree:
            if node.tag == StringsDict.dict_tag:
                for subnode in node.findall(StringsDict.dict_tag):
                    dict = subnode.find(StringsDict.dict_tag)
                    if dict is not None:
                        valid_key = False
                        category = None
                        for entry in dict:
                            if entry.tag == StringsDict.key_tag:
                                category = entry.text
                                valid_key = category in StringsDict.valid_keys
                            elif entry.tag == StringsDict.string_tag:
                                if valid_key:
                                    func(entry.text, category, entry)
                                valid_key = False

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

        if input_filename.endswith(".stringsdict"):
            input_keys = self.extract_strings_from_filename(
                input_filename
            )

            output_filename = os.path.join(
                output_directory,
                os.path.basename(input_filename)
            )

            created_file = False

            if not os.path.exists(output_filename):
                created_file = True

            tree = lxml.etree.fromstring(self._read_file(input_filename))

            def _rewrite_mapping(value, category, node):
                if value in mapping:
                    node.text = mapping[value]

            self._parse(tree, _rewrite_mapping)

            file = self._open_file_for_writing(output_filename)
            file.write(b"<?xml version=\"1.0\" encoding=\"UTF-8\"?>\n")
            lxml.etree.ElementTree(element = tree).write(
                file,
                xml_declaration = False,
                pretty_print = True,
                encoding = "utf-8"
            )

            if should_use_vcs:
                vcs_class.add_file(output_filename)

        return output_filename

    def _read_file(self, filename):
        fp = open(filename, "rb")
        return_value = fp.read()
        fp.close()
        return return_value

    def _open_file_for_writing(self, filename):
        return open(filename, "wb")

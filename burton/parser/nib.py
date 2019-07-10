import lxml.etree
import os
import subprocess

from .base import Base

import burton

class NIB(Base):
    def __init__(self):
        Base.__init__(self)

    def _filter_filenames(self, filenames):
        filtered_filenames = []
        for filename in filenames:
            parts = filename.rpartition(os.sep)
            if parts[0].endswith(".nib") and parts[-1].endswith("nib"):
                filtered_filenames.append(parts[0])
            else:
                filtered_filenames.append(filename)

        return list(set(filtered_filenames))

    def extract_strings_from_filename(self, filename):
        return_values = set([])

        localizable_key = "com.apple.ibtool.document.localizable-strings"
        dict_tag        = "dict"
        key_tag         = "key"
        string_tag      = "string"

        xml_contents = self._get_plist_from_nib_file(filename)
        tree = lxml.etree.fromstring(xml_contents)

        main_dict = tree.find(dict_tag)
        localizable_dict = None

        for child_index in range(0, len(main_dict)):
            child = main_dict[child_index]
            if child.tag == key_tag and child.text == localizable_key:
                localizable_dict = main_dict[child_index + 1]
                break

        if localizable_dict is not None:
            for node in localizable_dict.findall(dict_tag):
                strings = node.findall(string_tag)
                for string in strings:
                    string = string.text
                    if string is not None and len(string) > 0:
                        return_values.add(string.replace("\n", "\\n"))

        return return_values

    def extract_mapping_from_filename(self, filename):
        string_mapping = burton.StringMapping(filename = filename)

        for string in self.extract_strings_from_filename(filename):
            string_mapping.add_mapping(string, string)

        return string_mapping

    def _get_plist_from_nib_file(self, filename):
        return subprocess.Popen(
            [ "ibtool", "--localizable-strings", filename ],
            stdout = subprocess.PIPE,
            stderr = None,
        ).stdout.read()

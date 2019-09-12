import lxml.etree
import subprocess

import stringextractor

class NIB(stringextractor.Base):
    def __init__(self):
        stringextractor.Base.__init__(self)

    def extract_strings_from_files(self, filenames):
        filtered_filenames = []
        for filename in filenames:
            if filename.endswith("designable.nib") or \
               filename.endswith("keyedobjects.nib"):
                filtered_filenames.append(filename.rpartition("/")[0])
            else:
                filtered_filenames.append(filename)

        return stringextractor.Base.extract_strings_from_files(
            self,
            filtered_filenames
        )

    def extract_strings_from_filename(
        self,
        filename,
        additional_function_names = []
    ):
        return_values = set([])

        localizable_key = "com.apple.ibtool.document.localizable-strings"
        dict_tag        = "dict"
        key_tag         = "key"
        string_tag      = "string"

        tree = lxml.etree.fromstring(self._get_plist_from_nib_file(filename))

        main_dict = tree.find(dict_tag)
        localizable_dict = None

        for child_index in range(0, len(main_dict)):
            child = main_dict[child_index]
            if child.tag == key_tag and child.text == localizable_key:
                localizable_dict = main_dict[child_index + 1]
                break

        if localizable_dict is not None:
            for node in localizable_dict.findall(dict_tag):
                string = node.find(string_tag).text
                if len(string) > 0:
                    return_values.add(string)

        return return_values

    def _get_plist_from_nib_file(self, filename):
        return subprocess.Popen(
            [ "ibtool", "--localizable-strings", filename ],
            stdout = subprocess.PIPE,
            stderr = subprocess.STDOUT,
        ).stdout.read()

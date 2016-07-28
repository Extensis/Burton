import logging

import burton
import parser

class StringMapping(object):
    """The StringMapping class represents a mapping between localizable strings
    and their native-language translations.

    The class takes care of detecting duplicate localizable strings, both within
    a single mapping file and between mapping files. Additionally, it tracks
    whether these duplicated strings have the same native-language translations.
    """

    def __init__(self, filename = "reference mapping"):
        object.__init__(self)
        self.filename       = filename
        self._string_dict   = { }
        self._filename_dict = { }

    def __iter__(self):
        for key in self._string_dict:
            yield key

    def get_string(self, key):
        """Returns the native-language translation mapped to key"""
        return self._string_dict.get(key, None)

    def add_filenames(self, key, filenames):
        self._filename_dict[key] = self._filename_dict.get(key, [])
        self._filename_dict[key].extend(filenames)

    def get_filenames(self, key):
        """Returns the first filename which contained the localizable string"""
        return self._filename_dict.get(key, [ self.filename ])

    def get_string_mapping_dict(self):
        """Returns a dictionary containing a copy of the string mapping. The
        dictionary is safe to modify without changing this instance's mapping,
        and is useful for inspecting the final output of combined mappings.
        """
        return self._string_dict.copy()

    def add_mapping(self, key, value):
        """Adds a localizable string and its native-language translation, and
        logs errors if there are duplicates. This method is used to build a
        mapping from a single file, not to combine files. See combine_with"""
        key   = parser.filter_string(key)
        value = parser.filter_string(value)

        if key not in self._string_dict:
            self._string_dict[key] = value

        self.add_filenames(key, [ self.filename ])

    def delete_mapping(self, key):
        if key in self._string_dict:
            del self._string_dict[key]
        if key in self._filename_dict:
            del self._filename_dict[key]

    def combine_with(self, other_mapping):
        """Combines two file mappings, keeping track of which file which mapping
        came from, and logs an error if there are duplicates between files"""
        for key in other_mapping:
            if key not in self._string_dict:
                self._string_dict[key] = other_mapping.get_string(key)

            self.add_filenames(key, other_mapping.get_filenames(key))

    string_mapping_dict = property(get_string_mapping_dict, None)

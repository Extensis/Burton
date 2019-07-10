import logging

import burton
from .util import filter_string, replace_params

class Base(object):
    def __init__(self):
        object.__init__(self)

    def extract_strings_from_files(self, filenames, strings_to_ignore = []):
        logger           = logging.getLogger(burton.logger_name)
        raw_strings      = set([])
        filtered_strings = set([])

        for filename in set(self._filter_filenames(filenames)):
            logger.debug("Extracting strings from " + filename)
            raw_strings.update(self.extract_strings_from_filename(filename))

        for string in raw_strings:
            filtered_string = filter_string(string)
            replaced_string, params = replace_params(string)
            if replaced_string not in strings_to_ignore:
                filtered_strings.add(filtered_string)

        return filtered_strings

    def extract_string_mapping_from_files(
        self,
        filenames,
        strings_to_ignore = []
    ):
        logger            = logging.getLogger(burton.logger_name)
        reference_mapping = burton.StringMapping()

        for filename in set(self._filter_filenames(filenames)):
            logger.debug("Extracting string mapping from " + filename)
            reference_mapping.combine_with(
                self.extract_mapping_from_filename(filename)
            )

        strings_to_remove = []
        for string in reference_mapping:
            replaced_key, params = replace_params(string)
            if replaced_key in strings_to_ignore:
                strings_to_remove.append(string)
            elif reference_mapping.get_string(string) is not None:
                replaced_value, params = \
                  replace_params(reference_mapping.get_string(string))
                if replaced_value in strings_to_ignore:
                    strings_to_remove.append(string)

        for string in strings_to_remove:
            reference_mapping.delete_mapping(string)

        return reference_mapping

    def _filter_filenames(self, filenames):
        return filenames

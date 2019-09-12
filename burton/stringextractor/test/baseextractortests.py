import mock
import unittest

import stringextractor

class BaseExtractorTests(unittest.TestCase):
    def test_extract_strings_from_files(self):
        individual_file_strings = [
            [ "SomeString",      "SomeOtherString",    ],
            [ "SomeOtherString", "StillAnotherString", ],
        ]

        extractor = stringextractor.Base()
        extractor.extract_strings_from_filename = mock.Mock(side_effect =
            lambda x: individual_file_strings.pop()
        )

        self.assertEquals(
            extractor.extract_strings_from_files([ "file1", "file2" ]),
            set([ "SomeString", "SomeOtherString", "StillAnotherString" ])
        )

    def test_extract_strings_from_files_filters_strings(self):
        extractor = stringextractor.Base()
        extractor.extract_strings_from_filename = mock.Mock(return_value =
            [ "SomeString", "SomeOtherString", "StillAnotherString" ],
        )
        extractor._filter_string = mock.Mock(return_value = "FilteredString")

        self.assertEquals(
            extractor.extract_strings_from_files([ "file1", "file2" ]),
            set([ "FilteredString", "FilteredString", "FilteredString" ])
        )

    def test_filter_string_unescapes_slashes(self):
        extractor = stringextractor.Base()
        self.assertEquals(
            extractor._filter_string(r"There\'s no escape!"),
            "There's no escape!"
        )

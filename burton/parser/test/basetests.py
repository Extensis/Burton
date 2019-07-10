import mock
import unittest

import burton
import parser

class BaseTests(unittest.TestCase):
    def test_extract_strings_from_files(self):
        individual_file_strings = [
            [ u"SomeString",      u"SomeOtherString",    ],
            [ u"SomeOtherString", u"StillAnotherString", ],
            [ u"SomeString",      u"IgnoredString",      ],
        ]

        extractor = burton.parser.Base()
        extractor.extract_strings_from_filename = mock.Mock(side_effect =
            lambda filename: individual_file_strings.pop()
        )

        self.assertEquals(
            extractor.extract_strings_from_files(
                [ "file1", "file2", "file3"],
                [ "IgnoredString" ]
            ),
            set([ u"SomeString", u"SomeOtherString", u"StillAnotherString" ])
        )

    @mock.patch.object(burton.parser.base, "filter_string")
    def test_extract_strings_from_files_filters_strings(self, mock_filter_func):
        extractor = burton.parser.Base()
        extractor.extract_strings_from_filename = mock.Mock(return_value =
            [ u"SomeString", u"SomeOtherString", u"StillAnotherString" ],
        )
        mock_filter_func.return_value = u"FilteredString"

        self.assertEquals(
            extractor.extract_strings_from_files([ "file1", "file2" ]),
            set([ u"FilteredString", u"FilteredString", u"FilteredString" ])
        )

    def test_extract_mapping_from_files(self):
        mapping1 = burton.StringMapping(filename = "1.txt")
        mapping1.add_mapping(u"SomeKey", u"Translation for some key")

        mapping2 = burton.StringMapping(filename = "2.txt")
        mapping2.add_mapping(
            u"SomeOtherKey", u"Translation for the other string",
        )
        mapping2.add_mapping(
            u"IgnoredString", u"This is an ignored string",
        )
        mapping2.add_mapping(
            u"IgnoredString2", u"IgnoredString{0}",
        )

        individual_file_mappings = [ mapping1, mapping2 ]
        extractor = burton.parser.Base()
        extractor.extract_mapping_from_filename = mock.Mock(side_effect =
            lambda filename: individual_file_mappings.pop()
        )

        final_mapping = extractor.extract_string_mapping_from_files(
            [ "file1", "file2" ],
            [ "IgnoredString", "IgnoredString{0}" ],
        )

        self.assertEquals(
            final_mapping.string_mapping_dict, {
                u"SomeKey"      : u"Translation for some key",
                u"SomeOtherKey" : u"Translation for the other string",
            }
        )

import mock
import os
import types
import unittest

from io import StringIO

from burton import parser

class StringsTests(unittest.TestCase):
    sample_strings = \
"""// "This/is" = "a comment";
"SomeString" = "Translation for some string";
/* Other comment format */
"SomeOtherString" = "Translation for the \\
other string"; // End comment
"A string that translates to itself"; /* Comment at line's end */
"YetAnotherString" = "Yet another
string";
"Could not open font \\"{0}\\"." = "Could not open font \\"{0}\\".";
InfoPlistVariable = /* Middle comment */ "Info Plist Variable";
"XTK-jj-3ot.text" = "base localization string";
"""

    def test_open_file(self):
        extractor = parser.Strings()
        dir = os.path.dirname(__file__)
        file = os.path.join(dir, "test.strings")

        self.assertEquals(
            extractor._open_file(file)[0].read(),
            StringsTests.sample_strings
        )

    def test_extract_strings_from_filename(self):
        extractor = parser.Strings()
        extractor._open_file = mock.Mock(return_value = (
            StringIO(StringsTests.sample_strings),
            "utf_8"
        ))

        strings = extractor.extract_strings_from_filename("some_file")

        self.assertEquals(
            strings,
            set([
                u"SomeString",
                u"SomeOtherString",
                u"A string that translates to itself",
                u"YetAnotherString",
                u"Could not open font \\\"{0}\\\".",
                u"InfoPlistVariable",
                u"base localization string"
            ])
        )

    def test_extract_mapping_from_filename(self):
        extractor = parser.Strings()
        extractor._open_file = mock.Mock(return_value = (
            StringIO(StringsTests.sample_strings),
            "utf_8"
        ))

        string_mapping = extractor.extract_mapping_from_filename("some_file")

        self.assertEquals(
            string_mapping.string_mapping_dict,
            {
                u"SomeString" : u"Translation for some string",
                u"SomeOtherString" : u"Translation for the other string",
                u"A string that translates to itself" :
                    u"A string that translates to itself",
                u"YetAnotherString" : u"Yet another\\nstring",
                u"Could not open font \"{0}\"." :
                    u"Could not open font \"{0}\".",
                u"InfoPlistVariable" : u"Info Plist Variable",
                u"base localization string": u"base localization string"
            }
        )

        for key, value in string_mapping.string_mapping_dict.items():
            self.assertEquals(type(key), str)
            self.assertEquals(type(value), str)

    def test_write_mapping(self):
        file = StringIO()
        parser.Strings().write_mapping(file, {
            u'"SomeString"' : u'Translation for some string',
            u'"SomeOtherString"' : u'Can\'t "quote" this!'
        })

        self.assertEquals(
            file.getvalue(),
            """"SomeOtherString" = "Can\'t \\"quote\\" this!";
"SomeString" = "Translation for some string";
"""
        )

        file.close()

    def test_write_mapping_does_not_over_escape_newline(self):
        file = StringIO()
        parser.Strings().write_mapping(file, {
            u'"SomeString"' : u'String with a \r\n newline',
        })

        # This test is a little deceptive because we have to escape the python
        # string. The real string has only one backslash for each escaped
        # character. It is "String with a \r\n newline".
        self.assertEquals(
            file.getvalue(),
            """"SomeString" = "String with a \\r\\n newline";
"""
        )

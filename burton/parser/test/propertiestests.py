import codecs
import mock
import os
from burton import stringmapping
import types
import unittest

from burton import parser
from . import teststringio

class PropertiesTests(unittest.TestCase):
    sample_file = \
"""SomeString = Translation for some string
# This is a comment
SomeOtherString:Translation for the \\
other string
! This is another comment
YetAnotherString \\ Yet another string
CouldNotOpenFont Could not open font "{0}".
"""

    def test_open_file_for_reading(self):
        extractor = parser.Properties()
        dir = os.path.dirname(__file__)
        file = os.path.join(dir, "test.properties")

        self.assertEquals(
            extractor._open_file_for_reading(file).read(),
            PropertiesTests.sample_file
        )

    @mock.patch.object(codecs, "open")
    def test_open_file_for_writing(self, open_func):
        parser.Properties()._open_file_for_writing("test_filename")
        open_func.assert_called_with("test_filename", "w", "utf-8")

    def test_extract_strings_from_filename(self):
        extractor = parser.Properties()
        extractor._open_file_for_reading = mock.Mock(return_value = (
            teststringio.TestStringIO(None, PropertiesTests.sample_file)
        ))

        self.assertEquals(
            extractor.extract_strings_from_filename("some_file"),
            set([
                u"SomeString",
                u"SomeOtherString",
                u"YetAnotherString",
                u"CouldNotOpenFont"
            ])
        )

    def test_extract_mapping_from_filename(self):
        extractor = parser.Properties()
        extractor._open_file_for_reading = mock.Mock(return_value =
            teststringio.TestStringIO(None, PropertiesTests.sample_file),
        )

        string_mapping = extractor.extract_mapping_from_filename("some_file")

        self.assertEquals(
            string_mapping.string_mapping_dict,
            {
                u"SomeString"       : u"Translation for some string",
                u"SomeOtherString"  : u"Translation for the other string",
                u"YetAnotherString" : u"\\ Yet another string",
                u"CouldNotOpenFont" : u"Could not open font \"{0}\"."
            }
        )

        for key, value in string_mapping.string_mapping_dict.items():
            self.assertEquals(type(key), str)
            self.assertEquals(type(value), str)

    def test_write_mapping(self):
        file = teststringio.TestStringIO()
        parser.Properties().write_mapping(file, {
            u"SomeString" : u"Translation for some string",
        })

        self.assertEquals(
            file.getvalue(),
            """SomeString Translation for some string
"""
        )

        file.close()

    def test_write_mapping_does_not_over_escape_newline(self):
        file = teststringio.TestStringIO()
        parser.Properties().write_mapping(file, {
            u"SomeString" : u"String with a \\r\\n newline",
        })

        # This test is a little deceptive because we have to escape the python
        # string. The real string has only one backslash for each escaped
        # character. It is "String with a \r\n newline".
        self.assertEquals(
            file.getvalue(),
            """SomeString String with a \\r\\n newline
"""
        )

    @mock.patch.object(os, "mkdir")
    def test_translate(self, mkdir_func):
        test_parser = parser.Properties()
        test_file   = teststringio.TestStringIO()
        vcs_class   = mock.Mock()

        test_parser._open_file_for_writing = mock.Mock(return_value = test_file)

        string_mapping = stringmapping.StringMapping()
        string_mapping.add_mapping("SomeString", u"Translation for some string")
        string_mapping.add_mapping("NewString",  u"Untranslated string")
        test_parser.extract_string_mapping_from_files = mock.Mock(
            return_value = string_mapping
        )

        output_filename = test_parser.translate(
            "strings.properties",
            "locale",
            {
                u"Translation for some string" :
                    u"Traduzione di Bablefish per questa stringa",
                u"Extra string" : u"Not in file to localize",
            },
            "Italian",
            "it_IT",
            True,
            vcs_class,
            None
        )

        mkdir_func.assert_called_with(
            os.path.join("locale", "it_IT")
        )
        test_parser._open_file_for_writing.assert_called_with(
            os.path.join("locale", "it_IT", "strings.properties")
        )

        self.assertEquals(
            output_filename,
            os.path.join("locale", "it_IT", "strings.properties")
        )

        self.assertEquals(
            test_file.getvalue(),
            """SomeString Traduzione di Bablefish per questa stringa
NewString Untranslated string\n"""
        )

        vcs_class.add_file.assert_called_with(
            os.path.join("locale", "it_IT", "strings.properties")
        )

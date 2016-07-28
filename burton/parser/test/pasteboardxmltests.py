import mock
import os
import types
import unittest

import parser
import teststringio

class PasteboardXMLTests(unittest.TestCase):
    sample_xml = \
"""<manifest>
    <identifier>test-identifier</identifier>
    <category>English Category</category>
    <title>English Title</title>
    <version>1</version>
    <filename>test.html</filename>
    <imageFilename>test.png</imageFilename>
    <elements>
        <name>English Test Element 1</name>
        <element>test-element1</element>
        <name>English Test Element 2</name>
        <element>test-element2</element>
    </elements>
</manifest>
"""

    sample_translated_xml = \
"""<manifest>
    <identifier>test-identifier</identifier>
    <category>Translated Category</category>
    <title>Translated Title</title>
    <version>1</version>
    <filename>test.html</filename>
    <imageFilename>test.png</imageFilename>
    <elements>
        <name>Translated Test Element 1</name>
        <element>test-element1</element>
        <name>Translated Test Element 2</name>
        <element>test-element2</element>
    </elements>
</manifest>
"""

    def test_filter_filenames(self):
        extractor = parser.PasteboardXML()

        self.assertEquals(
            extractor._filter_filenames(
                [ "test-en.xml", "test-jp.xml" ]
            ),
            [ "test-en.xml" ]
        )

    def test_read_file(self):
        extractor = parser.PasteboardXML()
        dir = os.path.dirname(__file__)
        file = os.path.join(dir, "pasteboard-test-en.xml")

        self.assertEquals(
            extractor._read_file(file),
            PasteboardXMLTests.sample_xml
        )

    def test_extract_strings_from_filename(self):
        extractor = parser.PasteboardXML()
        extractor._read_file = mock.Mock(
            return_value = PasteboardXMLTests.sample_xml
        )

        extracted_strings = extractor.extract_strings_from_filename("some_file")

        self.assertEquals(
            extracted_strings,
            set([
                u"English Category",
                u"English Title",
                u"English Test Element 1",
                u"English Test Element 2",
            ])
        )

        for string in extracted_strings:
            self.assertEquals(type(string), types.UnicodeType)

    def test_extract_mapping_from_filename(self):
        extractor = parser.PasteboardXML()
        extractor._read_file = mock.Mock(
            return_value = PasteboardXMLTests.sample_xml
        )

        string_mapping = extractor.extract_mapping_from_filename("some_file")

        self.assertEquals(
            string_mapping.string_mapping_dict,
            {
                u"English Category"       : u"English Category",
                u"English Title"          : u"English Title",
                u"English Test Element 1" : u"English Test Element 1",
                u"English Test Element 2" : u"English Test Element 2",
            }
        )

        for key, value in string_mapping.string_mapping_dict.iteritems():
            self.assertEquals(type(key), types.UnicodeType)
            self.assertEquals(type(value), types.UnicodeType)

    @mock.patch.object(os, "mkdir")
    def test_translate(self, mkdir_func):
        xml_parser = parser.PasteboardXML()
        vcs_class = mock.Mock()
        xml_parser._read_file = mock.Mock(
            return_value = PasteboardXMLTests.sample_xml
        )
        test_file = teststringio.TestStringIO()

        xml_parser._open_file_for_writing = mock.Mock(return_value = test_file)

        self.assertEquals(
            xml_parser.translate(
                "pasteboard-test-en.xml",
                "Resources",
                {
                    u"English Category"       : u"Translated Category",
                    u"English Title"          : u"Translated Title",
                    u"English Test Element 1" : u"Translated Test Element 1",
                    u"English Test Element 2" : u"Translated Test Element 2",
                },
                "Japanese",
                "jp",
                True,
                vcs_class
            ),
            os.path.join("Resources", "pasteboard-test-jp.xml")
        )

        mkdir_func.assert_called_with(
            "Resources"
        )

        self.assertEquals(
            test_file.getvalue(),
            PasteboardXMLTests.sample_translated_xml
        )

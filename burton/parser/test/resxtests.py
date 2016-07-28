import mock
import os
import types
import unittest

import parser
import teststringio

class RESXTests(unittest.TestCase):
    sample_resx = \
"""<root>
    <data name="&gt;&gt;someString.Name" xml:space="preserve">
        <value>SomeString</value>
    </data>
    <data name="SomeString.Text" xml:space="preserve">
        <value>Translation for some string</value>
    </data>
    <data name="SomeOtherString" xml:space="preserve">
        <value>Translation for the other string</value>
    </data>
    <data name="&gt;&gt;$this.Name" xml:space="preserve">
        <value>YetAnotherString</value>
    </data>
    <data name="&gt;&gt;$this.Text" xml:space="preserve">
        <value>Yet another translation</value>
    </data>
    <data name="ToolTipString.ToolTipText" xml:space="preserve">
        <value>A ToolTip String</value>
    </data>
</root>
"""

    sample_translated_resx = \
"""<?xml version='1.0' encoding='UTF-8'?>
<root>
    <data name="&gt;&gt;someString.Name" xml:space="preserve">
        <value>SomeString</value>
    </data>
    <data name="SomeString.Text" xml:space="preserve">
        <value>Traduzione di Bablefish per questa stringa</value>
    </data>
    <data name="SomeOtherString" xml:space="preserve">
        <value>Translation for the other string</value>
    </data>
    <data name="&gt;&gt;$this.Name" xml:space="preserve">
        <value>YetAnotherString</value>
    </data>
    <data name="&gt;&gt;$this.Text" xml:space="preserve">
        <value>Yet another translation</value>
    </data>
    <data name="ToolTipString.ToolTipText" xml:space="preserve">
        <value>Translated ToolTip String</value>
    </data>
</root>
"""

    def test_read_file(self):
        extractor = parser.RESX()
        dir = os.path.dirname(__file__)
        file = os.path.join(dir, "test.resx")

        self.assertEquals(
            extractor._read_file(file),
            RESXTests.sample_resx
        )

    def test_extract_strings_from_filename(self):
        extractor = parser.RESX()
        extractor._read_file = mock.Mock(
            return_value = RESXTests.sample_resx
        )

        extracted_strings = extractor.extract_strings_from_filename("some_file")

        self.assertEquals(
            extracted_strings,
            set([
                u"SomeString",
                u"SomeOtherString",
                u"YetAnotherString",
                u"ToolTipString",
            ])
        )

        for string in extracted_strings:
            self.assertEquals(type(string), types.UnicodeType)

    def test_extract_mapping_from_filename(self):
        extractor = parser.RESX()
        extractor._read_file = mock.Mock(
            return_value = RESXTests.sample_resx
        )

        string_mapping = extractor.extract_mapping_from_filename("some_file")

        self.assertEquals(
            string_mapping.string_mapping_dict,
            {
                u"SomeString"       : u"Translation for some string",
                u"SomeOtherString"  : u"Translation for the other string",
                u"YetAnotherString" : u"Yet another translation",
                u"ToolTipString"    : u"A ToolTip String",
            }
        )

        for key, value in string_mapping.string_mapping_dict.iteritems():
            self.assertEquals(type(key), types.UnicodeType)
            self.assertEquals(type(value), types.UnicodeType)

    def test_filter_filenames(self):
        extractor = parser.RESX()

        self.assertEquals(
            extractor._filter_filenames(
                [ "suitcase.resx", "suitcase.jp-JP.resx" ],
            ),
            [ "suitcase.resx" ]
        )

        extractor._filter_filenames = mock.Mock(return_value = [])

        extractor.extract_strings_from_files([ "test.resx", "test.jp-JP.resx" ])

        extractor._filter_filenames.assert_called_with(
           [ "test.resx", "test.jp-JP.resx" ]
        )

        extractor.extract_string_mapping_from_files(
            [ "test.resx", "test.it-IT.resx" ]
        )

        extractor._filter_filenames.assert_called_with(
           [ "test.resx", "test.it-IT.resx" ]
        )

    @mock.patch.object(os, "mkdir")
    def test_translate(self, mkdir_func):
        resx_parser = parser.RESX()
        vcs_class = mock.Mock()
        resx_parser._read_file = mock.Mock(return_value = RESXTests.sample_resx)
        test_file = teststringio.TestStringIO()

        resx_parser._open_file_for_writing = mock.Mock(return_value = test_file)

        self.assertEquals(
            resx_parser.translate(
                "test.it-IT.resx",
                "Resources",
                {
                    u"Translation for \"some\" string" :
                        u"Traduzione di Bablefish per \"questa\" stringa",
                    u"Translation\\nfor the other string" :
                        u"Translation\\nfor the other string",
                    u"Will not show up" : u"Will not show up",
                    u"A ToolTip String" : u"Translated ToolTip String",
                },
                "Italian",
                "it-IT",
                True,
                vcs_class
            ),
            "test.it-IT.resx"
        )

        self.assertFalse(mkdir_func.called)
        self.assertFalse(resx_parser._open_file_for_writing.called)
        self.assertFalse(vcs_class.add_file.called)
        self.assertFalse(vcs_class.mark_file_for_edit.called)

        output_filename = resx_parser.translate(
            "Sample.resx",
            "Resources",
            {
                u"Translation for some string" :
                    u"Traduzione di Bablefish per questa stringa",
                u"Translation for the other string" :
                    u"Translation for the other string",
                u"Will not show up" : u"Will not show up",
                u"A ToolTip String" : u"Translated ToolTip String",
            },
            "Italian",
            "it-IT",
            True,
            vcs_class
        )

        mkdir_func.assert_called_with(
            "Resources"
        )
        resx_parser._open_file_for_writing.assert_called_with(
            os.path.join("Resources", "Sample.it-IT.resx")
        )

        self.assertEquals(
            output_filename,
            os.path.join("Resources", "Sample.it-IT.resx")
        )

        self.assertEquals(
            test_file.getvalue(),
            RESXTests.sample_translated_resx
        )

        vcs_class.add_file.assert_called_with(
            os.path.join("Resources", "Sample.it-IT.resx")
        )

    @mock.patch("__builtin__.open")
    def test_open_file_for_writing(self, open_func):
        extractor = parser.RESX()
        extractor._open_file_for_writing("filename")

        open_func.assert_called_with("filename", "w")

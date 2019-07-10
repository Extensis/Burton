import codecs
import mock
import os
import types
import unittest

from burton import parser
from . import teststringio

class RCTests(unittest.TestCase):
    sample_rc = \
"""#include "resource.h"
#define APSTUDIO_READONLY_SYMBOLS
#include "afxres.h"
#undef APSTUDIO_READONLY_SYMBOLS

#if !defined(AFX_RESOURCE_DLL) || defined(AFX_TARG_ENU)
#ifdef _WIN32
LANGUAGE LANG_ENGLISH, SUBLANG_ENGLISH_US
#pragma code_page(1252)
#endif //_WIN32

BEGIN
    BLOCK "StringFileInfo"
    BEGIN
        BLOCK "040904b0"
        BEGIN
            VALUE "FileVersion", "2, 0, 0, 1"
            VALUE "ProductVersion", "2, 0, 0, 1"
        END
    END
    BLOCK "VarFileInfo"
    BEGIN
        VALUE "Translation", 0x409, 1200
    END
END

IDD_PROGRESS DIALOGEX 0, 0, 316, 66
STYLE DS_SETFONT | DS_MODALFRAME | DS_FIXEDSYS | WS_POPUP | WS_CAPTION
CAPTION "Activating fonts"
FONT 8, "MS Shell Dlg", 400, 0, 0x1
BEGIN
    LTEXT           "YetAnotherString",IDC_STATIC_HEADER,12,6,294,8
    CONTROL         "",IDC_PROGRESS,"msctls_progress32",WS_BORDER,12,24,294,14
END

STRINGTABLE
BEGIN
     SomeString               "Translation for ""some"" string"
     SomeOtherString
                              "Translation\\nfor the \\
other string"
END
"""

    sample_translated_rc = \
"""#include "resource.h"\r
#define APSTUDIO_READONLY_SYMBOLS\r
#include "afxres.h"\r
#undef APSTUDIO_READONLY_SYMBOLS\r
\r
#if !defined(AFX_RESOURCE_DLL) || defined(AFX_TARG_ENU)\r
#ifdef _WIN32\r
LANGUAGE LANG_ENGLISH, SUBLANG_ENGLISH_US\r
#pragma code_page(1252)\r
#endif //_WIN32\r
\r
BEGIN\r
    BLOCK "StringFileInfo"\r
    BEGIN\r
        BLOCK "040904b0"\r
        BEGIN\r
            VALUE "FileVersion", "2, 0, 0, 1"\r
            VALUE "ProductVersion", "2, 0, 0, 1"\r
        END\r
    END\r
    BLOCK "VarFileInfo"\r
    BEGIN\r
        VALUE "Translation", 0x409, 1200\r
    END\r
END\r
\r
IDD_PROGRESS DIALOGEX 0, 0, 316, 66\r
STYLE DS_SETFONT | DS_MODALFRAME | DS_FIXEDSYS | WS_POPUP | WS_CAPTION\r
CAPTION "Activating fonts"\r
FONT 8, "MS Shell Dlg", 400, 0, 0x1\r
BEGIN\r
    LTEXT           "YetAnotherString",IDC_STATIC_HEADER,12,6,294,8\r
    CONTROL         "",IDC_PROGRESS,"msctls_progress32",WS_BORDER,12,24,294,14\r
END\r
\r
STRINGTABLE\r
BEGIN\r
     SomeString               "Traduzione di Bablefish per ""questa"" stringa"\r
     SomeOtherString\r
                              "Translation\\nfor the \\\r
other string"\r
END\r\n\r
"""

    def test_open_file(self):
        extractor = parser.RC()
        dir = os.path.dirname(__file__)
        file = os.path.join(dir, "test.rc")

        self.assertEquals(
            extractor._open_file(file)[0].read(),
            RCTests.sample_rc
        )

    def test_extract_strings_from_filename(self):
        extractor = parser.RC()
        extractor._open_file = mock.Mock(return_value = (
            teststringio.TestStringIO(None, RCTests.sample_rc),
            "iso-8859-1",
        ))

        extracted_strings = extractor.extract_strings_from_filename("some_file")

        self.assertEquals(
            extracted_strings,
            set([
                u"SomeString",
                u"SomeOtherString",
                u"YetAnotherString",
                u"Activating fonts",
            ])
        )

        for string in extracted_strings:
            self.assertEquals(type(string), str)

    def test_extract_mapping_from_filename(self):
        extractor = parser.RC()
        extractor._open_file = mock.Mock(return_value = (
            teststringio.TestStringIO(None, RCTests.sample_rc),
            "utf_8",
        ))

        string_mapping = extractor.extract_mapping_from_filename("some_file")

        self.assertEquals(
            string_mapping.string_mapping_dict,
            {
                u"SomeString" : u"Translation for \"some\" string",
                u"SomeOtherString" : u"Translation\\nfor the other string",
                u"YetAnotherString" : u"YetAnotherString",
                u"Activating fonts" : u"Activating fonts",
            }
        )

        for key, value in string_mapping.string_mapping_dict.items():
            self.assertEquals(type(key), str)
            self.assertEquals(type(value), str)

    def test_filter_filenames(self):
        extractor = parser.RC()

        self.assertEquals(
            extractor._filter_filenames(
                [ "suitcase.rc", "suitcase.jp-JP.rc" ],
            ),
            [ "suitcase.rc" ]
        )

        extractor._filter_filenames = mock.Mock(return_value = [])

        extractor.extract_strings_from_files([ "test.rc", "test.jp-JP.rc" ])

        extractor._filter_filenames.assert_called_with(
           [ "test.rc", "test.jp-JP.rc" ]
        )

        extractor.extract_string_mapping_from_files(
            [ "test.rc", "test.it-IT.rc" ]
        )

        extractor._filter_filenames.assert_called_with(
           [ "test.rc", "test.it-IT.rc" ]
        )

    @mock.patch.object(os, "mkdir")
    def test_translate(self, mkdir_func):
        rc_parser = parser.RC()
        vcs_class = mock.Mock()
        test_output_file = teststringio.TestStringIO()
        test_input_file = None

        def _get_input_file(self):
            test_input_file = teststringio.TestStringIO(None, RCTests.sample_rc)
            return test_input_file, "utf-8"

        rc_parser._open_file_for_writing = mock.Mock(
            return_value = test_output_file
        )
        rc_parser._open_file = mock.Mock(side_effect = _get_input_file)

        output_filename = rc_parser.translate(
            "Sample.rc",
            "Resources",
            {
                u"Translation for \"some\" string" :
                    u"Traduzione di Bablefish per \"questa\" stringa",
                u"Translation\\nfor the other string" :
                    u"Translation\\nfor the other string",
                u"Will not show up" : u"Will not show up",
            },
            "Italian",
            "it-IT",
            True,
            vcs_class,
            None
        )

        mkdir_func.assert_called_with(
            "Resources"
        )

        rc_parser._open_file_for_writing.assert_called_with(
            os.path.join("Resources", "Sample.it-IT.rc")
        )

        self.assertEquals(
            output_filename,
            os.path.join("Resources", "Sample.it-IT.rc")
        )

        self.assertEquals(
            test_output_file.getvalue(),
            RCTests.sample_translated_rc
        )

        vcs_class.add_file.assert_called_with(
            os.path.join("Resources", "Sample.it-IT.rc")
        )

    @mock.patch.object(codecs, "open")
    def test_open_file_for_writing(self, open_func):
        rc_parser = parser.RC()
        rc_parser._open_file_for_writing("filename")

        open_func.assert_called_with("filename", "w", "utf_16")

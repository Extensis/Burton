import mock
import os
import unittest

from io import StringIO

import stringextractor

class RCExtractorTests(unittest.TestCase):
    sample_resx = \
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
            VALUE "SomeString", "Translation for some string"
            VALUE "SomeOtherString", "Translation for the other string"
        END
    END
END
"""

    def test_open_file(self):
        extractor = stringextractor.RC()
        dir = os.path.dirname(__file__)
        file = os.path.join(dir, "test.rc")

        self.assertEquals(
            extractor._open_file(file).read(),
            RCExtractorTests.sample_resx
        )

    def test_extract_strings_from_filename(self):
        extractor = stringextractor.RC()
        extractor._open_file = mock.Mock(
            return_value = StringIO(RCExtractorTests.sample_resx)
        )

        self.assertEquals(
            extractor.extract_strings_from_filename("some_file"),
            set([ "SomeString", "SomeOtherString" ])
        )

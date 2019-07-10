import mock
import os
import sys
import types
import unittest

from burton import parser

class NIBTests(unittest.TestCase):
    @unittest.skipUnless(sys.platform == "darwin", "Requires Mac")
    def test_extract_strings_from_filename(self):
        extractor = parser.MacSource()
        extracted_strings = extractor.extract_strings_from_filename(
            os.path.join(os.path.dirname(__file__), "test.m")
        )

        self.assertEquals(
            extracted_strings,
            set([
                u"SomeString",
                u"SomeOtherString",
                u"YetAnotherString",
                u"SomeString2",
                u"SomeOtherString2",
                u"YetAnotherString2",
            ])
        )

        for string in extracted_strings:
            self.assertEquals(type(string), str)

import chardet
import cStringIO
import mock
import struct
import types
import unittest

import parser

class UtilTests(unittest.TestCase):
    def test_filter_string_unescapes_slashes(self):
        apostrophe_string = parser.filter_string(r"There\'s no escape!")
        newline_string    = parser.filter_string("New\r\nline")
        newline_string2   = parser.filter_string("New\\r\\nline")

        self.assertEquals(apostrophe_string, u"There's no escape!")
        self.assertEquals(type(apostrophe_string), types.UnicodeType)

        self.assertEquals(newline_string, u"New\\r\\nline")
        self.assertEquals(type(newline_string), types.UnicodeType)

        self.assertEquals(newline_string2, u"New\\r\\nline")
        self.assertEquals(type(newline_string2), types.UnicodeType)

    def test_replace_params(self):
        self.assertEquals(
            parser.replace_params("% -3.3lld of {5} %$ {x} %d%%%d %"),
            (   "{0} of {1} %$ {x} {2}%%{3} %",
                [ "% -3.3lld", "{5}",  "%d", "%d" ]
            )
        )

    def test_restore_platform_specific_params(self):
        self.assertEquals(
            parser.restore_platform_specific_params(
                "{0} of {1} %$ {x} {2} %",
                [ "{1}", "{5}", "%d" ]
            ),
            "{1} of {5} %$ {x} %d %"
        )

    @mock.patch.object(chardet, "detect")
    def test_detect_encoding(self, mock_func):
        mock_func.return_value = { "encoding" : "ascii" }

        test_file = cStringIO.StringIO("this is an ascii string")
        self.assertEquals(parser.detect_encoding(test_file), "ascii")
        test_file.close()

        bom = struct.pack("BBB", 0xEF, 0xBB, 0xBF)
        test_file = cStringIO.StringIO(bom + "UTF-8 String")
        self.assertEquals(parser.detect_encoding(test_file), "utf_8")

        bom = struct.pack("BB", 0xFE, 0xFF)
        test_file = cStringIO.StringIO(bom + "UTF-16 BE String")
        self.assertEquals(parser.detect_encoding(test_file), "utf_16")

        bom = struct.pack("BBBB", 0x00, 0x00, 0xFE, 0xFF)
        test_file = cStringIO.StringIO(bom + "UTF-16 32 String")
        self.assertEquals(parser.detect_encoding(test_file), "utf_32")

        def _throw_exception(file):
            raise Exception

        mock_func.side_effect = _throw_exception

        test_file = cStringIO.StringIO("this is a strange string")
        self.assertEquals(parser.detect_encoding(test_file), "iso-8859-1")


import chardet
import mock
import struct
import types
import unittest

from io import BytesIO

import burton.parser

class UtilTests(unittest.TestCase):
    def test_filter_string_unescapes_slashes(self):
        apostrophe_string = burton.parser.filter_string(r"There\'s no escape!")
        newline_string    = burton.parser.filter_string("New\r\nline")
        newline_string2   = burton.parser.filter_string("New\\r\\nline")

        self.assertEquals(apostrophe_string, u"There's no escape!")
        self.assertEquals(type(apostrophe_string), str)

        self.assertEquals(newline_string, u"New\\r\\nline")
        self.assertEquals(type(newline_string), str)

        self.assertEquals(newline_string2, u"New\\r\\nline")
        self.assertEquals(type(newline_string2), str)

    def test_replace_params(self):
        self.assertEquals(
            burton.parser.replace_params("%-3.3lld of {5} %$ {x} %d%%%d %"),
            (   "{0} of {1} %$ {x} {2}%%{3} %",
                [ "%-3.3lld", "{5}",  "%d", "%d" ]
            )
        )

        self.assertEquals(
            burton.parser.replace_params("{0}% complete"),
            (
                "{0}% complete",
                [ "{0}" ]
            )
        )

    def test_restore_platform_specific_params(self):
        self.assertEquals(
            burton.parser.restore_platform_specific_params(
                "{0} of {1} %$ {x} {2} %",
                [ "{1}", "{5}", "%d" ]
            ),
            "{1} of {5} %$ {x} %d %"
        )

    @mock.patch.object(chardet, "detect")
    def test_detect_encoding(self, mock_func):
        mock_func.return_value = { "encoding" : "ascii" }

        test_file = BytesIO(b"this is an ascii string")
        self.assertEquals(burton.parser.detect_encoding(test_file), "ascii")
        test_file.close()

        bom = struct.pack("BBB", 0xEF, 0xBB, 0xBF)
        test_file = BytesIO(bom + b"UTF-8 String")
        self.assertEquals(burton.parser.detect_encoding(test_file), "utf_8")

        bom = struct.pack("BB", 0xFE, 0xFF)
        test_file = BytesIO(bom + b"UTF-16 BE String")
        self.assertEquals(burton.parser.detect_encoding(test_file), "utf_16")

        bom = struct.pack("BBBB", 0x00, 0x00, 0xFE, 0xFF)
        test_file = BytesIO(bom + b"UTF-16 32 String")
        self.assertEquals(burton.parser.detect_encoding(test_file), "utf_32")

        def _throw_exception(file):
            raise Exception

        mock_func.side_effect = _throw_exception

        test_file = BytesIO(b"this is a strange string")
        self.assertEquals(burton.parser.detect_encoding(test_file), "iso-8859-1")

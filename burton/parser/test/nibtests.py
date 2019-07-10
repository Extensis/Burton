import mock
import os
import sys
import types
import unittest

from burton import parser

class NIBTests(unittest.TestCase):
    sample_nib = \
    str.encode("""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
	<key>com.apple.ibtool.document.localizable-strings</key>
	<dict>
		<key>1</key>
		<dict>
			<key>title</key>
			<string>SomeString</string>
		</dict>
		<key>3</key>
		<dict>
			<key>title</key>
			<string>SomeOtherString</string>
		</dict>
	</dict>
</dict>
</plist>
""")

    @unittest.skipUnless(sys.platform == "darwin", "Requires Mac")
    def test_get_plist_from_nib_file(self):
        extractor = parser.NIB()
        dir = os.path.dirname(__file__)
        files = [ os.path.join(dir, "test.nib"), os.path.join(dir, "test.xib") ]

        for file in files:
            self.assertEquals(
                extractor._get_plist_from_nib_file(file),
                NIBTests.sample_nib
            )

    def test_extract_strings_from_filename(self):
        extractor = parser.NIB()
        extractor._get_plist_from_nib_file = mock.Mock(
            return_value = NIBTests.sample_nib
        )

        extracted_strings = extractor.extract_strings_from_filename("some_file")

        self.assertEquals(
            extracted_strings,
            set([ u"SomeString", u"SomeOtherString" ])
        )

        for string in extracted_strings:
            self.assertEquals(type(string), str)

    def test_extract_mapping_from_filename(self):
        extractor = parser.NIB()
        extractor._get_plist_from_nib_file = mock.Mock(
            return_value = NIBTests.sample_nib
        )

        mapping = extractor.extract_mapping_from_filename("some_file")

        self.assertEquals(
            mapping.string_mapping_dict,
            {
                u"SomeString": u"SomeString",
                u"SomeOtherString": u"SomeOtherString"
            }
        )

    def test_extracts_strings_from_nib_package(self):
        params = []
        def store_param(param):
            params.append(param)
            return []

        extractor = parser.NIB()
        extractor.extract_strings_from_filename = mock.Mock(
            side_effect = store_param
        )

        extractor.extract_strings_from_files([
            os.path.join("some.nib", "designable.nib"),
            os.path.join("some.nib", "keyedobjects.nib"),
            os.path.join("other.nib", "random.nib"),
        ])

        self.assertEquals(set(params), set([ "some.nib", "other.nib" ]))

    def test_filter_filenames(self):
        extractor = parser.NIB()

        self.assertEquals(
            set(extractor._filter_filenames([
                os.path.join("some.nib", "designable.nib"),
                os.path.join("some.nib", "keyedobjects.nib"),
                os.path.join("other.nib", "random.nib"),
                os.path.join("other.nib", "random.other"),
            ])),
            set([
                os.path.join("other.nib", "random.other"),
                "other.nib",
                "some.nib",
            ])
        )

        extractor._filter_filenames = mock.Mock(return_value = [])

        extractor.extract_strings_from_files([
            os.path.join("some.nib", "designable.nib"),
            os.path.join("some.nib", "keyedobjects.nib"),
        ])

        extractor._filter_filenames.assert_called_with([
            os.path.join("some.nib", "designable.nib"),
            os.path.join("some.nib", "keyedobjects.nib"),
        ])

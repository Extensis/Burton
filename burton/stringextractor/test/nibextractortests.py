import mock
import os
import sys
import unittest

import stringextractor

class NIBExtractorTests(unittest.TestCase):
    sample_nib = \
    """<?xml version="1.0" encoding="UTF-8"?>
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
"""

    @unittest.skipUnless(sys.platform == "darwin", "Requires Mac")
    def test_get_plist_from_nib_file(self):
        extractor = stringextractor.NIB()
        dir = os.path.dirname(__file__)
        files = [ os.path.join(dir, "test.nib"), os.path.join(dir, "test.xib") ]

        for file in files:
            self.assertEquals(
                extractor._get_plist_from_nib_file(file),
                NIBExtractorTests.sample_nib
            )

    @unittest.skipUnless(sys.platform == "darwin", "Requires Mac")
    def test_extract_strings_from_filename(self):
        extractor = stringextractor.NIB()
        extractor._get_plist_from_nib_file = mock.Mock(
            return_value = NIBExtractorTests.sample_nib
        )

        self.assertEquals(
            extractor.extract_strings_from_filename("some_file"),
            set([ "SomeString", "SomeOtherString" ])
        )

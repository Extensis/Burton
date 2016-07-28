import mock
import os
import unittest

import stringextractor

class RESXExtractorTests(unittest.TestCase):
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
</root>
"""

    def test_read_file(self):
        extractor = stringextractor.RESX()
        dir = os.path.dirname(__file__)
        file = os.path.join(dir, "test.resx")

        self.assertEquals(
            extractor._read_file(file),
            RESXExtractorTests.sample_resx
        )

    def test_extract_strings_from_filename(self):
        extractor = stringextractor.RESX()
        extractor._read_file = mock.Mock(
            return_value = RESXExtractorTests.sample_resx
        )

        self.assertEquals(
            extractor.extract_strings_from_filename("some_file"),
            set([ "SomeString", "SomeOtherString" ])
        )

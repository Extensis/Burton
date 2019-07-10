import mock
import os
import types
import unittest

from io import BytesIO, StringIO

from burton import parser

class StringsDictTests(unittest.TestCase):
    sample_strings = str.encode(
"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
    <dict>
        <key>Activate %lu Fonts</key>
        <dict>
            <key>NSStringLocalizedFormatKey</key>
            <string>%#@variable_0@</string>
            <key>variable_0</key>
            <dict>
                <key>NSStringFormatSpecTypeKey</key>
                <string>NSStringPluralRuleType</string>
                <key>NSStringFormatValueTypeKey</key>
                <string>lu</string>
                <key>zero</key>
                <string>Activate %lu Fonts</string>
                <key>one</key>
                <string>Activate %lu Font</string>
                <key>two</key>
                <string>Activate %lu Fonts</string>
                <key>few</key>
                <string>Activate %lu Fonts</string>
                <key>many</key>
                <string>Activate %lu Fonts</string>
                <key>other</key>
                <string>Activate %lu Fonts</string>
            </dict>
        </dict>
        <key>Deactivate %lu Fonts</key>
        <dict>
            <key>NSStringLocalizedFormatKey</key>
            <string>%#@variable_0@</string>
            <key>variable_0</key>
            <dict>
                <key>NSStringFormatSpecTypeKey</key>
                <string>NSStringPluralRuleType</string>
                <key>NSStringFormatValueTypeKey</key>
                <string>lu</string>
                <key>zero</key>
                <string>Deactivate %lu Fonts</string>
                <key>one</key>
                <string>Deactivate %lu Font</string>
                <key>two</key>
                <string>Deactivate %lu Fonts</string>
                <key>few</key>
                <string>Deactivate %lu Fonts</string>
                <key>many</key>
                <string>Deactivate %lu Fonts</string>
                <key>other</key>
                <string>Deactivate %lu Fonts</string>
            </dict>
        </dict>
    </dict>
</plist>
""")

    translated_strings = str.encode(
"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
    <dict>
        <key>Activate %lu Fonts</key>
        <dict>
            <key>NSStringLocalizedFormatKey</key>
            <string>%#@variable_0@</string>
            <key>variable_0</key>
            <dict>
                <key>NSStringFormatSpecTypeKey</key>
                <string>NSStringPluralRuleType</string>
                <key>NSStringFormatValueTypeKey</key>
                <string>lu</string>
                <key>zero</key>
                <string>Activate Plural</string>
                <key>one</key>
                <string>Activate Singular</string>
                <key>two</key>
                <string>Activate Plural</string>
                <key>few</key>
                <string>Activate Plural</string>
                <key>many</key>
                <string>Activate Plural</string>
                <key>other</key>
                <string>Activate Plural</string>
            </dict>
        </dict>
        <key>Deactivate %lu Fonts</key>
        <dict>
            <key>NSStringLocalizedFormatKey</key>
            <string>%#@variable_0@</string>
            <key>variable_0</key>
            <dict>
                <key>NSStringFormatSpecTypeKey</key>
                <string>NSStringPluralRuleType</string>
                <key>NSStringFormatValueTypeKey</key>
                <string>lu</string>
                <key>zero</key>
                <string>Deactivate Plural</string>
                <key>one</key>
                <string>Deactivate Singular</string>
                <key>two</key>
                <string>Deactivate Plural</string>
                <key>few</key>
                <string>Deactivate Plural</string>
                <key>many</key>
                <string>Deactivate Plural</string>
                <key>other</key>
                <string>Deactivate Plural</string>
            </dict>
        </dict>
    </dict>
</plist>
""")

    def test_read_file(self):
        extractor = parser.StringsDict()
        dir = os.path.dirname(__file__)
        file = os.path.join(dir, "test.stringsdict")

        self.assertEquals(
            extractor._read_file(file),
            StringsDictTests.sample_strings
        )

    def test_extract_strings_from_filename(self):
        extractor = parser.StringsDict()
        extractor._read_file = mock.Mock(
            return_value = StringsDictTests.sample_strings
        )

        strings = extractor.extract_strings_from_filename("some_file")

        self.assertEquals(
            strings,
            set([
                u"Activate %lu Fonts",
                u"Activate %lu Font",
                u"Deactivate %lu Fonts",
                u"Deactivate %lu Font",
            ])
        )

    def test_extract_mapping_from_filename(self):
        extractor = parser.StringsDict()
        extractor._read_file = mock.Mock(
            return_value = StringsDictTests.sample_strings
        )

        string_mapping = extractor.extract_mapping_from_filename("some_file")

        self.assertEquals(
            string_mapping.string_mapping_dict,
            {
                u"Activate %lu Fonts" : "Activate %lu Fonts",
                u"Activate %lu Font" : "Activate %lu Font",
                u"Deactivate %lu Fonts" : "Deactivate %lu Fonts",
                u"Deactivate %lu Font" : u"Deactivate %lu Font",
            }
        )

        for key, value in string_mapping.string_mapping_dict.items():
            self.assertEquals(type(key), str)
            self.assertEquals(type(value), str)

    @mock.patch.object(os, "mkdir")
    def test_translate(self, mkdir_func):
        file = BytesIO()
        translator = parser.StringsDict();
        test_file = BytesIO()
        vcs_class = mock.Mock()

        translator._open_file_for_writing = mock.Mock(return_value = test_file)
        translator._read_file = mock.Mock(return_value = StringsDictTests.sample_strings)

        self.assertEquals(
            translator.translate(
                "test.stringsdict",
                "Resources",
                {
                    u'Activate %lu Fonts' : u'Activate Plural',
                    u'Activate %lu Font' : u'Activate Singular',
                    u'Deactivate %lu Fonts' : u'Deactivate Plural',
                    u'Deactivate %lu Font' : u'Deactivate Singular'
                },
                "French",
                "fr",
                True,
                vcs_class,
                None
            ),
            os.path.join("Resources", "test.stringsdict")
        )

        self.assertEquals(
            test_file.getvalue(),
            StringsDictTests.translated_strings
        )

        mkdir_func.assert_called_with(
            "Resources"
        )

        translator._open_file_for_writing.assert_called_with(
            os.path.join("Resources", "test.stringsdict")
        )

        vcs_class.add_file.assert_called_with(
            os.path.join("Resources", "test.stringsdict")
        )

        file.close()

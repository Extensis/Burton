import codecs
import mock
import os
import unittest

from burton import parser
from burton import stringmapping
from . import teststringio

class LPROJTests(unittest.TestCase):

    @mock.patch.object(os, "listdir")
    @mock.patch.object(os, "mkdir")
    def test_translate(self, mkdir_func, listdir_func):
        listdir_func.return_value = [ "Localizable.strings", "Localizable.stringsdict" ]
        lproj_parser = parser.LPROJ()
        test_file = teststringio.TestStringIO()
        fake_strings_parser = parser.Strings()
        fake_stringsdict_parser = parser.StringsDict();
        vcs_class = mock.Mock()

        lproj_parser._open_file = mock.Mock(return_value = test_file)
        lproj_parser._create_strings_parser = mock.Mock(
            return_value = fake_strings_parser
        )

        lproj_parser._create_stringsdict_parser = mock.Mock(
            return_value = fake_stringsdict_parser
        )
        fake_stringsdict_parser.translate = mock.Mock()

        string_mapping = stringmapping.StringMapping()
        string_mapping.add_mapping(
            '"SomeString"',
            u"Translation for some string"
        )
        string_mapping.add_mapping('"NewString"',  u"Untranslated string")
        string_mapping.add_mapping('InfoPlistVar',  u"Untranslated string")
        fake_strings_parser.extract_mapping_from_filename = mock.Mock(
            return_value = string_mapping
        )

        translation_dict = {
            u"Translation for some string" :
                u"Traduzione di Bablefish per questa stringa",
            u"Extra string" : u"Not in file to localize",
        };

        output_filenames = lproj_parser.translate(
            "en.lproj",
            "Resources",
            translation_dict,
            "Italian",
            "it",
            True,
            vcs_class,
            None
        )

        mkdir_func.assert_called_with(
            os.path.join("Resources", "it.lproj")
        )
        lproj_parser._open_file.assert_called_with(
            os.path.join("Resources", "it.lproj", "Localizable.strings")
        )

        self.assertEquals(
            output_filenames,
            os.path.join("Resources", "it.lproj")
        )

        self.assertEquals(
            test_file.getvalue(),
            """"NewString" = "Untranslated string";
"SomeString" = "Traduzione di Bablefish per questa stringa";
InfoPlistVar = "Untranslated string";\n"""
        )

        fake_stringsdict_parser.translate.assert_called_with(
            os.path.join("en.lproj", "Localizable.stringsdict"),
            os.path.join("Resources", "it.lproj"),
            translation_dict,
            "Italian",
            "it",
            True,
            vcs_class,
            None
        )

        vcs_class.add_file.assert_called_with(
            os.path.join("Resources", "it.lproj", "Localizable.strings")
        )

    @mock.patch.object(codecs, "open")
    def test_open_file(self, open_func):
        lproj_parser = parser.LPROJ()
        lproj_parser._open_file("filename")
        open_func.assert_called_with("filename", "w", "utf-8")

    def test_create_strings_parser(self):
        lproj_parser = parser.LPROJ()
        self.assertEquals(
            type(lproj_parser._create_strings_parser()),
            type(parser.Strings())
        )

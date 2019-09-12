import mock
import os
import types
import unittest

from io import StringIO

from burton import parser
from . import teststringio

class AngularTests(unittest.TestCase):
    sample_strings = \
"""///<reference path='../../typings/tsd.d.ts' />

module Extensis.Suitcase.i18n {

    import ITranslateProvider = angular.translate.ITranslateProvider;
    import ITranslationTable = angular.translate.ITranslationTable;

    'use strict';

    angular
        .module('webapp')
        .config(['$translateProvider', ($translateProvider: ITranslateProvider) => {

            var strings: ITranslationTable = {
                '[SomeString]'                 : 'Translation for some string',
                '[SomeOtherString]'            : 'Translation for the other string',
                '[Couldn\'t open font "{0}".]' : 'Couldn\'t open font "{0}".',
            };

            $translateProvider.translations('en', strings);
        }]);
}
"""

    translated_strings = \
"""///<reference path='../../typings/tsd.d.ts' />

module Extensis.Suitcase.i18n {

    import ITranslateProvider = angular.translate.ITranslateProvider;
    import ITranslationTable = angular.translate.ITranslationTable;

    'use strict';

    angular
        .module('webapp')
        .config(['$translateProvider', ($translateProvider: ITranslateProvider) => {

            var strings: ITranslationTable = {
                '[SomeString]'                 : 'Translation for some string',
                '[SomeOtherString]'            : 'Can\\\'t "quote" \\xe9\\u4e00\\xe9!',
                '[Couldn\\\'t open font "{0}".]' : 'Couldn\\\'t open font "{0}".',
            };

            $translateProvider.translations('es', strings);
        }]);
}

"""

    def test_extract_strings_from_filename(self):
        extractor = parser.Angular()
        extractor._open_file_for_reading = mock.Mock(return_value = (
            StringIO(AngularTests.sample_strings),
            "utf_8"
        ))

        strings = extractor.extract_strings_from_filename("some_file")

        self.assertEquals(
            strings,
            set([
                u"SomeString",
                u"SomeOtherString",
                u"Couldn\'t open font \"{0}\"."
            ])
        )

    def test_extract_mapping_from_filename(self):
        extractor = parser.Angular()
        extractor._open_file_for_reading = mock.Mock(return_value = (
            StringIO(AngularTests.sample_strings),
            "utf_8"
        ))

        string_mapping = extractor.extract_mapping_from_filename("some_file")

        self.assertEquals(
            string_mapping.string_mapping_dict,
            {
                u"SomeString" : u"Translation for some string",
                u"SomeOtherString" : u"Translation for the other string",
                u"Couldn\'t open font \"{0}\"." :
                    u"Couldn\'t open font \"{0}\".",
            }
        )

        for key, value in string_mapping.string_mapping_dict.items():
            self.assertEquals(type(key), str)
            self.assertEquals(type(value), str)

    def test_translate(self):
        vcs_class = mock.Mock()
        translator = parser.Angular()
        output_file = teststringio.TestStringIO()

        translator._open_file_for_reading = mock.Mock(return_value = (
            teststringio.TestStringIO(None, AngularTests.sample_strings),
            "utf_8"
        ))

        translator._open_file_for_writing = mock.Mock(return_value = output_file)

        mapping = { u"Translation for the other string" : u"Can't \"quote\" \xe9\u4e00\xe9!" }

        translator.translate(
            'english.i18n.ts',
            '.',
            mapping,
            'Spanish',
            'es',
            True,
            vcs_class,
            None
        )

        self.assertEquals(
            output_file.getvalue(),
            AngularTests.translated_strings
        )

        translator._open_file_for_writing.assert_called_with(
            os.path.join(".", "spanish.i18n.ts")
        )

        vcs_class.add_file.assert_called_with(
            os.path.join(".", "spanish.i18n.ts")
        )

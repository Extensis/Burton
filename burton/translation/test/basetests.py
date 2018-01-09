import unittest

import translation

class BaseTests(unittest.TestCase):
    def test_add_translation(self):
        trans = translation.Base("Italian", "it-IT", "en", "", "", "")
        trans.add_translation(u"Some native string", u"Some translation")
        self.assertEquals(
            trans.translation_dict,
            {
                u"Some native string"             : u"Some translation",
                u"Some native string..."          : u"Some translation...",
                u"Some native string\xe2\x80\xa6" : u"Some translation\xe2\x80\xa6"
            }
        )

    def test_delete_translation(self):
        trans = translation.Base("Italian", "it-IT", "en", "", "", "")
        trans.add_translation(u"Some native string", u"Some translation")
        self.assertEquals(
            trans.translation_dict,
            {
                u"Some native string"             : u"Some translation",
                u"Some native string..."          : u"Some translation...",
                u"Some native string\xe2\x80\xa6" : u"Some translation\xe2\x80\xa6"
            }
        )

        trans.delete_translation(u"Some native string")
        self.assertEquals(trans.translation_dict,{})

    def test_get_translation(self):
        trans = translation.Base("Italian", "it-IT", "en", "", "", "")
        trans.add_translation(u"Some native string", u"Some translation")
        self.assertEquals(
            trans.get_translation(u"Some native string"),
            u"Some translation"
        )

    def test_combine_with(self):
        trans1 = trans = translation.Base("Italian", "it-IT", "en", "", "", "")
        trans1.add_translation(u"Some native string", u"Some translation")
        trans1.add_translation(u"Some other string", u"Some other translation")

        trans2 = trans = translation.Base("Italian", "it-IT", "en", "", "", "")
        trans2.add_translation(u"Some native string", u"Different translation")
        trans2.add_translation(u"Some other string", None)
        trans2.add_translation(u"Some new string", u"Some new translation")

        trans1.combine_with(trans2)

        self.assertEquals(
            trans1.translation_dict,
            {
                u"Some native string"             : u"Different translation",
                u"Some native string..."          : u"Different translation...",
                u"Some native string\xe2\x80\xa6" : u"Different translation\xe2\x80\xa6",
                u"Some other string"              : u"Some other translation",
                u"Some other string..."           : u"Some other translation...",
                u"Some other string\xe2\x80\xa6"  : u"Some other translation\xe2\x80\xa6",
                u"Some new string"                : u"Some new translation",
                u"Some new string..."             : u"Some new translation...",
                u"Some new string\xe2\x80\xa6"    : u"Some new translation\xe2\x80\xa6",
            }
        )

    def test_remove_untranslated_strings(self):
        trans = trans = translation.Base("Italian", "it-IT", "en", "", "", "")
        trans.add_translation(u"Some native string", u"Some translation")
        trans.add_translation(u"Some other string", None)

        trans.remove_untranslated_strings()

        self.assertEquals(
            trans.translation_dict,
            {
                u"Some native string"             : u"Some translation",
                u"Some native string..."          : u"Some translation...",
                u"Some native string\xe2\x80\xa6" : u"Some translation\xe2\x80\xa6"
            }
        )

    def test_remove_translated_strings(self):
        trans = trans = translation.Base("Italian", "it-IT", "en", "", "", "")
        trans.add_translation(u"Some native string", u"Some translation")
        trans.add_translation(u"Some other string", None)

        trans.remove_translated_strings()

        self.assertEquals(
            trans.translation_dict,
            { u"Some other string" : None }
        )

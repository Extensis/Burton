import mock
import testfixtures
import unittest

import burton

class StringMappingTests(unittest.TestCase):
    def test_get_accessors(self):
        reference_mapping = burton.StringMapping(filename = "1.txt")
        reference_mapping.add_mapping(u"SomeKey", u"Translation for some key")

        self.assertEquals(
            reference_mapping.get_string(u"SomeKey"),
            u"Translation for some key"
        )
        self.assertEquals(reference_mapping.get_filenames(u"SomeKey"), ["1.txt"])

    def test_add_mapping(self):
        reference_mapping = burton.StringMapping()
        reference_mapping.add_mapping(u"SomeKey", u"Translation for some key")

        self.assertEquals(
            reference_mapping.get_string(u"SomeKey"),
            u"Translation for some key"
        )

    def test_combine_string_mappings(self):
        reference_mapping = burton.StringMapping()

        mapping1 = burton.StringMapping(filename = "1.txt")
        mapping1.add_mapping("SomeKey", "Translation for some key")

        mapping2 = burton.StringMapping(filename = "2.txt")
        mapping2.add_mapping(
            "SomeOtherKey", "Translation for the other string",
        )

        reference_mapping.combine_with(mapping1)
        reference_mapping.combine_with(mapping2)

        self.assertEquals(
            reference_mapping.get_string("SomeKey"),
            "Translation for some key"
        )
        self.assertEquals(reference_mapping.get_filenames("SomeKey"), ["1.txt"])

        self.assertEquals(
            reference_mapping.get_string("SomeOtherKey"),
            "Translation for the other string"
        )
        self.assertEquals(
            reference_mapping.get_filenames("SomeOtherKey"),
            [ "2.txt" ]
        )

    def test_iter(self):
        reference_mapping = burton.StringMapping(filename = "1.txt")
        reference_mapping.add_mapping(u"SomeKey", u"Translation for some key")
        reference_mapping.add_mapping(
            u"SomeOtherKey", u"Translation for the other string",
        )

        actual_return_values   = []
        expected_return_values = [ u"SomeKey",  u"SomeOtherKey" ]

        for key in reference_mapping:
            actual_return_values.append(key)

        actual_return_values.sort()
        self.assertEquals(actual_return_values, expected_return_values)

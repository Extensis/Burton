ellipsis = u'\xe2\x80\xa6'
three_dots = '...'

class Base(object):
    """This class is the base of the translation hierarchy. Translation objects
    represent a mapping from native-language strings into strings of another
    language, and read and write files intended for use by translators, such as
    XLIFF files.
    """

    def __init__(
        self,
        language,
        language_code,
        source_language,
        company_name,
        product_name,
        contact_email
    ):
        object.__init__(self)
        self._translation_dict = {}
        self.language          = language
        self.language_code     = language_code
        self.source_language   = source_language
        self.company_name      = company_name
        self.product_name      = product_name
        self.contact_email     = contact_email

    def add_translation(self, native_string, translation):
        """This method adds a translation to the object, replacing the previous
        translation for the native-language string, if any.
        """

        if translation is None:
            if native_string.endswith(ellipsis) or native_string.endswith(three_dots):
                native_string = native_string[:-3]

                if native_string in self._translation_dict:
                    return

        self._translation_dict[native_string] = translation

    def delete_translation(self, native_string):
        """This methods deletes the translation for the native string, if any.
        """
        if native_string in self._translation_dict:
            del self._translation_dict[native_string]

    def get_translation(self, native_string):
        """Returns the translation for the native-language string, or None if
        there is no translation for that string.
        """
        return self._translation_dict.get(native_string, None)

    def get_translation_dict(self):
        """This method returns a dictionary containing the translations held in
        this object. The return value can be freely modified without affecting
        the contents of this object"""
        copied_dict = self._translation_dict.copy()
        keys = list(copied_dict.keys())

        for key in keys:
            if not key.endswith(ellipsis) and not key.endswith(three_dots):
                mac_key = key + ellipsis
                win_key = key + three_dots

                value = copied_dict[key]

                if value is not None:
                    if not mac_key in copied_dict:
                        copied_dict[mac_key] = value + ellipsis

                    if not win_key in copied_dict:
                        copied_dict[win_key] = value + three_dots

        return copied_dict

    translation_dict = property(get_translation_dict, None)

    def combine_with(self, other):
        """Combines two translations, overriding this object's translatoins with
        the translations of th eobject passed in. However, if this object has a
        translation for a native-language string, and the translation passed in
        has a translation of None for the same string, that translation will not
        be replaced.
        """

        other_dict = other.translation_dict
        for key in other_dict:
            translation = other_dict[key]
            if not (translation is None and \
              self._translation_dict.get(key, None) is not None):
                self.add_translation(key, translation)

    def remove_untranslated_strings(self):
        """Removes all strings which are untranslated. After calling this
        method, untranslated strings will not be written when write() is called,
        unless more untranslated strings are added after this method is called.
        """

        keys_to_delete = []
        for key in self._translation_dict:
            if self._translation_dict[key] is None:
                keys_to_delete.append(key)

        for key in keys_to_delete:
            del self._translation_dict[key]

    def remove_translated_strings(self):
        """Removes all strings which are untranslated."""

        keys_to_delete = []
        for key in self._translation_dict:
            if self._translation_dict[key] is not None:
                keys_to_delete.append(key)

        for key in keys_to_delete:
            del self._translation_dict[key]

    def read(self, file):
        """This method accepts a file-like object and reads its contents,
        calling add_translation for each translation in the source file.

        The default implementation does nothing; it up to subclasses to override
        this method.
        """

    def write(self, file):
        """This method writes the translations to a file-like object.

        The default implementation does nothing; it up to subclasses to override
        this method.
        """

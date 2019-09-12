import lxml
import os

from pkg_resources import resource_stream

from burton import parser
from .base import Base

class XLF(Base):
    encoding               = "UTF-8"
    file_tag               = "file"
    header_tag             = "header"
    phase_group_tag        = "phase-group"
    phase_tag              = "phase"
    body_tag               = "body"
    group_tag              = "group"
    trans_unit_tag         = "trans-unit"
    source_tag             = "source"
    target_tag             = "target"
    product_name_attrib    = "product-name"
    company_name_attrib    = "company-name"
    contact_email_attrib   = "contact-email"
    target_language_attrib = "target-language"
    lang_attrib            = "{http://www.w3.org/XML/1998/namespace}lang"

    def read(self, file):
        tree = None

        try:
            tree = lxml.etree.fromstring(file.read())
        except Exception as e:
            tree = self._read_template()

        group = tree.find(XLF.file_tag).find(XLF.body_tag).find(XLF.group_tag)

        for child in group:
            if child.tag == XLF.trans_unit_tag and len(child) > 1:
                source = child.find(XLF.source_tag).text
                target = child.find(XLF.target_tag).text

                self.add_translation(source, target)

        if len(self._translation_dict) == 0:
            raise Exception(
                "Attempted to an read XLF file with no translations."
            )

    def write(self, file):
        tree = self._read_template()
        group = tree.find(XLF.file_tag).find(XLF.body_tag).find(XLF.group_tag)
        group.text = None # Needed for pretty_print to work

        untranslated_keys = []
        translated_keys   = []

        for key in self._translation_dict:
            if self._translation_dict[key] is None:
                untranslated_keys.append(key)
            else:
                translated_keys.append(key)

        untranslated_keys.sort()
        translated_keys.sort()

        all_keys = untranslated_keys
        all_keys.extend(translated_keys)

        for key in all_keys:
            if key is not None and key.strip() != "":
                trans_unit = lxml.etree.Element(
                    XLF.trans_unit_tag,
                    { "restype" : "string" },
                )

                source = lxml.etree.Element(
                    XLF.source_tag,
                    { XLF.lang_attrib : self.source_language },
                )

                filtered_source = None
                if key is not None:
                    filtered_source, replaced_params = \
                        parser.replace_params(key)

                source.text = filtered_source

                target = lxml.etree.Element(
                    XLF.target_tag,
                    { },
                )

                target.text = self._translation_dict[key]

                trans_unit.append(source)
                trans_unit.append(target)

                group.append(trans_unit)

        tree.write(
            file,
            xml_declaration = True,
            pretty_print = True,
            encoding = XLF.encoding
        )

    def _read_template(self):
        tree = lxml.etree.parse(
            resource_stream(__name__, "template.xlf"),
            lxml.etree.XMLParser(remove_blank_text = True)
        )

        file = tree.find(XLF.file_tag)
        file.set(XLF.target_language_attrib, self.language)
        file.set(XLF.product_name_attrib, self.product_name)

        phase = file.find(XLF.header_tag).\
            find(XLF.phase_group_tag).\
            find(XLF.phase_tag)

        phase.set(XLF.company_name_attrib, self.company_name)
        phase.set(XLF.contact_email_attrib, self.contact_email)

        return tree

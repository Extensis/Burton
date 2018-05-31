import logging
import lxml.etree
import os

import burton
from base import Base
from util import filter_string

class RESX(Base):
    data_tag             = "data"
    value_tag            = "value"
    space_attribute      = "{http://www.w3.org/XML/1998/namespace}space"
    name_attribute       = "name"
    preserve_value       = "preserve"
    name_suffix          = "Name"
    localizable_suffixes = [ "Text", "ToolTipText", "LabelText" ]

    def __init__(self):
        Base.__init__(self)

    def _filter_filenames(self, filenames):
        filtered_files = []

        for filename in filenames:
            parts = os.path.basename(filename).split(".")
            if len(parts) <= 2:
                filtered_files.append(filename)

        return filtered_files

    def extract_strings_from_filename(self, filename):
        return set(
            self.extract_mapping_from_filename(filename).\
            string_mapping_dict.keys()
        )

    def extract_mapping_from_filename(self, filename):
        string_mapping = burton.StringMapping(filename = filename)

        tree = lxml.etree.fromstring(self._read_file(filename))

        def _add_mapping(key, value, node):
            string_mapping.add_mapping(key + '-' + filename, value)

        self._parse(tree, filename, _add_mapping)

        return string_mapping

    def _parse(self, tree, filename, func):
        dollarsign_this_replacement = self._find_dollarsign_this(tree)
        if dollarsign_this_replacement is None:
            dollarsign_this_replacement = filename

        def filter_component(component):
            component = component.lstrip(">")

            if component == "$this":
                component = dollarsign_this_replacement

            return component

        for node in tree.findall(RESX.data_tag):
            if RESX.space_attribute in node.attrib \
               and node.attrib[RESX.space_attribute] == RESX.preserve_value:
                components = node.attrib[RESX.name_attribute].split(".")
                if len(components) == 1 \
                or components[-1] in RESX.localizable_suffixes:
                    key = unicode(".".join(map(filter_component, components)))
                    value = unicode(node.find(RESX.value_tag).text)

                    if key == "$this":
                        key = dollarsign_this_replacement

                    func(key, value, node)

    def translate(
        self,
        input_filename,
        output_directory,
        mapping,
        language,
        language_code,
        should_use_vcs,
        vcs_class
    ):
        parts = os.path.basename(input_filename).split(".")
        if len(parts) > 2:
            return input_filename

        logger = logging.getLogger(burton.logger_name)
        logger.debug("Localizing " + input_filename + " into " + language)

        output_filename = None
        if not os.path.exists(output_directory):
            os.mkdir(output_directory)

        if input_filename.endswith(".resx"):
            input_keys = self.extract_strings_from_filename(
                input_filename
            )

            output_filename = os.path.splitext(
                os.path.basename(input_filename)
            )[0]
            output_filename = os.path.join(
                output_directory,
                output_filename + "." + language_code + ".resx"
            )

            created_file = False

            if not os.path.exists(output_filename):
                created_file = True
                logger.error("Created new file " + output_filename)

            tree = lxml.etree.fromstring(self._read_file(input_filename))

            def _rewrite_mapping(key, value, node):
                if value in mapping:
                    node.find(RESX.value_tag).text =  mapping[value]

                elif filter_string(value) in mapping:
                    node.find(RESX.value_tag).text = \
                        mapping[filter_string(value)]


            self._parse(tree, input_filename, _rewrite_mapping)

            file = self._open_file_for_writing(output_filename)
            lxml.etree.ElementTree(element = tree).write(
                file,
                xml_declaration = True,
                pretty_print = True,
                encoding = "utf-8"
            )

            file.close()

            if should_use_vcs:
                vcs_class.add_file(output_filename)

        return output_filename

    def _find_dollarsign_this(self, tree):
        for node in tree.findall(RESX.data_tag):
            if RESX.space_attribute in node.attrib \
               and node.attrib[RESX.space_attribute] == RESX.preserve_value:
                components = node.attrib[RESX.name_attribute].split(".")
                if len(components) > 1 and \
                   components[-1] == RESX.name_suffix and \
                   components[-2].endswith("$this"):
                    return unicode(node.find(RESX.value_tag).text)

    def _read_file(self, filename):
        fp = open(filename, "r")
        return_value = fp.read()
        fp.close()
        return return_value

    def _open_file_for_writing(self, filename):
        return open(filename, "w")

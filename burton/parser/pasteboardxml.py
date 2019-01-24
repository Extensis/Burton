import logging
import lxml.etree
import os
import re

import burton
from base import Base
from util import filter_string

class PasteboardXML(Base):
    root_tag           = "manifest"
    identifier_tag     = "identifier"
    category_tag       = "category"
    title_tag          = "title"
    version_tag        = "version"
    filename_tag       = "filename"
    image_filename_tag = "imageFilename"
    elements_tag       = "elements"
    name_tag           = "name"
    element_tag        = "element"

    def __init__(self):
        Base.__init__(self)

    def _filter_filenames(self, filenames):
        filtered_files = []

        for filename in filenames:
            if filename.endswith("-en.xml"):
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
            string_mapping.add_mapping(key, value)

        self._parse(tree, _add_mapping)

        return string_mapping

    def translate(
        self,
        input_filename,
        output_directory,
        mapping,
        language,
        language_code,
        should_use_vcs,
        vcs_class,
        proj_file
    ):
        logger = logging.getLogger(burton.logger_name)
        logger.debug("Localizing " + input_filename + " into " + language)

        output_filename = None
        if not os.path.exists(output_directory):
            os.mkdir(output_directory)

        if input_filename.endswith("-en.xml"):
            output_filename = re.sub(
                u"-en\.xml$",
                u"-" + language_code + u".xml",
                input_filename
            )

            output_filename = os.path.join(output_directory, output_filename)

            if not os.path.exists(output_filename):
                logger.error("Create new file " + output_filename)

            tree = lxml.etree.fromstring(self._read_file(input_filename))

            def _rewrite_mapping(key, value, node):
                if value in mapping:
                    node.text = mapping[filter_string(value)]

            self._parse(tree, _rewrite_mapping)

            file = self._open_file_for_writing(output_filename)
            lxml.etree.ElementTree(element = tree).write(
                file,
                xml_declaration = False,
                pretty_print = True,
                encoding = "utf-8"
            )

            file.close()

            if should_use_vcs:
                vcs_class.add_file(output_filename)

        return output_filename

    def _parse(self, tree, func):
        element = tree.find(PasteboardXML.title_tag)

        if element != None:
            func(element.text, element.text, element)

        element = tree.find(PasteboardXML.category_tag)

        if element != None:
            func(element.text, element.text, element)

        element = tree.find(PasteboardXML.elements_tag)

        if element != None:
            for name in element.findall(PasteboardXML.name_tag):
                if name != None:
                    func(name.text, name.text, name)

    def _read_file(self, filename):
        fp = open(filename, "r")
        return_value = fp.read()
        fp.close()
        return return_value

    def _open_file_for_writing(self, filename):
        return open(filename, "w")

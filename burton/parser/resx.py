import logging
import lxml.etree
import os

import burton
from .base import Base
from .util import filter_string

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
                    key = ".".join(map(filter_component, components))
                    value = node.find(RESX.value_tag).text

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
        vcs_class,
        proj_file
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


            tree = lxml.etree.fromstring(self._read_file(input_filename))

            def _rewrite_mapping(key, value, node):
                if value in mapping:
                    node.find(RESX.value_tag).text =  mapping[value]

                elif filter_string(value) in mapping:
                    node.find(RESX.value_tag).text = \
                        mapping[filter_string(value)]


            self._parse(tree, input_filename, _rewrite_mapping)

            #Make sure output file exists
            file = self._open_file_for_writing(output_filename)
            lxml.etree.ElementTree(element = tree).write(
                file
            )
            # Keep open for unit tests
            file.flush()

            if proj_file is not None and proj_file.lower() != "none":
                # namespace for xpath queries
                ns = '{http://schemas.microsoft.com/developer/msbuild/2003}'

                # add this file to given project
                # open file
                proj_file_h = self._open_file_for_appending(proj_file)
                # load as xml
                parser = lxml.etree.XMLParser(remove_blank_text=True)
                proj_file_tree = lxml.etree.parse(proj_file_h, parser)
                proj_file_h.close()

                # compute our relative path of output_filename
                proj_base_path = os.path.dirname(os.path.abspath(proj_file)).replace('/', '\\')
                resx_relative_path = os.path.abspath(output_filename)
                resx_relative_path = resx_relative_path.replace('/', '\\')
                resx_relative_path = resx_relative_path.replace(proj_base_path, '')[1:]

                # see if file already exists in project
                # file name starts with a '/' at this point so skip that
                xpath = './/' + ns + 'EmbeddedResource[@Include="' + resx_relative_path + '"]'
                exists_in_proj = proj_file_tree.findall(xpath)

                if(len(exists_in_proj) == 0):
                    # add to project if needed
                    # modify proj file
                    # a section looks like:
                    #   <EmbeddedResource Include="MainView\Wizard\UpdatesPage.it-IT.resx">
                    #   <DependentUpon>UpdatesPage.cs</DependentUpon>
                    #   </EmbeddedResource>

                    # calculate our filenames for the include infile name and our dependent file name
                    dependent_upon = os.path.basename(file.name).split('.')
                    source_file_name = os.path.basename(input_filename);
                    out_file_name = os.path.basename(output_filename)

                    resx_relative_base_path = "\\".join(resx_relative_path.split('\\')[0:-1])
                    localized_element_path = resx_relative_base_path + '\\' + out_file_name
                    localized_element_path = localized_element_path.lstrip('/').lstrip('\\')
                    dep_upon_element_path =  source_file_name
                    dep_upon_element_path = dep_upon_element_path.lstrip('/').lstrip('\\')

                    # add after our dependent upon file
                    # determine if our dependent upon file is a compile or an embedded resource
                    element_type = 'Compile'
                    if(source_file_name.endswith('.resx')):
                        element_type = 'EmbeddedResource'

                    # generate our xpath
                    xpath = ".//" + ns + element_type + '[@Include="' + resx_relative_base_path + '\\' + dep_upon_element_path + '"]'

                    # find any matching
                    dep_upon_source = proj_file_tree.findall(xpath)
                    # if we don't match anything something went wrong
                    if (len(dep_upon_source) < 1):
                        print("Could not find " + input_filename + " in project file. Not adding " + output_filename + " to project")
                    else:
                        # create our new element
                        resource_elem = lxml.etree.Element('EmbeddedResource', Include=localized_element_path)
                        dep_upon_elem = lxml.etree.Element('DependentUpon')
                        dep_upon_elem.text = dep_upon_source[0][0].text
                        resource_elem.append(dep_upon_elem)

                        dep_upon_source[0].addnext(resource_elem)

                        # write changed file
                        newContents = lxml.etree.tostring(proj_file_tree, xml_declaration=True, pretty_print=True)
                        proj_file_h = self._open_file_for_writing(proj_file)
                        proj_file_h.write(newContents)
                        proj_file_h.close()

                        # add to vcs if we need to
                        if (should_use_vcs):
                            vcs_class.add_file(proj_file)

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
                    return node.find(RESX.value_tag).text

    def _read_file(self, filename):
        fp = open(filename, "r")
        return_value = fp.read()
        fp.close()
        return return_value

    def _open_file_for_writing(self, filename):
        return open(filename, "wb")

    def _open_file_for_appending(self, filename):
        return open(filename, 'rab')

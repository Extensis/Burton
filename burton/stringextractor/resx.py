import lxml.etree

import stringextractor

class RESX(stringextractor.Base):
    def __init__(self):
        stringextractor.Base.__init__(self)

    def extract_strings_from_filename(self, filename):
        return_values = set([])

        data_tag        = "data"
        value_tag       = "value"
        space_attribute = "{http://www.w3.org/XML/1998/namespace}space"
        name_attribute  = "name"
        preserve_value  = "preserve"
        name_suffix     = "Name"

        tree = lxml.etree.fromstring(self._read_file(filename))

        for node in tree.findall(data_tag):
            if space_attribute in node.attrib \
               and node.attrib[space_attribute] == preserve_value:
                components = node.attrib[name_attribute].split(".")
                if len(components) == 1:
                    return_values.add(components[0])
                elif components[-1] == name_suffix:
                    return_values.add(node.find(value_tag).text)

        return return_values

    def _read_file(self, filename):
        return open(filename, "r").read()

import cStringIO
import codecs
import logging
import os

import burton
from base import Base
from strings import Strings
from util import replace_params, restore_platform_specific_params

class LPROJ(Base):
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
        logger = logging.getLogger(burton.logger_name)
        logger.debug("Localizing " + input_filename + " into " + language)

        output_directory = os.path.join(
            output_directory,
            language_code + ".lproj"
        )
        
        created_file = False
        
        if not os.path.exists(output_directory):
            os.mkdir(output_directory)
            created_file = True
            logger.error("Created new file " + output_directory)

        for filename in os.listdir(input_filename):
            if filename.endswith(".strings"):
                strings_parser = self._create_strings_parser()
                input_mapping = \
                  strings_parser.extract_mapping_from_filename(
                      os.path.join(input_filename, filename),
                      False
                  ).string_mapping_dict

                output_filename = os.path.join(
                    output_directory,
                    os.path.basename(filename)
                )

                if should_use_vcs and not created_file:
                    vcs_class.update_path(output_filename)
                    vcs_class.mark_file_for_edit(output_filename)

                output_file_mapping = { }

                for key in input_mapping:
                    if input_mapping[key] is not None:
                        input_key, params = replace_params(input_mapping[key])
                        if input_key in mapping:
                            output_value = restore_platform_specific_params(
                                mapping[input_key],
                                params
                            )
                            output_file_mapping[key] = output_value
                        else:
                            output_file_mapping[key] = input_mapping[key]

                file = self._open_file(output_filename)
                strings_parser.write_mapping(file, output_file_mapping)
                
                file.close()
                
                if should_use_vcs:
                    if created_file:
                        vcs_class.add_file(output_filename)
                    else:
                        vcs_class.mark_file_for_edit(output_filename)

        return output_directory

    def _open_file(self, filename):
        return codecs.open(filename, "w", "utf-8")

    def _create_strings_parser(self):
        return Strings()

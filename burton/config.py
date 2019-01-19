import codecs
import collections
import ConfigParser
import json
import logging
import os
import re

from pkg_resources import resource_stream

import burton

class Config(object):
    """The Config class parses command-line options and configuration files,
    storing their values.

    Configuration files are in the standard Python ConfigParser format, with
    additional sections representing a platform that can be passed in on the
    command-line. When a platform is so passed in, its values in the config file
    will override the values in the default section, of the config file.

    Values can be any built-in Python type, including lists and dictionaries.
    This is accomplished using the JSON parser, so strings must use the
    double-quote symbol, not the single-quote symbol. Furthermore, dictionary
    keys must be strings.

    Config's parse method will only parse variables which are present in its
    config_file_defaults dictionary, and will emit an error if a config file
    contains a variable not present in this dictionary. However, users can
    manually set variables using the set method which are not in this
    dictionary.

    Command-line options are mapped to keys for use in Config. E.g., "-h" might
    be mapped to "help." In addition, command-line options are mapped to types,
    which can be "str", "int", "float", or None. Options with a type of None are
    boolean flags with no arguments.

    This mapping is specified as the command_line_mapping argument to __init__.
    Required command-line options are passed in to __init__ as the
    required_command_line_options argument.
    """

    # Constants for config file variables
    source_path              = "source_path"
    company_name             = "company_name"
    product_name             = "product_name"
    contact_email            = "contact_email"
    log_filename             = "log_filename"
    log_to_file              = "log_to_file"
    strings_to_ignore_file   = "strings_to_ignore_file"
    database_adaptor         = "database_adaptor"
    database_path            = "database_path"
    logging_level            = "logging_level"
    vcs_class                = "vcs_class"
    extensions_to_parse      = "extensions_to_parse"
    disallowed_paths         = "disallowed_paths"
    mapping_files            = "mapping_files"
    parsers_by_extension     = "parsers_by_extension"
    output_languages         = "output_languages"
    native_language          = "native_language"
    translation_files_class  = "translation_files_class"
    language_codes           = "language_codes"
    files_by_language        = "files_by_language"
    paths_to_localize        = "paths_to_localize"
    recursive_localization   = "recursive_localization"
    localization_output_dir  = "localization_output_dir"
    extensions_to_localize   = "extensions_to_localize"
    abort_if_no_translations = "abort_if_no_translations"
    xlf_repo_path            = "xlf_repo_path"
    base_localization_paths  = "base_localization_paths"
    proj_path                = "proj_path"

    # Constants for command-line options
    root_path          = "root_path"
    config_filename    = "config_filename"
    print_help         = "print_help"
    platform           = "platform"
    use_vcs            = "use_vcs"
    commit_vcs         = "commit_vcs"

    _config_file_defaults = {
        source_path              : None,
        company_name             : "",
        product_name             : "",
        contact_email            : "",
        strings_to_ignore_file   : strings_to_ignore_file,
        database_adaptor         : None,
        database_path            : None,
        logging_level            : '"info"',
        vcs_class                : '"vcs.NoOp"',
        extensions_to_parse      : None,
        disallowed_paths         : None,
        mapping_files            : None,
        parsers_by_extension     : None,
        output_languages         : None,
        native_language          : None,
        paths_to_localize        : [],
        recursive_localization   : "false",
        localization_output_dir  : None,
        extensions_to_localize   :  [],
        files_by_language        : {},
        translation_files_class  : "translation.XLF",
        abort_if_no_translations : "false",
        xlf_repo_path            : None,
        base_localization_paths  : {},
        proj_path                : "",
        language_codes           : {
            "English"    : "en-US",
            "French"     : "fr-FR",
            "German"     : "de-DE",
            "Italian"    : "it-IT",
            "Japanese"   : "jp-JP",
            "Portuguese" : "pt-PT",
            "Spanish"    : "es-ES",
        }
    }

    _command_line_defaults = {
        config_filename    : "burton.config",
        log_to_file        : False,
        print_help         : False,
        platform           : None,
        use_vcs            : True,
        commit_vcs         : False,
        log_filename       : "None",
    }

    _command_line_mapping = {
        "--config"             : [ config_filename,    "str",  ],
        "--log-to-file"        : [ log_to_file,        None,   ],
        "-h"                   : [ print_help,         None,   ],
        "--help"               : [ print_help,         None,   ],
        "-p"                   : [ platform,           "str",  ],
        "--platform"           : [ platform,           "str",  ],
        "--use-vcs"            : [ use_vcs,            "bool", ],
        "--commit-vcs"         : [ commit_vcs,         None,   ],
        "--log-filename"       : [ log_filename,       "str",  ],
    }

    _required_command_line_options = [ ]

    _custom_methods = {
        extensions_to_parse : [ None, "_add_file_extension_regexes"  ],
        disallowed_paths    : [ None, "_add_disallowed_path_regexes" ],
        mapping_files       : [ None, "_add_mapping_files_regexes"   ],
    }

    def __init__(
        self,
        config_file_defaults          = _config_file_defaults,
        command_line_defaults         = _command_line_defaults,
        command_line_mapping          = _command_line_mapping,
        required_command_line_options = _required_command_line_options,
        custom_methods                = _custom_methods
    ):
        object.__init__(self)
        self._config_file_defaults          = config_file_defaults
        self._command_line_defaults         = command_line_defaults
        self._command_line_mapping          = command_line_mapping
        self._required_command_line_options = required_command_line_options
        self._custom_methods                = custom_methods
        self._config                        = {}
        self._platform_queue                = collections.deque([])

    def parse_command_line_options(self, script_name, options):
        """Parses the command-line options, which are passed in as a list.

        This method takes exactly one option that is not present in
        command_line defaults, and treats this as the root path from which to
        run.
        """
        option_index = 0
        while option_index < len(options):
            current_option = options[option_index]

            if current_option in self._command_line_mapping:
                option_name, option_type =\
                    self._command_line_mapping[current_option]

                if option_type is not None and option_type != "None":
                    option_index += 1
                    if option_index < len(options):
                        if option_type == "str":
                            option_value = str(options[option_index])
                        elif option_type == "int":
                            option_value = int(options[option_index])
                        elif option_type == "float":
                            option_value = float(options[option_index])
                        elif option_type == "bool":
                            option_value = str(options[option_index])
                            if option_value.lower() == "false" or \
                               option_value.lower() == "no":
                                option_value = False
                            else:
                                option_value = bool(options[option_index])
                        else:
                            option_value = options[option_index]

                        self.set(option_name, option_value)
                    else:
                        logger = logging.getLogger(burton.logger_name)
                        logger.error("Missing argument for " + current_option)
                        return False
                else:
                    self.set(option_name, True)
            else:
                if Config.root_path not in self._config:
                    self.set(Config.root_path, current_option)
                else:
                    logger = logging.getLogger(burton.logger_name)
                    logger.error("Unknown option " + current_option)
                    return False

            option_index += 1

        for required_option in self._required_command_line_options:
            if required_option not in self._config:
                logger = logging.getLogger(burton.logger_name)
                logger.error("Missing required option " + required_option)
                return False

        if Config.print_help in self._config:
            logger = logging.getLogger(burton.logger_name)
            logger.error("usage: python " + script_name + " [path] [arguments]")
            logger.error("This application takes the following arguments")
            logger.error(
                "\n\t".join(self._command_line_mapping.keys())
            )
            return False

        for option in self._command_line_defaults:
            if option not in self._config:
                self._config[option] = self._command_line_defaults[option]

        if Config.root_path not in self._config:
            logger = logging.getLogger(burton.logger_name)
            logger.warning("No path found in command-line arguments")
            logger.warning("Using current working directory")
            self._config[Config.root_path] = os.getcwd()

        if Config.platform in self._config and \
           self._config[Config.platform] is not None:
            self._platform_queue.append(self._config[Config.platform])
        else:
            full_path = os.path.join(
                self.get(Config.root_path),
                self.get(Config.config_filename)
            )

            if os.path.exists(full_path):
                fp = self._open_for_reading(full_path)
                print("b")
                parser = ConfigParser.SafeConfigParser(self._config_file_defaults)
                parser.readfp(fp)
                self._platform_queue.extend(parser.sections())

        self._config[Config.platform] = None

        return True

    def num_remaining_platforms(self):
        return len(self._platform_queue)

    def parse_config_file_for_next_platform(self):
        parse_successful = False

        self._config[Config.platform] = None

        if self.num_remaining_platforms() > 0:
            for key in self._config_file_defaults:
                if key in self._config:
                    del self._config[key]

            self._config[Config.platform] = self._platform_queue.popleft()
            parse_successful = self._parse_config_file()

        return parse_successful

    def _parse_config_file(self):
        """This method uses the root_path and config_filename variables set in
        the config to locate the config file, opens it, and passes it to readfp,
        using the platform variable.

        It is designed to be called after a successful call to
        parse_command_line_options
        """
        full_path = os.path.join(
            self.get(Config.root_path),
            self.get(Config.config_filename)
        )

        if os.path.exists(full_path):
            fp = self._open_for_reading(full_path)
            return_value = self.readfp(
                fp,
                self.get(Config.platform)
            )

            fp.close()
            return return_value
        else:
            self.create_new_config_file(full_path)

    def create_new_config_file(self, full_path):
        outfp = self._open_for_writing(full_path)
        infp = self._get_default_config_file()

        outfp.write(infp.read())
        outfp.close()
        infp.close()

        logger = logging.getLogger(burton.logger_name)
        logger.error("An empty config file has been created at " + full_path)
        logger.error(
            "Please fill out the config file and run your command again"
        )

    def readfp(self, fp, platform):
        """The readfp method reads configuration data from a file or file-like
        object for a specific platform.
        """
        parser = ConfigParser.SafeConfigParser(self._config_file_defaults)
        parser.readfp(fp)

        if not parser.has_section(platform):
            logger = logging.getLogger(burton.logger_name)
            logger.error("Unable to parse config file")
            logger.error("Platform " + str(platform) + " does not exist")
            return False

        sections = [ parser.defaults(), dict(parser.items(platform)) ]

        for section in sections:
            for key in section:
                if key not in self._config_file_defaults:
                    logger = logging.getLogger(burton.logger_name)
                    logger.error("Unable to parse config file")
                    logger.error(key + " is not a valid option")
                    return False
                else:
                    value = section[key]
                    if value is not None and value != "None" and len(value) > 0:
                        self.set(key, self._parse_value(value))

        return self._validate_config_file(self._config_file_defaults)

    def set(self, key, value):
        if key in self._custom_methods:
            value = self._apply_custom_method(key, value)
        self._config[key] = value

    def get(self, key):
        return self._config[key]

    def get_strings_to_ignore(self):
        return_value = []

        filename = os.path.join(
            self.get(Config.root_path),
            self.get(Config.strings_to_ignore_file)
        )

        if os.path.exists(filename):
            fp = codecs.open(filename, "r", encoding="utf8")
            return_value = fp.read().split("\n")
            fp.close()

        return return_value

    def _parse_value(self, value):
        if value is not None and value != "None":
            try:
                return json.loads(value)
            except Exception as e:
                raise ValueError("Error parsing '" + value + "': " + str(e))

        return None

    def _validate_config_file(self, validation_dict):
        for key in validation_dict:
            if self._config.get(key, None) is None:
                logger = logging.getLogger(burton.logger_name)
                logger.error("Unable to parse config file")
                logger.error(key + " has not been set")
                return False

        return True

    def _apply_custom_method(self, key, value):
        target, method_name = self._custom_methods[key]
        if target is None:
            target = self

        method = getattr(target, method_name)
        return method(value)

    def _add_file_extension_regexes(self, values):
        return map(
            lambda(extension): re.compile(".*\." + extension + "$"),
            values
        )

    def _add_disallowed_path_regexes(self, values):
        return map(lambda(directory): re.compile(directory), values)

    def _add_mapping_files_regexes(self, values):
        return map(lambda(file): re.compile(file), values)

    def _open_for_reading(self, filename):
        return open(filename, "r")

    def _open_for_writing(self, filename):
        return open(filename, "w")

    def _get_default_config_file(self):
        return resource_stream(__name__, "default.config")

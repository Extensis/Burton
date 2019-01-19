import cProfile
import glob
import logging
import os
import re
import subprocess
import sys

import database
import parser
import translation
import vcs

from config import Config
from logginghandler import BurtonLoggingHandler
from stringmapping import StringMapping

logger_name = "extensis.burton"
logging_handler = BurtonLoggingHandler()

def setup_default_logger():
    logger = logging.getLogger(logger_name)
    sh = logging.StreamHandler(sys.stdout)
    sh.setFormatter(logging.Formatter("[%(levelname)s] %(message)s"))
    logger.addHandler(sh)
    logger.addHandler(logging_handler)

def config_logger(conf):
    logging_levels = {
        "debug"    : logging.DEBUG,
        "info"     : logging.INFO,
        "warning"  : logging.WARNING,
        "error"    : logging.ERROR,
        "critical" : logging.CRITICAL
    }

    logger = logging.getLogger(logger_name)
    logger.setLevel(logging_levels[conf.get(Config.logging_level)])

    log_filename = conf.get(Config.log_filename)
    if log_filename != "None":
        fh = logging.FileHandler(log_filename)
        fh.setFormatter(logging.Formatter("[%(levelname)s] %(message)s"))
        logger.addHandler(fh)

def create_vcs_class(conf):
    vcs_class = _class_from_string(conf.get(Config.vcs_class))()
    return vcs_class

def _class_from_string(class_name):
    if not class_name:
        return None

    parts = class_name.split('.')
    module = ".".join(parts[:-1])
    try:
        cls = __import__(module)
        for part in parts[1:]:
            cls = getattr(cls, part)
        return cls
    except (KeyError, AttributeError) as e:
        return None

def find_all_files(conf):
    """Finds all files recursively under the root directory"""
    return_files = []
    for root, subdirs, files in os.walk("."):
        for file in files:
            disallowed_file = False
            for disallowed_path in conf.get(Config.disallowed_paths):
                if disallowed_path.search(os.path.join(root, file)) is not None:
                    disallowed_file = True

            if not disallowed_file:
                return_files.append(os.path.join(root, file))

    return return_files

def find_files_for_extension(conf, extension):
    """Finds all files recursively under thae root directory with the specified
    extension"""

    return_files = []

    files = find_all_files(conf)
    for file in files:
        if extension.search(file) is not None:
            return_files.append(file)

    return return_files

def _regex_for_extension(conf, extension):
    for allowed_extension in conf.get(Config.extensions_to_parse):
        if allowed_extension.search("." + extension) is not None:
            return allowed_extension

    return None

def extract_strings(conf, strings_to_ignore):
    """Extracts a list of all strings from the files to parse"""
    strings = set([])
    extensions_by_parser = _get_extensions_by_parser(conf)

    logger = logging.getLogger(logger_name)
    logger.info("Extracting strings")

    for parser_name in extensions_by_parser:
        files = []
        for extension in extensions_by_parser[parser_name]:
            regex = _regex_for_extension(conf, extension)
            if regex is not None:
                files.extend(find_files_for_extension(conf, regex))

        strings.update(_extract_strings(parser_name, files, strings_to_ignore))

    return strings

def _extract_strings(parser_name, files, strings_to_ignore):
    strings = set([])
    if len(files) > 0:
        cls = _class_from_string(parser_name)
        parser = cls()
        strings = parser.extract_strings_from_files(files, strings_to_ignore)

    return strings

def _get_extensions_by_parser(conf):
    extensions_by_parser = { }
    for key, value in conf.get(Config.parsers_by_extension).iteritems():
        extensions_by_parser[value] = extensions_by_parser.get(value, [])
        extensions_by_parser[value].append(key)

    return extensions_by_parser

def extract_mapping(conf, strings_to_ignore):
    """Extracts a mapping of strings to native-language translations"""
    reference_mapping = StringMapping()
    extensions_by_parser = _get_extensions_by_parser(conf)

    logger = logging.getLogger(logger_name)
    logger.info("Extracting string mapping")

    for parser_name in extensions_by_parser:
        files = []
        for extension in extensions_by_parser[parser_name]:
            regex = re.compile("\." + extension + "$")
            candidate_files = find_files_for_extension(conf, regex)
            for file in candidate_files:
                if _is_mapping_file(file, conf):
                    files.append(file)

        reference_mapping.combine_with(
            _extract_mapping(parser_name, files, strings_to_ignore)
        )

    return reference_mapping

def _extract_mapping(parser_name, files, strings_to_ignore):
    reference_mapping = StringMapping()
    if len(files) > 0:
        cls = _class_from_string(parser_name)
        parser = cls()
        reference_mapping = parser.extract_string_mapping_from_files(
            files,
            strings_to_ignore
        )

    return reference_mapping

def _is_mapping_file(file, conf):
    for regex in conf.get(Config.mapping_files):
        if regex.search(file) is not None:
            return True

    return False

def check_for_unmapped_strings(extracted_strings, string_mapping):
    """Logs a warning for each string that does not have a native translation"""
    unmapped_strings = [ ]
    missing_strings  = [ ]
    logger           = logging.getLogger(logger_name)

    logger.info("Checking for unmapped strings")
    for string in extracted_strings:
        if string not in string_mapping:
            unmapped_strings.append(string)

    if len(unmapped_strings) > 0:
        logger.warning(
            "The following strings have not been mapped to a native string"
        )
        logger.warning("\t" + "\n\t".join(unmapped_strings) + "\n")

def update_base_localizations(conf, vcs_class):
    patterns = conf.get(Config.base_localization_paths)
    for pattern in patterns:
        paths = glob.glob(pattern)
        for path in paths:
            output_path = path.rsplit('.', 1)[0] + '.strings'
            output_path = output_path.replace('Base.lproj', 'en.lproj')

            subprocess.Popen(
                [ "ibtool", path, "--generate-strings-file", output_path ],
                stdout = None,
                stderr = None
            ).wait()

            vcs_class.add_file(output_path)

def update_translation_file(
    conf,
    platform_translation_keys,
    all_translation_keys,
    language,
    vcs_class
):
    translation_file, filename = _open_translation_file_for_language(
        conf,
        language,
        vcs_class
    )
    translation_dict = translation_file.translation_dict

    _add_new_keys_to_translation_file(
        platform_translation_keys,
        translation_dict,
        translation_file
    )

    _remove_unused_strings_from_language_file(
        all_translation_keys,
        translation_dict,
        translation_file,
        filename
    )

    translation_dict = translation_file.translation_dict

    has_translation = False
    for key in translation_dict:
        if translation_dict[key] is not None:
            has_translation = True
            break

    if conf.get(Config.abort_if_no_translations) and not has_translation:
        raise Exception(
            "Attempted to write an XLF file with no translations"
        )

    file = open(filename, "w")
    translation_file.write(file)
    file.close()

    translation_file, filename = _open_translation_file_for_language(
        conf,
        language,
        vcs_class
    )

    _check_for_untranslated_strings(translation_file, filename)

def _add_new_keys_to_translation_file(
    translation_keys,
    translation_dict,
    translation_file
):
    replaced_translation_keys = [ ]
    for key in translation_keys:
        filtered_string, replaced_params = parser.replace_params(key)
        replaced_translation_keys.append(filtered_string)

    translation_keys = replaced_translation_keys

    for translation_key in translation_keys:
        if translation_key not in translation_dict:
            translation_file.add_translation(translation_key, None)

def _remove_unused_strings_from_language_file(
    translation_keys,
    translation_dict,
    translation_file,
    filename
):
    replaced_translation_keys = []
    strings_to_remove         = []

    for key in translation_keys:
        replaced_key, replaced_params = parser.replace_params(key)
        replaced_translation_keys.append(replaced_key)

    for key in translation_dict:
        if key is not None and key not in replaced_translation_keys and \
          translation_dict[key] is None:
            strings_to_remove.append(key)

    if len(strings_to_remove) > 0:
        logger = logging.getLogger(logger_name)
        logger.info(
            "The following unused, untranslated strings were removed from " +
                filename
        )
        logger.info("\t" +  "\n\t".join(strings_to_remove) + "\n")

    for string in strings_to_remove:
        translation_file.delete_translation(string)

def _check_for_untranslated_strings(translation_file, filename):
    """Logs errors for any untranslated strings in a translation file"""
    untranslated_strings = []
    translation_dict = translation_file.translation_dict
    for key in translation_dict:
        if key is not None and translation_dict[key] is None:
            untranslated_strings.append(key)

    if len(untranslated_strings) > 0:
        logger = logging.getLogger(logger_name)
        logger.warning("There are untranslated strings in " + filename)

def create_localized_resources(conf, native_strings, vcs_class):
    logger = logging.getLogger(logger_name)
    logger.info("Creating localized resources")

    orig_path = os.getcwd()
    os.chdir(conf.get(Config.root_path))

    for language in conf.get(Config.output_languages):
        translation_file, filename = _open_translation_file_for_language(
            conf,
            language,
            vcs_class
        )

        translation_dict = translation_file.translation_dict

        _mark_untranslated_strings(translation_dict)

        translation_dict = _restore_params_to_translation_dict(
            native_strings,
            translation_dict
        )

        paths = []

        if conf.get(Config.recursive_localization):
            for root, dirs, files in os.walk(conf.get(Config.source_path)):
                for dir in dirs:
                    paths.append(os.path.join(root, dir))

                paths.append(root)
        else:
            paths = conf.get(Config.paths_to_localize)

        for path in paths:
            path = os.path.join(conf.get(Config.root_path), path)
            for listing in os.listdir(path):
                disallowed_file = False
                for disallowed_path in conf.get(Config.disallowed_paths):
                    if disallowed_path.search(listing) is not None:
                        disallowed_file = True

                if disallowed_file:
                    continue

                for extension in conf.get(Config.extensions_to_localize):
                    if listing.endswith(extension):
                        localized_resource = _get_localized_resource_instance(
                            conf,
                            extension
                        )

                        output_dir = conf.get(Config.localization_output_dir)
                        if output_dir == "None":
                            output_dir = path
                        else:
                            output_dir = os.path.join(
                                conf.get(Config.root_path),
                                output_dir
                            )

                        localized_resource.translate(
                            os.path.join(path, listing),
                            output_dir,
                            translation_dict,
                            language,
                            conf.get(Config.language_codes)[language],
                            conf.get(Config.use_vcs),
                            vcs_class,
                            conf.get(Config.proj_path)
                        )

    os.chdir(orig_path)

def _get_localized_resource_instance(conf, extension):
    cls = _class_from_string(conf.get(Config.parsers_by_extension)[extension])
    return cls()

def _open_translation_file_for_language(conf, language, vcs_class):
    filename = conf.get(Config.files_by_language)[language]

    cls = _class_from_string(conf.get(Config.translation_files_class))
    translation_file = cls(
        language,
        conf.get(Config.language_codes)[language],
        conf.get(Config.language_codes)[conf.get(Config.native_language)],
        conf.get(Config.company_name),
        conf.get(Config.product_name),
        conf.get(Config.contact_email)
    )

    xlf_repo_path = os.path.abspath(conf.get(Config.xlf_repo_path))

    full_path = os.path.join(xlf_repo_path, filename)
    if os.path.exists(full_path):
        if conf.get(Config.use_vcs):
            vcs_class.add_file(filename, xlf_repo_path)

        file = open(full_path, "r")
        translation_file.read(file)
        file.close()

    return translation_file, full_path

def _restore_params_to_translation_dict(native_strings, translation_dict):
    """Strings stored in the translation files are filtered so that all
    format placeholders (e.g. "%d", "{0}") are replaced with incrementing
    placeholders "{0}", "{1}", etc. This allows us to use the same string with
    different formats across multiple platforms but only send one string for
    translation. See burton.parser.util.replace_params for more information on
    how strings are filtered.

    However, strings in the database are stored unchanged. This allows us to
    map the strings from the translation file to the original strings. We back
    into this by performing the same filtering on a copy of the original
    string and then searching the translation file for that string.

    This function modifies the translation dictionary passed into it in-place
    and then returns it.
    """
    for key in native_strings:
        replaced_key, replaced_params = parser.replace_params(key)
        if replaced_key in translation_dict and len(replaced_params) > 0 \
          and translation_dict[replaced_key] is not None \
          and replaced_key != key:
            translation_dict[key] = parser.restore_platform_specific_params(
                translation_dict[replaced_key],
                replaced_params,
            )

    return translation_dict

def _mark_untranslated_strings(translation_dict):
    """Marks all untranslated keys as untranslated by surrounding them with
    lte and gte symbols.

    This function modifies the translation dictionary passed into it in-place
    and then returns it.
    """
    # This was a requirement when burton was written, but may be an unwanted
    # side effect for other projects that adopt burton. We should replace it
    # with something more flexible.

    for key in translation_dict:
        if key is not None and translation_dict[key] is None:
            translation_dict[key] = u"\u2264" + key + u"\u2265"

    return translation_dict

def _create_config_instance():
    return Config()

def _create_db_instance(conf):
    return database.SQLite(os.path.join(
        os.path.abspath(conf.get(Config.xlf_repo_path)),
        conf.get(Config.database_path)
    ))

def run():
    setup_default_logger()
    logger = logging.getLogger(logger_name)
    conf = _create_config_instance()
    if not conf.parse_command_line_options(sys.argv[0], sys.argv[1:]):
        logger.error("Unable to parse command-line options")
        exit(1)

    elif conf.num_remaining_platforms() <= 0:
        logger.error("No platforms found in config file")
        exit(1)

    orig_path = os.getcwd()

    while conf.num_remaining_platforms() > 0:
        os.chdir(orig_path)

        if not conf.parse_config_file_for_next_platform():
            platform = conf.get(Config.platform)
            if platform is not None:
                logger.error(
                    "Unable to parse config file for platform " + platform
                )
            else:
                logger.error("Unable to determine next platform in config file")

        else:
            xlf_repo_path = os.path.abspath(conf.get(Config.xlf_repo_path))
            if not os.path.isdir(xlf_repo_path):
                logger.error("XLF repo path does not exist at " + xlf_repo_path)
                logger.error("Please clone it to this location")
                exit(1)

            config_logger(conf)

            logger.info("Running for platform " + conf.get(Config.platform))

            should_use_vcs = conf.get(Config.use_vcs)
            vcs_class      = create_vcs_class(conf)

            try:
                strings_to_ignore = conf.get_strings_to_ignore()

                os.chdir(conf.get(Config.root_path))

                source_path = conf.get(Config.source_path)
                if source_path != "None":
                    os.chdir(source_path)

                update_base_localizations(conf, vcs_class)

                extracted_strings = extract_strings(conf, strings_to_ignore)
                string_mapping    = extract_mapping(conf, strings_to_ignore)

                check_for_unmapped_strings(extracted_strings, string_mapping)

                os.chdir(orig_path)

                logger.info("Writing string mapping to database")
                db = _create_db_instance(conf)

                if should_use_vcs:
                    db.update_from_vcs(vcs_class, xlf_repo_path)

                db.connect()
                db.write_string_mapping_for_platform(
                    conf.get(Config.platform),
                    string_mapping.string_mapping_dict,
                )

                for language in conf.get(Config.output_languages):
                    update_translation_file(
                        conf,
                        db.get_native_translations_for_platform(
                            conf.get(Config.platform)
                        ),
                        db.get_all_native_translations(),
                        language,
                        vcs_class
                   )

                create_localized_resources(
                    conf,
                    db.get_native_translations_for_platform(
                        conf.get(Config.platform)
                    ),
                    vcs_class
                )

                db.disconnect()

                if should_use_vcs:
                    vcs_class.add_file(db.filename, xlf_repo_path)

                if conf.get(Config.commit_vcs):
                    logger.info("Committing changes");
                    vcs_class.commit_changes("Automatic localization commit", xlf_repo_path)
                    vcs_class.upload_changes(xlf_repo_path)
                else:
                    logger.info(
                        "Not commiting changes since --commit-vcs not passed in"
                    )

            except Exception as e:
                logger.exception(e)
                logger.error("Reverting checkout")
                vcs_class.revert_all(xlf_repo_path)
            finally:
                logger.info(
                    "Finished running for platform " + conf.get(Config.platform)
                )

    if logging_handler.max_level > logging.WARNING:
        exit(1)

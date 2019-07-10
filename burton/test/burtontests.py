import codecs
import collections
import copy
import logging
import mock
import os
import testfixtures
import unittest
import re
import sys

import burton

class TestParser(object):
    def __init__(self):
        self.parser_name = "None"

    def extract_strings_from_files(
        self,
        filenames,
        strings_to_ignore = []
    ):
        return list(self.extract_string_mapping_from_files(
            filenames,
            strings_to_ignore
        ).get_string_mapping_dict().keys())

    def extract_string_mapping_from_files(
        self,
        filenames,
        strings_to_ignore = []
    ):
        return_mapping = burton.StringMapping()

        return_mapping.add_mapping("Shared String", "Shared String mapping")
        return_mapping.add_mapping("ignore_this",   "ignore_this mapping"  )

        for file_index in range(1, len(filenames) + 1):
            key = self.parser_name + str(file_index)
            return_mapping.add_mapping(key, key + " mapping")

        for string in strings_to_ignore:
            return_mapping.delete_mapping(string)

        return return_mapping


class TestRCParser(TestParser):
    def __init__(self):
        TestParser.__init__(self)
        self.parser_name = "RCString"


class TestSourceParser(TestParser):
    def __init__(self):
        TestParser.__init__(self)
        self.parser_name = "SourceString"


class BurtonTests(unittest.TestCase):
    def test_class_from_string(self):
        self.assertEquals(burton._class_from_string(None), None)
        self.assertEquals(burton._class_from_string("burton.FakeClass"), None)

        instance = burton._class_from_string(
            "burton.test.burtontests.TestParser"
        )()

        self.assertEquals(type(instance), type(TestParser()))
        self.assertNotEqual(type(instance), type(TestRCParser()))

    def test_create_vcs_class(self):
        conf = mock.Mock()
        conf.get.return_value = "burton.vcs.NoOp"

        self.assertEquals(
            type(burton.create_vcs_class(conf)),
            type(burton.vcs.NoOp())
        )

    def test_find_all_files(self):
        conf = mock.Mock()
        conf.get.return_value = [
            re.compile("build"),
            re.compile("cs")
        ]

        original_cwd = os.getcwd()

        try:
            os.chdir(os.path.join(os.path.dirname(__file__), "filesystem"))

            self.assertEquals(
                burton.find_all_files(conf),
                [
                    "find_this.h",
                    "src/find_this.txt"
                ]
            )
        except Exception as e:
            pass
        finally:
            os.chdir(original_cwd)

    def test_find_files_for_extension(self):
        conf = mock.Mock()
        conf.get.return_value = [
            re.compile("build"),
            re.compile("cs")
        ]

        original_cwd = os.getcwd()
        result = None

        try:
            os.chdir(os.path.join(os.path.dirname(__file__), "filesystem"))
            result = burton.find_files_for_extension(conf, re.compile(".txt$"))
        except Exception as e:
            pass
        finally:
            os.chdir(original_cwd)
            self.assertEquals(result, [ "./src/find_this.txt" ])

    @mock.patch.object(burton, "_get_extensions_by_parser")
    @mock.patch.object(burton, "_regex_for_extension"     )
    @mock.patch.object(burton, "find_files_for_extension" )
    def test_extract_strings(self, find_func, regex_func, extension_func):
        extension_func.return_value = {
            "burton.test.burtontests.TestRCParser"      : [ "rc" ],
            "burton.test.burtontests.TestSourceParser"  : [ "h", "m" ],
        }

        def _regex_for_extension(self, extension):
            return re.compile("." + extension + "$")

        regex_func.side_effect = _regex_for_extension

        def _find_files_for_extension(conf, extension):
            extension = extension.pattern[:-1]
            return [
                "file1" + extension,
                "file2" + extension
            ]

        find_func.side_effect = _find_files_for_extension

        self.assertEquals(
            burton.extract_strings(mock.Mock(), [ "ignore_this" ]),
            set([
                "Shared String",
                "RCString1",
                "RCString2",
                "SourceString1",
                "SourceString2",
                "SourceString3",
                "SourceString4"
            ])
        )

    def test_get_extensions_by_parser(self):
        conf = mock.Mock()
        conf.get.return_value = {
            "rc" : "burton.test.burtontests.TestRCParser",
            "h"  : "burton.test.burtontests.TestSourceParser",
            "m"  : "burton.test.burtontests.TestSourceParser"
        }

        self.assertEquals(
            burton._get_extensions_by_parser(conf),
            {
                "burton.test.burtontests.TestRCParser"      : [ "rc" ],
                "burton.test.burtontests.TestSourceParser"  : [ "h", "m" ],
            }
        )

    def test_regex_for_extension(self):
        conf = mock.Mock()
        return_regex = re.compile(".rc$")

        conf.get.return_value = [ return_regex ]

        self.assertEquals(
            burton._regex_for_extension(conf, "rc"),
            return_regex
        )

        self.assertEquals(
            burton._regex_for_extension(conf, "h"),
            None
        )

    def test_update_base_localizations(self):
        output_filename = "Test.strings"
        config_dict = {
            burton.Config.base_localization_paths: { "Test.storyboard": output_filename }
        }

        def _config_get(key):
            return config_dict[key]

        conf = mock.Mock()
        conf.get.side_effect = _config_get

        vcs_class = mock.Mock()

        original_cwd = os.getcwd()

        try:
            os.chdir(os.path.join(os.path.dirname(__file__), "filesystem"))
            if os.path.exists(output_filename):
                os.remove(output_filename)
            burton.update_base_localizations(conf, vcs_class)
        except Exception as e:
            pass
        finally:
            self.assertTrue(os.path.exists(output_filename))
            self.assertTrue(
                "Test String" in codecs.open(output_filename, "r", "utf-16-le").read()
            )

            vcs_class.add_file.assert_called_with(output_filename)

            os.remove(output_filename)
            os.chdir(original_cwd)

    @mock.patch.object(burton, "_get_extensions_by_parser")
    @mock.patch.object(burton, "find_files_for_extension" )
    def test_extract_mapping(self, find_func, extension_func):
        extension_func.return_value = {
            "burton.test.burtontests.TestRCParser"      : [ "rc" ],
            "burton.test.burtontests.TestSourceParser"  : [ "h", "m" ],
        }

        def _find_files_for_extension(conf, extension):
            extension = extension.pattern[:-1]
            return [
                "file1" + extension,
                "file2" + extension,
                # _find_files_for_extension does not normally return files
                # for different extensions, but we want to test the robustness
                # of this function to filter out unwanted files
                "bogus_file"
            ]

        find_func.side_effect = _find_files_for_extension

        conf = mock.Mock()
        conf.get.return_value = [
            re.compile("\.rc$"),
            re.compile("\.h$"),
            re.compile("\.m$")
        ]

        self.assertEquals(
            burton.extract_mapping(
                conf, [ "ignore_this" ]
            ).get_string_mapping_dict(),
            {
                "Shared String" : "Shared String mapping",
                "RCString1"     : "RCString1 mapping",
                "RCString2"     : "RCString2 mapping",
                "SourceString1" : "SourceString1 mapping",
                "SourceString2" : "SourceString2 mapping",
                "SourceString3" : "SourceString3 mapping",
                "SourceString4" : "SourceString4 mapping"
            }
        )

    def test_check_for_unmapped_strings(self):
        captured_log = testfixtures.LogCapture()

        burton.check_for_unmapped_strings(
            [ "mapped string", "unmapped string" ],
            { "mapped string" : "mapping"        }
        )

        captured_log.check(
            (burton.logger_name, "INFO", "Checking for unmapped strings"),
            (
                burton.logger_name,
                "WARNING",
                "The following strings have not been mapped to a native string"
            ),
            (burton.logger_name, "WARNING", "\tunmapped string\n"),
        )

        captured_log.uninstall()

    @mock.patch("builtins.open")
    @mock.patch.object(burton, "_open_translation_file_for_language")
    def test_update_translation_file(
        self,
        read_func,
        write_func
    ):
        translation_file = burton.translation.Base(
            "English",
            "en",
            "en-us",
            "Test Company",
            "Test Product",
            "foo@eample.com"
        )

        translation_file.add_translation("String1", "Translation for String1")
        translation_file.add_translation("String{0}", None)
        translation_file.add_translation("Missing key", None)

        read_func.return_value = translation_file, "test filename"

        captured_log = testfixtures.LogCapture()

        burton.update_translation_file(
            mock.Mock(),
            [ "String1", "String%d", "String3" ],
            [ "String1", "String%d", "String3" ],
            "English",
            burton.vcs.NoOp()
        )

        self.assertEquals(
            translation_file._translation_dict,
            {
                "String1"   : "Translation for String1",
                "String{0}" : None,
                "String3"   : None,
            }
        )

        captured_log.check(
            (
                burton.logger_name,
                "INFO",
                "The following unused, untranslated strings were removed from test filename"
            ),
            (burton.logger_name, "INFO", "\tMissing key\n"),
            (
                burton.logger_name,
                "WARNING",
                "There are untranslated strings in test filename"
            ),
        )

        captured_log.uninstall()

    @mock.patch("builtins.open")
    @mock.patch.object(burton, "_open_translation_file_for_language")
    def test_update_translation_file_ignores_whitespace_entries(
        self,
        read_func,
        write_func
    ):
        def _open_translation_file(conf, language, vcs_class):
            translation_file = burton.translation.Base(
                "English",
                "en",
                "en-us",
                "Test Company",
                "Test Product",
                "foo@eample.com"
            )
            translation_file.add_translation(
                "String1",
                "Translation for String1"
            )

            return translation_file, "test filename"

        read_func.side_effect = _open_translation_file

        captured_log = testfixtures.LogCapture()

        burton.update_translation_file(
            mock.Mock(),
            [ " ", "String1" ],
            [ " ", "String1" ],
            "English",
            burton.vcs.NoOp()
        )

        captured_log.check()
        captured_log.uninstall()

    @mock.patch.object(os, "listdir")
    @mock.patch.object(burton, "_get_localized_resource_instance")
    @mock.patch.object(burton, "_open_translation_file_for_language")
    def test_create_localized_resources(self, read_func, mock_func, list_func):
        translation_file = mock.Mock()
        translation_file.translation_dict = {
            "String1"      : "Translation for String1",
            "String{0}"    : "Printf-formatted string {0}",
            "String{0}{1}" : "Curly-formatted string {0}{1}",
            "String4"      : None
        }

        read_func.return_value = translation_file, "some_filename"

        config_dict = {
            burton.Config.disallowed_paths        : [ ],
            burton.Config.output_languages        : [ "English" ],
            burton.Config.paths_to_localize       : [ "test_path" ],
            burton.Config.extensions_to_localize  : [ "rc" ],
            burton.Config.localization_output_dir : "None",
            burton.Config.language_codes          : { "English" : "en-us" },
            burton.Config.use_vcs                 : False,
            burton.Config.root_path               : ".",
            burton.Config.recursive_localization  : False,
        }

        def _config_get(key):
            return config_dict.get(key, None)

        conf = mock.Mock()
        conf.get.side_effect = _config_get
        return_instance = mock.Mock()
        mock_func.return_value = return_instance

        list_func.return_value = [ "test_filename.rc" ]

        parts = os.path.splitext("test_filename.rc")
        extension = parts[1].lstrip(".")

        vcs_class = burton.vcs.NoOp()
        burton.create_localized_resources(
            conf,
            [ "String1", "String%d", "String{0}{1}", "String4" ],
            vcs_class
        )

        return_instance.translate.assert_called_with(
            os.path.join(".", "test_path", "test_filename.rc"),
            os.path.join(".", "test_path"),
            {
                "String1"      : "Translation for String1",
                "String%d"     : "Printf-formatted string %d",
                "String{0}"    : "Printf-formatted string {0}",
                "String{0}{1}" : "Curly-formatted string {0}{1}",
                "String4"      : u"\u2264String4\u2265"
            },
            "English",
            "en-us",
            False,
            vcs_class,
            None
        )

        config_dict[burton.Config.localization_output_dir] = "foo"
        burton.create_localized_resources(
            conf,
            [ "String1", "String%d", "String{0}{1}", "String4" ],
            vcs_class
        )

        return_instance.translate.assert_called_with(
            os.path.join(".", "test_path", "test_filename.rc"),
            os.path.join(".", "foo"),
            {
                "String1"      : "Translation for String1",
                "String%d"     : "Printf-formatted string %d",
                "String{0}"    : "Printf-formatted string {0}",
                "String{0}{1}" : "Curly-formatted string {0}{1}",
                "String4"      : u"\u2264String4\u2265"
            },
            "English",
            "en-us",
            False,
            vcs_class,
            None
        )

    def test_get_localized_resource_instance(self):
        conf = mock.Mock()
        conf.get.return_value = { "rc": "burton.test.burtontests.TestRCParser" }
        self.assertEquals(
            type(burton._get_localized_resource_instance(conf, "rc")),
            type(TestRCParser())
        )

    @mock.patch("builtins.open")
    @mock.patch.object(os.path, "exists")
    def test_open_translation_file_for_language(self, exists_func, open_func):
        exists_func.return_value = False

        mock_file = mock.Mock()
        open_func.return_value = mock_file
        xlf_repo_path = "xlf"

        config_dict = {
            burton.Config.files_by_language       : {
                "English" : "English.xlf",
                "French"  : "French.xlf"
            },
            burton.Config.language_codes          : {
                "English" : "en-US",
                "French"  : "fr-FR"
            },
            burton.Config.native_language         : "English",
            burton.Config.translation_files_class : "burton.translation.Base",
            burton.Config.use_vcs                 : False,
            burton.Config.root_path               : ".",
            burton.Config.company_name            : "Test Company",
            burton.Config.product_name            : "Test Product",
            burton.Config.contact_email           : "foo@example.com",
            burton.Config.xlf_repo_path           : xlf_repo_path
        }

        def _config_get(key):
            return config_dict[key]

        conf = mock.Mock()
        conf.get.side_effect = _config_get

        vcs_class = mock.Mock()

        translation_file, filename = burton._open_translation_file_for_language(
            conf,
            "English",
            vcs_class
        )

        self.assertEquals(
            type(translation_file),
            type(burton.translation.Base("English", "en", "en-US", "", "", ""))
        )

        self.assertEquals(
            filename,
            os.path.join(os.path.abspath(xlf_repo_path), "English.xlf")
        )

        self.assertFalse(open_func.called)
        self.assertFalse(mock_file.close.called)
        self.assertFalse(vcs_class.add_file.called)

        exists_func.return_value = True
        config_dict[burton.Config.use_vcs] = True

        translation_file, filename = burton._open_translation_file_for_language(
            conf,
            "English",
            vcs_class
        )

        self.assertEquals(
            type(translation_file),
            type(burton.translation.Base("English", "en", "en-US", "", "", ""))
        )

        self.assertEquals(
            filename,
            os.path.join(os.path.abspath(xlf_repo_path), "English.xlf")
        )

        open_func.assert_called_with(
            os.path.join(os.path.abspath(xlf_repo_path), "English.xlf"),
            "r"
        )
        self.assertTrue(mock_file.close.called)

        vcs_class.add_file.assert_called_with(
            "English.xlf",
            os.path.abspath(xlf_repo_path)
        )

    @mock.patch("builtins.exit")
    @mock.patch.object(os, "chdir")
    @mock.patch.object(os.path, "isdir")
    @mock.patch.object(burton, "_create_config_instance")
    @mock.patch.object(burton, "setup_default_logger")
    @mock.patch.object(burton, "config_logger")
    @mock.patch.object(burton, "create_vcs_class")
    @mock.patch.object(burton, "update_base_localizations")
    @mock.patch.object(burton, "extract_strings")
    @mock.patch.object(burton, "extract_mapping")
    @mock.patch.object(burton, "check_for_unmapped_strings")
    @mock.patch.object(burton, "_create_db_instance")
    @mock.patch.object(burton, "update_translation_file")
    @mock.patch.object(burton, "create_localized_resources")
    def test_run(
        self,
        create_localized_resources_func,
        update_translation_file_func,
        create_db_instance_func,
        check_for_unmapped_strings_func,
        extract_mapping_func,
        extract_strings_func,
        update_base_localizations_func,
        create_vcs_class_func,
        config_logger_func,
        setup_default_logger_func,
        create_config_instance_func,
        isdir_func,
        chdir_func,
        exit_func
    ):
        ran_all_tests = False
        test_db_name = "burton_test.sql"
        platform_string = "Test-platform"
        xlf_repo_path = "submodule"
        config_dict = {
            burton.Config.use_vcs            : False,
            burton.Config.vcs_class          : "burton.vcs.NoOp",
            burton.Config.commit_vcs         : False,
            burton.Config.root_path          : os.getcwd(),
            burton.Config.database_path      : test_db_name,
            burton.Config.platform           : platform_string,
            burton.Config.output_languages   : [ "French" ],
            burton.Config.logging_level      : "info",
            burton.Config.source_path        : "foo",
            burton.Config.xlf_repo_path      : xlf_repo_path
        }

        isdir_func.return_value = True

        def _config_get(key):
            return config_dict[key]

        conf = mock.Mock()
        conf._platform_queue = collections.deque([platform_string])

        def _num_remaining_platforms():
            return len(conf._platform_queue)

        def _parse_next():
            return_value = conf._parse_config_file()

            if len(conf._platform_queue) > 0:
                conf._platform_queue.popleft()

            return return_value

        conf.num_remaining_platforms.side_effect = _num_remaining_platforms
        conf.parse_config_file_for_next_platform.side_effect = _parse_next
        conf.get.side_effect = _config_get
        conf.get_string_to_ignore.return_value = [ "Ignore1", "Ignore2" ]
        conf.parse_command_line_options.return_value = True
        conf._parse_config_file.return_value = False

        create_config_instance_func.return_value = conf

        chdir_directories = []
        def _chdir(directory):
            chdir_directories.append(directory)

        chdir_func.side_effect = _chdir

        try:
            burton.run()

            conf._parse_config_file.return_value = True

            vcs_class = mock.Mock()
            create_vcs_class_func.return_value = vcs_class

            mapping = burton.StringMapping()
            mapping.add_mapping("String1", "Mapping1")

            extract_strings_func.return_value = [ "String1" ]
            extract_mapping_func.return_value = mapping

            mock_db = mock.Mock()
            mock_db.get_all_native_translations.return_value = [ "Mapping1" ]
            mock_db.get_native_translations_for_platform.return_value = [
                "Mapping1"
            ]
            create_db_instance_func.return_value = mock_db

            conf._platform_queue = collections.deque([platform_string])
            burton.run()

            self.assertTrue(create_db_instance_func.called)

            self.assertTrue(mock_db.connect.called)
            self.assertFalse(mock_db.update_from_vcs.called)

            cwd = os.getcwd()
            self.assertEquals(
                chdir_directories,
                [
                    cwd,
                    cwd,
                    cwd,
                    "foo",
                    cwd
                ]
            )

            mock_db.write_string_mapping_for_platform.assert_called_with(
                platform_string,
                mapping.string_mapping_dict,
            )

            update_translation_file_func.assert_called_with(
                conf,
                [ "Mapping1" ],
                [ "Mapping1" ],
                "French",
                vcs_class
            )

            create_localized_resources_func.assert_called_with(
                conf,
                [ "Mapping1" ],
                vcs_class
            )

            update_base_localizations_func.assert_called_with(conf, vcs_class)

            self.assertTrue(mock_db.disconnect.called)

            self.assertFalse(vcs_class.commit_changes.called)
            self.assertFalse(vcs_class.upload_changes.called)

            config_dict[burton.Config.use_vcs] = True

            conf._platform_queue = collections.deque([platform_string])
            burton.run()

            self.assertTrue(mock_db.update_from_vcs.called)

            config_dict[burton.Config.commit_vcs] = True

            conf._platform_queue = collections.deque([platform_string])
            burton.run()

            self.assertTrue(vcs_class.commit_changes.called)
            self.assertTrue(vcs_class.upload_changes.called)

            def _throw_exception(conf, native_translations, vcs_class):
                raise Exception("Sample Exception")

            create_localized_resources_func.side_effect = _throw_exception

            captured_log = testfixtures.LogCapture()
            burton.logging_handler.max_level = logging.ERROR
            conf._platform_queue = collections.deque([platform_string])
            burton.run()

            captured_log.check(
                (
                    burton.logger_name,
                    "INFO",
                    "Running for platform Test-platform"
                ),
                (
                    burton.logger_name,
                    'INFO',
                    'Writing string mapping to database'
                ),
                (burton.logger_name, 'ERROR', 'Sample Exception'),
                (burton.logger_name, 'ERROR', 'Reverting checkout'),
                (
                    burton.logger_name,
                    "INFO",
                    "Finished running for platform Test-platform"
                )
            )
            captured_log.uninstall()

            exit_func.assert_called_with(1)

            ran_all_tests = True

        except Exception as e:
            print(e)
            self.assertFalse(True)
        finally:
            if os.path.exists(test_db_name):
                os.remove(test_db_name)

            self.assertTrue(ran_all_tests)

    @mock.patch("builtins.exit")
    @mock.patch.object(burton, "_create_config_instance")
    def test_run_fails_if_there_are_no_platforms_in_config_file(
        self,
        create_config_instance_func,
        exit_func
    ):

        conf = mock.Mock()
        conf.num_remaining_platforms.return_value = 0
        create_config_instance_func.return_value = conf

        captured_log = testfixtures.LogCapture()
        burton.run()

        captured_log.check(
            (
                burton.logger_name,
                "ERROR",
                "No platforms found in config file"
            )
        )

        captured_log.uninstall()

        exit_func.assert_called_with(1)

    @mock.patch("builtins.exit")
    @mock.patch.object(burton, "_create_config_instance")
    def test_exits_if_command_line_arguments_cannot_be_parsed(
        self,
        create_config_instance_func,
        exit_func
    ):
        conf = mock.Mock()
        conf.parse_command_line_options.return_value = False
        conf.num_remaining_platforms.return_value    = 0
        create_config_instance_func.return_value     = conf

        captured_log = testfixtures.LogCapture()
        burton.run()

        captured_log.check(
            (
                burton.logger_name,
                "ERROR",
                "Unable to parse command-line options"
            )
        )

        captured_log.uninstall()

        exit_func.assert_called_with(1)

    @mock.patch("builtins.exit")
    @mock.patch.object(burton, "_create_config_instance")
    def test_exits_if_cannot_read_platforms_from_config(
        self,
        create_config_instance_func,
        exit_func
    ):
        def _config_get(key):
            return {
                burton.Config.logging_level : "info",
                burton.Config.log_filename  : "None",
                burton.Config.platform      : None
            }[key]

        conf = mock.Mock()
        conf.get.side_effect                         = _config_get
        conf.parse_command_line_options.return_value = True

        conf._platform_queue = collections.deque(["foo"])
        def _parse_next():
            if len(conf._platform_queue) > 0:
                conf._platform_queue.popleft()
            return False

        conf.parse_config_file_for_next_platform.side_effect = _parse_next

        def _num_remaining_platforms():
            return len(conf._platform_queue)

        conf.num_remaining_platforms.side_effect = _num_remaining_platforms

        create_config_instance_func.return_value = conf

        captured_log = testfixtures.LogCapture()
        burton.run()

        captured_log.check(
            (
                burton.logger_name,
                "ERROR",
                "Unable to determine next platform in config file"
            )
        )

        captured_log.uninstall()

        exit_func.assert_called_with(1)

    def test_create_config_instance(self):
        self.assertEquals(
            type(burton._create_config_instance()),
            type(burton.Config())
        )

    @mock.patch.object(burton.database, "SQLite")
    def test_create_db_instance(self, mock_constructor):
        def _config_get(key):
            return {
                burton.Config.xlf_repo_path : "some_path",
                burton.Config.database_path : "some_file"
            }[key]

        conf = mock.Mock()
        conf.get.side_effect = _config_get

        burton._create_db_instance(conf)
        mock_constructor.assert_called_with(
            os.path.join(os.path.abspath("some_path")
            , "some_file")
        )

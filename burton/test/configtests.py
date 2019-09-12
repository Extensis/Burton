import codecs
import collections
import logging
import mock
import os
import re
import testfixtures
import unittest

from io import StringIO

import burton

class ConfigTests(unittest.TestCase):
    def test_set_and_get(self):
        c = burton.Config()
        c.set("a_param", 1)
        self.assertEquals(c.get("a_param"), 1)

    def test_overrides_default_values_with_platform_specific_values(self):
        config_fp = StringIO("""
            [DEFAULT]
            default_param = 0
            overidden_param = 0

            [platform1]
            overidden_param = 1

            [platform2]
            default_param = 2
            overidden_param = 2
        """.replace("    ", ""))

        c = burton.Config({ "default_param" : None, "overidden_param" : None })
        self.assertTrue(c.readfp(config_fp, "platform1"))

        self.assertEquals(c.get("default_param"), 0)
        self.assertEquals(c.get("overidden_param"), 1)

    def test_returns_false_if_missing_required_variable(self):
        config_fp = StringIO("""
            [DEFAULT]
            overidden_param = 0

            [platform1]
            overidden_param = 1
        """.replace("    ", ""))

        captured_log = testfixtures.LogCapture()
        c = burton.Config({ "default_param" : None, "overidden_param" : None })

        self.assertFalse(c.readfp(config_fp, "platform1"))
        captured_log.check(
            (burton.logger_name, "ERROR", "Unable to parse config file"),
            (burton.logger_name, "ERROR", "default_param has not been set"),
        )
        
        captured_log.uninstall()

    def test_returns_false_if_config_file_contains_unknown_variable(self):
        config_fp = StringIO("""
            [DEFAULT]
            default_param = 0
            overidden_param = 0

            [platform1]
            overidden_param = 1
            other_param = 1
        """.replace("    ", ""))

        captured_log = testfixtures.LogCapture()
        c = burton.Config({ "default_param" : None, "overidden_param" : None })

        self.assertFalse(c.readfp(config_fp, "platform1"))
        captured_log.check(
            (burton.logger_name, "ERROR", "Unable to parse config file"),
            (burton.logger_name, "ERROR", "other_param is not a valid option"),
        )
        
        captured_log.uninstall()

    def test_returns_false_if_config_file_does_not_contain_platform(self):
        config_fp = StringIO("""
            [DEFAULT]
            default_param = 0
            overidden_param = 0

            [platform1]
            overidden_param: 1
        """.replace("    ", ""))

        c = burton.Config({ "default_param" : None, "overidden_param" : None })

        captured_log = testfixtures.LogCapture()
        self.assertFalse(c.readfp(config_fp, "platform2"))
        captured_log.check(
            (burton.logger_name, "ERROR", "Unable to parse config file"),
            (burton.logger_name, "ERROR", "Platform platform2 does not exist"),
        )
        
        captured_log.uninstall()

    def test_parses_json_values(self):
        config_fp = StringIO("""
            [DEFAULT]
            default_param = [ "1", 2, "three" ]
            overidden_param = 0

            [platform1]
            overidden_param = { "1" : "one", "2" : "two" }
        """.replace("    ", ""))

        c = burton.Config({ "default_param" : None, "overidden_param" : None })
        self.assertTrue(c.readfp(config_fp, "platform1"))

        self.assertEquals(c.get("default_param"), [ "1", 2, "three" ])
        self.assertEquals(
            c.get("overidden_param"),
                { "1" : "one", "2" : "two" }
            )

    def test_calls_custom_methods_for_specified_keys(self):
        config_fp = StringIO("""
            [DEFAULT]
            default_param = 0
            overidden_param = 0

            [platform1]
            overidden_param = 1
        """.replace("    ", ""))

        target = mock.Mock()
        target.custom_method = mock.Mock()

        c = burton.Config(
            config_file_defaults = {
                "default_param" : None,
                "overidden_param" : None
            },
            custom_methods = {
                "default_param" : [ target, "custom_function" ]
            },
        )

        self.assertTrue(c.readfp(config_fp, "platform1"))
        target.custom_function.assert_called_with(0)

    def test_creates_regexes_from_file_extensions(self):
        config_fp = StringIO("""
            [DEFAULT]
            extensions_to_parse = [ ]

            [platform1]
            extensions_to_parse = [ "resx", "nib" ]
        """.replace("    ", ""))

        c = burton.Config({ burton.Config.extensions_to_parse : None })

        self.assertTrue(c.readfp(config_fp, "platform1"))
        self.assertEquals(
            [regex.pattern for regex in c.get(burton.Config.extensions_to_parse)],
            [ ".*\.resx$", ".*\.nib$" ]
        )

    def test_creates_regexes_from_disallowed_paths(self):
        config_fp = StringIO("""
            [DEFAULT]
            disallowed_paths = [ ]

            [platform1]
            disallowed_paths = [ "Shared Code/cpp_core/output", "build"]
        """.replace("    ", ""))

        c = burton.Config({ burton.Config.disallowed_paths : None })

        self.assertTrue(c.readfp(config_fp, "platform1"))
        self.assertEquals(
            [regex.pattern for regex in c.get(burton.Config.disallowed_paths)],
            [ "Shared Code/cpp_core/output", "build" ]
        )

    def test_creates_regexes_from_mapping_files(self):
        config_fp = StringIO("""
            [DEFAULT]
            mapping_files = [ ]

            [platform1]
            mapping_files = [ "\\\\.strings$", "\\\\.rc$", "\\\\.resx$" ]
        """.replace("    ", ""))

        c = burton.Config({ burton.Config.mapping_files : [ ] })

        self.assertTrue(c.readfp(config_fp, "platform1"))
        self.assertEquals(
            [regex.pattern for regex in c.get(burton.Config.mapping_files)],
            [ "\\.strings$", "\\.rc$", "\\.resx$" ]
        )

    def test_parse_command_line_options(self):
        c = burton.Config(
            command_line_defaults = {
                "first_option"                : None,
                "second_option"               : 0,
                "third_option"                : 0.0,
                "fourth_option"               : False,
                "fifth_option"                : False,
                "o"                           : False,
                "w"                           : False,
                "t"                           : False,
                burton.Config.print_help      : False,
                burton.Config.config_filename : "burton.config",
            },
            command_line_mapping = {
                "--option1" : [ "first_option",              "str"    ],
                "--option2" : [ "second_option",             "int"    ],
                "--option3" : [ "third_option",              "float", ],
                "--option4" : [ "fourth_option",             "bool",  ],
                "--option5" : [ "fifth_option",              "bool",  ],
                "-o"        : [ "o",                         None,    ],
                "-t"        : [ "t",                         "other", ],
                "-w"        : [ "w",                         None,    ],
                "--help"    : [ burton.Config.print_help,    None,    ],
            },
            required_command_line_options = [],
        )

        self.assertTrue(
            c.parse_command_line_options(
                "script_name",
                [
                    "some_path",
                    "--option1", "value1",
                    "--option2", 2,
                    "--option3", 3.0,
                    "--option4", "false",
                    "--option5", 0,
                    "-o",
                    "-t", 1,
                ],
            )
        )

        self.assertEquals(c.get(burton.Config.root_path), "some_path")
        self.assertEquals(c.get("first_option"),  "value1")
        self.assertEquals(c.get("second_option"), 2)
        self.assertEquals(c.get("third_option"),  3.0)
        self.assertEquals(c.get("fourth_option"), False)
        self.assertEquals(c.get("fifth_option"), False)
        self.assertEquals(c.get("o"), True)
        self.assertEquals(c.get("t"),  1)
        self.assertEquals(c.get("w"),  False)

        captured_log = testfixtures.LogCapture()
        self.assertFalse(c.parse_command_line_options(
            "script_name",
            ["--help"]
        ))

        captured_log.check(
            (
                burton.logger_name,
                "ERROR",
                "usage: python script_name [path] [arguments]"
            ),
            (
                burton.logger_name,
                "ERROR",
                "This application takes the following arguments"
            ),
            (
                burton.logger_name,
                "ERROR",
                "\n\t".join(list(c._command_line_mapping.keys()))
            )
        )
        
        captured_log.uninstall()

    def test_returns_false_if_missing_required_command_line_options(self):
        c = burton.Config(
            command_line_defaults = {
                "foo"  : None,
            },
            command_line_mapping = {
                "--foo" : [ "foo",  "str" ],
            },
            required_command_line_options = [ "foo" ],
        )

        captured_log = testfixtures.LogCapture()
        self.assertFalse(c.parse_command_line_options("script_name", [ ]))
        captured_log.check(
            (burton.logger_name, "ERROR", "Missing required option foo"),
        )
        
        captured_log.uninstall()

        captured_log = testfixtures.LogCapture()
        self.assertFalse(c.parse_command_line_options(
            "script_name",
            [ "some_path", ]
        ))
        captured_log.check(
            (burton.logger_name, "ERROR", "Missing required option foo"),
        )
        
        captured_log.uninstall()

    def test_returns_false_if_encounters_unknown_command_line_options(self):
        c = burton.Config(
            command_line_defaults = { "platform"  : None, },
            command_line_mapping = { "--platform" : [ "platform",  "str" ], },
            required_command_line_options = [ "platform" ],
        )

        captured_log = testfixtures.LogCapture()
        self.assertFalse(c.parse_command_line_options(
            "script_name",
            [ "some_path", "-o" ]
        ))
        captured_log.check(
            ( burton.logger_name, "ERROR", "Unknown option -o" ),
        )
        
        captured_log.uninstall()

    def test_returns_false_if_missing_command_line_arguments(self):
        c = burton.Config(
            command_line_defaults = { "platform"  : None, },
            command_line_mapping = { "--platform" : [ "platform",  "str" ], },
            required_command_line_options = [ "platform" ],
        )

        captured_log = testfixtures.LogCapture()
        self.assertFalse(c.parse_command_line_options(
            "script_name",
            [ "some_path", "--platform" ]
        ))
        captured_log.check(
            (burton.logger_name, "ERROR", "Missing argument for --platform"),
        )
        
        captured_log.uninstall()

    def test_uses_defaults(self):
        config_fp = StringIO("""
            [DEFAULT]
            [platform1]
        """.replace("    ", ""))

        c = burton.Config(
            config_file_defaults  = { "default_param" : '"default_value"' },
            command_line_defaults = { "platform"  : "Mac", },
            command_line_mapping  = { "--platform" : [ "platform",  "str" ], },
            required_command_line_options = [  ],
        )

        self.assertTrue(c.parse_command_line_options(
            "script_name",
            [ "some_path" ]
        ))
        self.assertTrue(c.readfp(config_fp, "platform1"))

        self.assertEquals(c.get("default_param"), "default_value")
        self.assertEquals(c._platform_queue, collections.deque(["Mac"]))

    @mock.patch.object(os.path, "exists")
    def test_parse_config_file(self, mock_path_exists_func):
        config_fp = StringIO("""
            [DEFAULT]
            [platform1]
        """.replace("    ", ""))

        c                                  = burton.Config()
        c._open_for_reading                = mock.Mock(return_value = config_fp)
        c.readfp                           = mock.Mock(return_value = True)
        mock_path_exists_func.return_value = True

        c.set(burton.Config.root_path, "some_path")
        c.set(burton.Config.config_filename, "some_filename")
        c.set(burton.Config.platform, "Mac")

        self.assertTrue(c._parse_config_file())
        c.readfp.assert_called_with(config_fp, "Mac")
        c._open_for_reading.assert_called_with(
            os.path.join("some_path", "some_filename")
        )

    @mock.patch.object(os.path, "exists")
    def test_parse_config_file_creates_new_file_when_necessary(
        self,
        mock_path_exists_func
    ):
        c                                  = burton.Config()
        c.create_new_config_file           = mock.Mock()
        mock_path_exists_func.return_value = False

        c.set(burton.Config.root_path, "some_path")
        c.set(burton.Config.config_filename, "some_filename")
        c.set(burton.Config.platform, "Mac")

        self.assertFalse(c._parse_config_file())
        c.create_new_config_file.assert_called_with(
            os.path.join("some_path", "some_filename")
        )

    def test_create_new_config_file(self):
        lines = []
        def _write(line):
            lines.append(line.decode())

        write_fp            = mock.Mock()
        write_fp.write      = mock.Mock(side_effect = _write)
        c                   = burton.Config()
        c._open_for_writing = mock.Mock(return_value = write_fp)

        captured_log = testfixtures.LogCapture()
        c.create_new_config_file("some_path")

        captured_log.check(
            (
                burton.logger_name,
                "ERROR",
                "An empty config file has been created at some_path"
            ),
            (
                burton.logger_name,
                "ERROR",
                "Please fill out the config file and run your command again"
            ),
        )
        
        captured_log.uninstall()

        self.assertEquals(
            str.encode("".join(lines)),
            c._get_default_config_file().read()
        )

    @mock.patch.object(codecs, "open")
    @mock.patch.object(os.path, "exists")
    def test_strings_to_ignore(self, mock_path_exists_func, open_func):
        config_dict = {
            burton.Config.root_path              : "root_path",
            burton.Config.strings_to_ignore_file : "test_filename"
        }

        def _config_get(key):
            return config_dict[key]

        conf = burton.Config()
        conf.get = mock.Mock(side_effect = _config_get)

        mock_path_exists_func.return_value = True
        open_func.return_value = StringIO("""ignore1
ignore2
ignore3""")

        self.assertEquals(
            conf.get_strings_to_ignore(),
            [ "ignore1", "ignore2", "ignore3" ]
        )

        open_func.assert_called_with(
            os.path.join("root_path", "test_filename"),
            "r",
            encoding = "utf8"
        )

    def test_parse_value(self):
        c = burton.Config()

        self.assertEquals(c._parse_value(None), None)
        self.assertEquals(c._parse_value("None"), None)
        self.assertEquals(c._parse_value("1"), 1)
        self.assertEquals(c._parse_value('"String"'), "String")
        self.assertEquals(c._parse_value("[1, 2, 3]"), [ 1, 2, 3])

        test_passed = False
        try:
            c._parse_value("[invalid value")
        except ValueError as e:
            test_passed = True
        finally:
            self.assertTrue(test_passed)

    @mock.patch("builtins.open")
    def test_open_for_reading(self, open_func):
        c = burton.Config()
        c._open_for_reading("filename")

        open_func.assert_called_with("filename", "r")

    @mock.patch("builtins.open")
    def test_open_for_writing(self, open_func):
        c = burton.Config()
        c._open_for_writing("filename")

        open_func.assert_called_with("filename", "w")

    def test_root_path_defaults_to_cwd(self):
        c = burton.Config()
        c.parse_command_line_options("some_script", [])
        self.assertEquals(c.get(burton.Config.root_path), os.getcwd())

    @mock.patch.object(os.path, "exists")
    def test_parse_config_file_for_next_platform(self, mock_path_exists_func):
        def _open_file(filename):
            config_fp = StringIO("""
                [DEFAULT]
                default_param = 0
                overidden_param = 0

                [platform1]
                default_param = 1
                overidden_param = 1

                [platform2]
                overidden_param = 2
            """.replace("    ", ""))
            return config_fp

        mock_path_exists_func.return_value = True

        c = burton.Config({ "default_param" : None, "overidden_param" : None })
        c._open_for_reading = mock.Mock(side_effect = _open_file)

        c.parse_command_line_options("some_script", [])

        self.assertEquals(c.num_remaining_platforms(), 2)

        c.parse_config_file_for_next_platform()
        self.assertEquals(c.get("default_param"), 1)
        self.assertEquals(c.get("overidden_param"), 1)

        c.parse_config_file_for_next_platform()
        self.assertEquals(c.get("default_param"), 0)
        self.assertEquals(c.get("overidden_param"), 2)

import mock
import os
import unittest

import vcs

class PerforceTests(unittest.TestCase):
    def test_update_path(self):
        perforce = vcs.Perforce()
        perforce._run_command = mock.Mock()

        perforce.update_path("some_path")

        perforce._run_command.assert_called_with(
            [ "sync", os.path.abspath("some_path") + "/...#head" ]
        )

        def _file_already_added(*args, **kwargs):
            raise vcs.VCSException([{
                "code" : "error",
                "data" : "some_other_path: file(s) up-to-date"
            }])

        perforce._run_command.side_effect = _file_already_added

        perforce.update_path("some_other_path")

        perforce._run_command.assert_called_with(
            [ "sync", os.path.abspath("some_other_path") + "/...#head" ]
        )

        def _no_such_file(*args, **kwargs):
            raise vcs.VCSException([{
                "code" : "error",
                "data" : "some_other_path: no such file(s)"
            }])

        perforce._run_command.side_effect = _no_such_file

        perforce.update_path("yet_another_path")

        perforce._run_command.assert_called_with(
            [ "sync", os.path.abspath("yet_another_path") + "/...#head" ]
        )

        def _other_error(*args, **kwargs):
            raise vcs.VCSException([{
                "code" : "error",
                "data" : "other_error"
            }])

        perforce._run_command.side_effect = _other_error
        test_succeeded = False

        try:
            perforce.update_path("yet_another_path")
        except vcs.VCSException as e:
            test_succeeded = True
        finally:
            self.assertTrue(test_succeeded)

    def test_add_file(self):
        perforce = vcs.Perforce()
        perforce._run_command = mock.Mock()

        perforce.add_file("some_file")

        perforce._run_command.assert_called_with(
            [ "add", "-f", "-c", "default", os.path.abspath("some_file") ]
        )

    def test_mark_file_for_edit(self):
        perforce = vcs.Perforce()
        perforce._run_command = mock.Mock()

        perforce.mark_file_for_edit("some_file")

        perforce._run_command.assert_called_with(
            [ "edit", "-c", "default", os.path.abspath("some_file") ]
        )

        def _not_on_client(*args, **kwargs):
            raise vcs.VCSException([{
                "code" : "error",
                "data" : "some_file: not on client"
            }])

        perforce._run_command.side_effect = _not_on_client

        perforce.mark_file_for_edit("some_file")

        perforce._run_command.assert_called_with(
            [ "edit", "-c", "default", os.path.abspath("some_file") ]
        )

    def test_commit_changes(self):
        perforce = vcs.Perforce()
        perforce._run_command = mock.Mock()

        perforce.commit_changes("some message")

        perforce._run_command.assert_called_with(
            [ "submit", "-f", "revertunchanged", "-d", "some message" ]
        )

        def _no_files(*args, **kwargs):
            raise vcs.VCSException([{
                "code" : "error",
                "data" : "No files to submit"
            }])

        perforce._run_command.side_effect = _no_files

        perforce.commit_changes("some message")

        perforce._run_command.assert_called_with(
            [ "submit", "-f", "revertunchanged", "-d", "some message" ]
        )

        def _other_error(*args, **kwargs):
            raise vcs.VCSException([{
                "code" : "error",
                "data" : "other_error"
            }])

        perforce._run_command.side_effect = _other_error
        test_succeeded = False

        try:
            perforce.commit_changes("some message")
        except vcs.VCSException as e:
            test_succeeded = True
        finally:
            self.assertTrue(test_succeeded)

    @mock.patch.object(os.path, "isdir")
    def test_revert(self, mock_func):
        perforce = vcs.Perforce()
        perforce._run_command = mock.Mock()
        mock_func.return_value = False

        def _file_not_opened(*args, **kwargs):
            raise vcs.VCSException([{
                "code" : "error",
                "data" : "some_file: file(s) not opened on this client."
            }])

        perforce._run_command.side_effect = _file_not_opened

        perforce.revert("some_file")

        perforce._run_command.assert_called_with(
            [ "revert", os.path.abspath("some_file") ]
        )

        mock_func.return_value = True

        perforce.revert("some_path")

        perforce._run_command.assert_called_with(
            [ "revert", os.path.abspath("some_path") + "/..." ]
        )

    @mock.patch.object(os.path, "isdir")
    def test_revert_unchanged(self, mock_func):
        perforce = vcs.Perforce()
        perforce._run_command = mock.Mock()
        mock_func.return_value = False

        def _file_not_opened(*args, **kwargs):
            raise vcs.VCSException([{
                "code" : "error",
                "data" : "some_file: file(s) not opened on this client."
            }])

        perforce._run_command.side_effect = _file_not_opened

        perforce.revert_unchanged("some_file")

        perforce._run_command.assert_called_with(
            [ "revert", "-a", os.path.abspath("some_file") ]
        )

        mock_func.return_value = True

        perforce.revert_unchanged("some_path")

        perforce._run_command.assert_called_with(
            [ "revert", "-a", os.path.abspath("some_path") + "/..." ]
        )

        def _some_other_error(*args, **kwargs):
            raise vcs.VCSException([{
                "code" : "error",
                "data" : "some_file: some other error."
            }])

        perforce._run_command.side_effect = _some_other_error
        caught_exception = False

        try:
            perforce.revert_unchanged("some_path")
        except vcs.VCSException as e:
            caught_exception = True

        self.assertTrue(caught_exception)


    def test_run_command(self):
        perforce = vcs.Perforce()
        perforce._run_command([ "help" ])

        caught_exception = False

        try:
            perforce._run_command([ "fake_command" ])
        except vcs.VCSException as e:
            caught_exception = True

        self.assertTrue(caught_exception)

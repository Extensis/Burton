import mock
import os
import unittest

import vcs

class TestStdout():
    def read(self):
        return 'modified'

class TestPipe():
    def __init__(self):
        self.stdout = TestStdout();

class GitTests(unittest.TestCase):

    def test_add_file(self):
        git = vcs.Git()
        git._run_command = mock.Mock()

        filename = 'some_file'
        git.add_file(filename)

        git._run_command.assert_called_with(
            [ 'add', filename ],
            None
        )
        
        xlf_repo_path = 'xlf_repo_path';
        
        git.add_file(filename, xlf_repo_path)
        
        git._run_command.assert_called_with(
            [ 'add', filename ],
            xlf_repo_path
        )

    def test_commit_changes(self):
        git = vcs.Git()
        git._run_command = mock.Mock()
        git._run_command_and_return_output_pipe = mock.Mock(return_value = TestPipe())
        xlf_repo_path = 'xlf_repo_path'
        commit_message = 'some message'

        git.commit_changes(commit_message, xlf_repo_path)

        git._run_command_and_return_output_pipe.assert_has_calls([
            mock.call(
                [ "status", "-uno", "--porcelain" ],
                xlf_repo_path
            ),
            mock.call(
                [ "status", "-uno", "--porcelain" ]
            )
        ])
        
        git._run_command.assert_has_calls([
            mock.call(
                [ "commit", "-m", commit_message ],
                xlf_repo_path
            ),
            mock.call(
                [ "push", "origin", "HEAD" ],
                xlf_repo_path
            ),
            mock.call(
                [ "commit", "-m", commit_message ]
            ),
            mock.call(
                [ "push", "origin", "HEAD" ]
            )
        ])

    def test_revert(self):
        git = vcs.Git()
        git._run_command = mock.Mock()
        filename = 'some_file'
        xlf_repo_path = 'xlf_repo_path'

        git.revert(filename)

        git._run_command.assert_any_call(
            [ "reset", "HEAD", filename ],
            None
        )
        
        git._run_command.assert_called_with(
            [ "checkout", filename ],
            None
        )

        git.revert(filename, xlf_repo_path)

        git._run_command.assert_any_call(
            [ "reset", "HEAD", filename ],
            xlf_repo_path
        )
        
        git._run_command.assert_called_with(
            [ "checkout", filename ],
            xlf_repo_path
        )
    
    def test_revert_all(self):
        git = vcs.Git()
        git._run_command = mock.Mock()
        xlf_repo_path = 'xlf_repo_path'

        git.revert_all(xlf_repo_path)

        git._run_command.assert_any_call(
            [ "reset", "--hard" ],
            xlf_repo_path
        )
        
        git._run_command.assert_called_with(
            [ "reset", "--hard" ]
        )

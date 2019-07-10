import marshal
import os
import re
import subprocess
import sys

from .noop import NoOp
from .vcsexception import VCSException

class Git(NoOp):
    def __init__(self):
        NoOp.__init__(self)

    def add_file(self, file, xlf_repo_path = None):
        self._run_command(
            [ "add", file ],
            xlf_repo_path
        )

    def commit_changes(self, message, xlf_repo_path = None):
        if xlf_repo_path is not None:        
            pipe = self._run_command_and_return_output_pipe(
                [ "status", "-uno", "--porcelain" ],
                xlf_repo_path
            )
    
            if pipe.stdout.read() != '':
                self._run_command(
                   [ "commit", "-m", message ],
                   xlf_repo_path
                )
        
                self._run_command(
                    [ "push", "origin", "HEAD" ],
                    xlf_repo_path
                )
    
        pipe = self._run_command_and_return_output_pipe(
            [ "status", "-uno", "--porcelain" ]
        )
        
        if pipe.stdout.read() == '':
            return
    
        self._run_command(
           [ "commit", "-m", message ]
        )
        
        self._run_command(
            [ "push", "origin", "HEAD" ]
        )

    def revert_all(self, xlf_repo_path = None):
        if xlf_repo_path is not None:
            self._run_command([ "reset", "--hard" ], xlf_repo_path)
    
        self._run_command([ "reset", "--hard" ])

    def revert(self, path, xlf_repo_path = None):
        self._run_command([ "reset", "HEAD", path ], xlf_repo_path)
        self._run_command([ "checkout", path ], xlf_repo_path)

    def _run_command(self, commands, xlf_repo_path = None):
        cwd = os.getcwd()
        if xlf_repo_path is not None:
            os.chdir(xlf_repo_path)

        self._check_for_errors(self._run_command_and_return_output_pipe(commands))
        
        if xlf_repo_path is not None:
            os.chdir(cwd)

    def _run_command_and_return_output_pipe(self, commands, xlf_repo_path = None):
        cwd = os.getcwd();
        if xlf_repo_path is not None:
            os.chdir(xlf_repo_path)
        
        commands.insert(0, "git")

        pipe = subprocess.Popen(
            commands,
            stdout = subprocess.PIPE,
            stderr = subprocess.STDOUT,
        )
        
        pipe.wait()
        
        if cwd is not None:
            os.chdir(cwd)
        
        return pipe

    def _check_for_errors(self, pipe):
        if pipe.returncode != 0:
            raise VCSException(pipe.stdout.read())

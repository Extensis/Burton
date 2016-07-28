import marshal
import os
import re
import subprocess
import sys

from noop import NoOp
from vcsexception import VCSException

class Git(NoOp):
    def __init__(self):
        NoOp.__init__(self)

    def add_file(self, file, submodule_path = None):
        file = self._get_relative_submodule_path(file, submodule_path)
        self._run_command(
            [ "add", file ],
            submodule_path
        )
    
    def mark_file_for_edit(self, file, submodule_path = None):
        self.add_file(file, submodule_path)

    def commit_changes(self, message):
        for submodule_path in self.submodule_paths:
            self._run_command(
                [ "add", submodule_path ]
            )
        
            cwd = os.getcwd()
            os.chdir(submodule_path)
            
            pipe = self._run_command_and_return_output_pipe(
                [ "status", "-uno", "--porcelain" ]
            )
        
            if pipe.stdout.read() == '':
                os.chdir(cwd)
                continue
            
            self._run_command(
               [ "commit", "-m", message ]
            )
            
            self._run_command(
                [ "push", "origin", "HEAD" ]
            )
            
            os.chdir(cwd)
            
            self._run_command(
                [ "add", submodule_path ]
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

    def revert_all(self):
        for submodule_path in self.submodule_paths:
            cwd = os.getcwd()
            os.chdir(submodule_path)
            
            self._run_command([ "reset", "-hard" ])
            
            os.chdir(cwd)
    
        self._run_command([ "reset", "-hard" ])

    def revert(self, path, submodule_path = None):
        path = self._get_relative_submodule_path(path, submodule_path)
        self._run_command([ "reset", "HEAD", path ], submodule_path)
        self._run_command([ "checkout", path ], submodule_path)

    def _run_command(self, commands, submodule_path = None):
        cwd = os.getcwd()
        if submodule_path is not None:
            os.chdir(submodule_path)

        self._check_for_errors(self._run_command_and_return_output_pipe(commands))
        
        if submodule_path is not None:
            os.chdir(cwd)

    def _run_command_and_return_output_pipe(self, commands):
        commands.insert(0, "git")

        pipe = subprocess.Popen(
            commands,
            stdout = subprocess.PIPE,
            stderr = subprocess.STDOUT,
        )
        
        pipe.wait()
        
        return pipe

    def _check_for_errors(self, pipe):
        if pipe.returncode != 0:
            raise VCSException(pipe.stdout.read())
    
    def _get_relative_submodule_path(self, path, submodule_path):
        if submodule_path is not None:
            return os.path.relpath(os.path.abspath(path), os.path.abspath(submodule_path))
        else:
            return os.path.abspath(path)

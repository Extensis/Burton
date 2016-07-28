import marshal
import os
import re
import subprocess
import sys

from noop import NoOp
from vcsexception import VCSException

class Perforce(NoOp):
    def __init__(self):
        NoOp.__init__(self)

    def update_path(self, path, submodule_path = None):
        try:
            self._run_command([ "sync", os.path.abspath(path) + "/...#head" ])

        except VCSException as e:
            for exception in e.value:
                regex1 = re.compile("file\(s\) up-to-date")
                regex2 = re.compile("no such file\(s\)")
                if "data" not in exception or (\
                   regex1.search(exception["data"]) is None and \
                   regex2.search(exception["data"]) is None):
                    raise e

    def add_file(self, file, submodule_path = None):
        self._run_command(
            [ "add", "-f", "-c", "default", os.path.abspath(file) ]
        )

    def mark_file_for_edit(self, file, submodule_path = None):
        try:
            self._run_command(
                [ "edit", "-c", "default", os.path.abspath(file) ]
            )

        except VCSException as e:
            for exception in e.value:
                regex = re.compile("not on client")
                if "data" not in exception or \
                   regex.search(exception["data"]) is None:
                    raise e

    def commit_changes(self, message):
        try:
            self._run_command(
               [ "submit", "-f", "revertunchanged", "-d", message ]
            )

        except VCSException as e:
            for exception in e.value:
                regex = re.compile("No files to submit")
                if "data" not in exception or \
                   regex.search(exception["data"]) is None:
                    raise e

    def revert_all(self):
        self._run_revert_command([ "revert", "-c", "default", "//..." ])

    def revert(self, path, submodule_path = None):
        path = self._path_for_revert_command(path)
        self._run_revert_command([ "revert", path ])

    def revert_unchanged(self, path, submodule_path = None):
        path = self._path_for_revert_command(path)
        self._run_revert_command([ "revert", "-a", path ])

    def _path_for_revert_command(self, path):
        path = os.path.abspath(path)

        if os.path.isdir(path):
            path = path + "/..."

        return path

    def _run_revert_command(self, arguments):
        try:
            self._run_command(arguments)

        except VCSException as e:
            regex = re.compile("file\(s\) not opened on this client.")
            for exception in e.value:
                if "data" not in exception or \
                  regex.search(exception["data"]) is None:
                    raise e

    def _run_command(self, commands):
        commands.insert(0, "p4")
        commands.insert(1, "-G")

        stdout = subprocess.Popen(
            commands,
            stdout = subprocess.PIPE,
            stderr = subprocess.STDOUT,
        ).stdout

        self._check_for_errors(stdout)

    def _check_for_errors(self, stdout):
        records = []
        try:
            while True:
                records.append(marshal.load(stdout))

        except EOFError as e:
            pass

        exceptions = []
        for record in records:
            if "code" in record and record["code"] == "error":
                exceptions.append(record)

        if len(exceptions) > 0:
            raise VCSException(exceptions)

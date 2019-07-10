import os
import shutil
import subprocess
import tempfile

from .base import Base
from .strings import Strings

class MacSource(Base):
    def __init__(self):
        Base.__init__(self)

    def extract_strings_from_filename(self, filename):
        output_dir = self._get_output_directory()
        self._run_genstrings_command_for_file(filename, output_dir)

        full_paths = []
        for file in os.listdir(output_dir):
            full_paths.append(os.path.join(output_dir, file))

        strings_parser = Strings()
        return_values = \
            strings_parser.extract_strings_from_files(full_paths)

        shutil.rmtree(output_dir)
        return return_values

    def _run_genstrings_command_for_file(self, filename, output_dir):
        subprocess.Popen(
            [ "genstrings", "-u", "-o", output_dir, filename ],
            stdout = subprocess.PIPE,
            stderr = subprocess.STDOUT,
        ).stdout.read()

    def _get_output_directory(self):
        return tempfile.mkdtemp()

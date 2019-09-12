import codecs
import os
import re
import shutil
import subprocess
import tempfile

from .base import Base
from .strings import Strings

class MacSource(Base):
    def __init__(self):
        Base.__init__(self)

    def extract_strings_from_filename(
        self,
        filename,
        additional_function_names = []
    ):
        output_dir = self._get_output_directory()
        self._run_genstrings_command_for_file(filename, output_dir)

        full_paths = []
        for file in os.listdir(output_dir):
            full_paths.append(os.path.join(output_dir, file))

        strings_parser = Strings()
        return_values = \
            strings_parser.extract_strings_from_files(full_paths)

        shutil.rmtree(output_dir)
        
        if len(additional_function_names) > 0:
            func_exp = '|'.join(additional_function_names)
            regex = u'(%s)\(\s*@?"((?:(?<=\\\\)"|[^"])*)(?<!\\\\)"' % func_exp
            skipping = False
            f = codecs.open(filename, 'r', 'utf-8')
            contents = f.read();
            contents = re.sub('//.*?\n|/\*.*?\*/', '', contents, flags=re.S)
            
            for line in contents.split("\n"):
                line = line.replace('\0', '')
                parseline = line
                match = re.search(regex, parseline, re.UNICODE)
                if match:
                    return_values.add(match.group(2))
        
        return return_values

    def _run_genstrings_command_for_file(self, filename, output_dir):
        subprocess.Popen(
            [ "genstrings", "-u", "-o", output_dir, filename ],
            stdout = subprocess.PIPE,
            stderr = subprocess.STDOUT,
        ).stdout.read()

    def _get_output_directory(self):
        return tempfile.mkdtemp()

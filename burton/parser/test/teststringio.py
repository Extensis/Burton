import os

from io import StringIO

class TestStringIO(StringIO):
    def __init__(self, filename = None, buffer = None):
        print("cwd: " + os.getcwd())
        #print('file: ' + filename)
        StringIO.__init__(self, buffer)
        self.name = filename

    def close(self):
        pass
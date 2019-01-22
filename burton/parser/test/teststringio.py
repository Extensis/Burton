import StringIO
import os

class TestStringIO(StringIO.StringIO):
    def __init__(self, filename = None, buffer = None):
        print("cwd: " + os.getcwd())
        #print('file: ' + filename)
        StringIO.StringIO.__init__(self, buffer)
        self.name = filename

    def close(self):
        pass
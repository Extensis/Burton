import StringIO

class TestStringIO(StringIO.StringIO):
    def __init__(self, buffer = None):
        StringIO.StringIO.__init__(self, buffer)

    def close(self):
        pass
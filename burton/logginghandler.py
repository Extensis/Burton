import logging

class BurtonLoggingHandler(logging.Handler):
    def __init__(self, *args, **kwargs):
        logging.Handler.__init__(self, *args, **kwargs)
        self.max_level = 0

    def emit(self, record):
        if record.levelno > self.max_level:
            self.max_level = record.levelno

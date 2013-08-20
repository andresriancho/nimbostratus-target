from __future__ import print_function

import logging

from fabric.colors import red, yellow, green


def configure_logging():
    logging.getLogger('boto').setLevel(logging.CRITICAL)
    logging.getLogger("paramiko").setLevel(logging.CRITICAL)
        
    # define a Handler which writes INFO messages or higher to the sys.stderr
    console = ColorLog()
    console.setLevel(logging.DEBUG)
    logging.getLogger('').addHandler(console)


class ColorLog(logging.Handler):
    """
    A class to print colored messages to stdout
    """

    COLORS = {
                logging.CRITICAL: red,
                logging.ERROR: red,
                logging.WARNING: yellow,
                logging.INFO: green,
                logging.DEBUG: lambda x: x,
              }
    
    def __init__(self):
        logging.Handler.__init__(self)

    def usesTime(self):
        return False

    def emit(self, record):
        color = self.COLORS.get(record.levelno, lambda x: x)
        print(color(record.msg))
        
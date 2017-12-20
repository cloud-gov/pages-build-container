'''
Setup nice logs.
Clients should use the `get_logger` method to get a logger instance.
'''

import os
import sys
import logging


class AsciiEncodingFormatter(logging.Formatter):
    def format(self, record):
        result = logging.Formatter.format(self, record)
        # remove any invalid ascii characters
        result = result.encode('ascii', 'replace').decode('ascii')
        return result


LOG_FORMATTER = AsciiEncodingFormatter(
    "[%(name)s] %(asctime)s %(levelname)s: %(message)s",
    datefmt='%Y-%m-%d %H:%M:%S',
)

LOG_HANDLER = logging.StreamHandler(sys.stdout)
LOG_HANDLER.setFormatter(LOG_FORMATTER)


def get_logger(name):
    '''
    Gets a logger instance configured with our formatter and handler
    for the given name.
    '''
    logger = logging.getLogger(name)
    logger.setLevel(os.environ.get('LOGLEVEL', logging.INFO))
    logger.addHandler(LOG_HANDLER)
    return logger

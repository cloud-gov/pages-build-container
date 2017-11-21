'''
Setup nice logs.
Clients should use the `get_logger` method to get a logger instance.
'''

import os
import sys
import logging


LOG_FORMATTER = logging.Formatter(
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

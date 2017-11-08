'''
Setup nice logs.
Clients should use the `get_logger` method to get a logger instance.
'''

import os
import sys
import logging

from colorlog import ColoredFormatter

LOG_FORMATTER = ColoredFormatter(
    "%(log_color)s%(levelname)-8s%(reset)s %(blue)s[%(name)s]%(reset)s "
    "%(asctime)s %(levelname)-8s %(message)s",
    datefmt='%Y-%m-%d %H:%M:%S',
    reset=True,
    log_colors={
        'DEBUG':    'cyan',
        'INFO':     'green',
        'WARNING':  'yellow',
        'ERROR':    'red',
        'CRITICAL': 'red,bg_white',
    },
    secondary_log_colors={},
    style='%'
)

LOG_HANDLER = logging.StreamHandler(sys.stdout)
LOG_HANDLER.setFormatter(LOG_FORMATTER)

def get_logger(name):
    '''Gets a logger instance for the given name'''
    logger = logging.getLogger(name)
    logger.setLevel(os.environ.get('LOGLEVEL', logging.INFO))
    logger.addHandler(LOG_HANDLER)
    return logger

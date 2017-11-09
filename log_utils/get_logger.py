'''
Setup nice logs.
Clients should use the `get_logger` method to get a logger instance.
'''

import os
import sys
import logging

# TODO: some npm characters are coming back as unreadable, 
# some encoding issue for sure:
#
# OUT uswds@0.13.3 node_modules/uswds
# OUT ��������� normalize.css@3.0.3
# OUT ��������� classlist - polyfill@1.2.0

# TODO: Might want to remove S3Publisher's log output
# because it will list too many files


LOG_FORMATTER = logging.Formatter(
    "[%(name)s] %(asctime)s %(levelname)s: %(message)s",
    datefmt='%Y-%m-%d %H:%M:%S',
)

LOG_HANDLER = logging.StreamHandler(sys.stdout)
LOG_HANDLER.setFormatter(LOG_FORMATTER)

def get_logger(name):
    '''Gets a logger instance for the given name'''
    logger = logging.getLogger(name)
    logger.setLevel(os.environ.get('LOGLEVEL', logging.INFO))
    logger.addHandler(LOG_HANDLER)
    return logger

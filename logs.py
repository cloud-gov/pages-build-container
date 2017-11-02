import os
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

LOG_HANDLER = logging.StreamHandler()
LOG_HANDLER.setFormatter(LOG_FORMATTER)
ROOT_LOGGER = logging.getLogger()
ROOT_LOGGER.setLevel(os.environ.get('LOGLEVEL', logging.INFO))
ROOT_LOGGER.addHandler(LOG_HANDLER)

'''
Common variables, tasks, and functions
'''

import os
import logging
import shutil

from invoke import task
from colorlog import ColoredFormatter

REPO_BASE_URL = 'github.com'
WORKING_DIR = os.path.join(os.curdir, 'tmp')

CLONE_DIR = 'site_repo'
CLONE_DIR_PATH = os.path.join(WORKING_DIR, CLONE_DIR)

SITE_BUILD_DIR = '_site'
SITE_BUILD_DIR_PATH = os.path.join(CLONE_DIR_PATH, SITE_BUILD_DIR)

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

LOGGER = logging.getLogger('COMMON')

@task
def clean(ctx, which=None):
    '''Deletes the specified directory'''
    which = which or CLONE_DIR_PATH
    LOGGER.info(f'Cleaning {which}')
    shutil.rmtree(which, ignore_errors=True)

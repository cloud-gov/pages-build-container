'''
Common variables, tasks, and functions
'''

import shutil
from pathlib import Path
from invoke import task
from log_utils import get_logger
from log_utils.load_dotenv import load_dotenv

REPO_BASE_URL = 'github.com'

WORKING_DIR_PATH = Path('/work')

# Make the working directory if it doesn't exist
WORKING_DIR_PATH.mkdir(exist_ok=True)

CLONE_DIR = 'site_repo'
CLONE_DIR_PATH = WORKING_DIR_PATH / CLONE_DIR

SITE_BUILD_DIR = '_site'
SITE_BUILD_DIR_PATH = CLONE_DIR_PATH / SITE_BUILD_DIR


@task
def clean(ctx, which=None):
    '''Deletes the specified directory'''
    load_dotenv()
    LOGGER = get_logger('COMMON')

    which = which or CLONE_DIR_PATH
    LOGGER.info(f'Cleaning {which}')
    shutil.rmtree(which, ignore_errors=True)

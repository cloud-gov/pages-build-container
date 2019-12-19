'''
Common variables, tasks, and functions
'''

import shutil
from pathlib import Path
from invoke import task

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
    which = which or CLONE_DIR_PATH
    print(f'Cleaning {which}')
    shutil.rmtree(which, ignore_errors=True)

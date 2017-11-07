'''
Common variables, tasks, and functions
'''

import os
import shutil
import logging

from invoke import task

REPO_BASE_URL = 'github.com'
WORKING_DIR = os.path.join(os.curdir, 'tmp')

CLONE_DIR = 'site_repo'
CLONE_DIR_PATH = os.path.join(WORKING_DIR, CLONE_DIR)

SITE_BUILD_DIR = '_site'

# Changing SITE_BUILD_DIR_PATH to not be inside CLONE_DIR_PATH
# will break hugo builds. See `build_hugo` task.
SITE_BUILD_DIR_PATH = os.path.join(CLONE_DIR_PATH, SITE_BUILD_DIR)

LOGGER = logging.getLogger('COMMON')

@task
def clean(ctx, which=None):
    '''Deletes the specified directory'''
    which = which or CLONE_DIR_PATH
    LOGGER.info(f'Cleaning {which}')
    shutil.rmtree(which, ignore_errors=True)

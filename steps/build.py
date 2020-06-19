import os
import shutil
from os import path

from common import (CLONE_DIR_PATH, SITE_BUILD_DIR, SITE_BUILD_DIR_PATH)
from log_utils import get_logger


def build_static():
    '''Moves all files from CLONE_DIR into SITE_BUILD_DIR'''
    logger = get_logger('build-static')

    dir = path.join(CLONE_DIR_PATH, '.git')
    logger.info(f'Cleaning {dir}')
    shutil.rmtree(dir, ignore_errors=True)

    logger.info(f'Moving files to {SITE_BUILD_DIR}')

    # Make the site build directory first
    SITE_BUILD_DIR_PATH.mkdir(exist_ok=True)

    files = os.listdir(CLONE_DIR_PATH)

    for file in files:
        # don't move the SITE_BUILD_DIR dir into itself
        if file is not SITE_BUILD_DIR:
            shutil.move(str(CLONE_DIR_PATH / file),
                        str(SITE_BUILD_DIR_PATH))

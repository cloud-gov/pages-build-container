'''
Common variables, tasks, and functions
'''

from pathlib import Path

REPO_BASE_URL = 'github.com'

WORKING_DIR_PATH = Path('/tmp/work')  # nosec

CLONE_DIR = 'site_repo'
CLONE_DIR_PATH = WORKING_DIR_PATH / CLONE_DIR

SITE_BUILD_DIR = '_site'
SITE_BUILD_DIR_PATH = CLONE_DIR_PATH / SITE_BUILD_DIR

STATUS_COMPLETE = 'success'
STATUS_ERROR = 'error'
STATUS_PROCESSING = 'processing'

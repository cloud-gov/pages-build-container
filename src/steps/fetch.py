'''
Fetch tasks and helpers
'''
import shlex

from log_utils import get_logger
from runner import run
from common import (REPO_BASE_URL, CLONE_DIR_PATH)


def fetch_url(owner, repository, access_token=''):  # nosec
    '''
    Creates a URL to a remote git repository.
    If `access_token` is specified, it will be included in the authentication
    section of the returned URL.

    >>> fetch_url('owner', 'repo')
    'https://github.com/owner/repo.git'

    >>> fetch_url('owner2', 'repo2', 'secret-token')
    'https://secret-token@github.com/owner2/repo2.git'
    '''
    repo_url = f'{REPO_BASE_URL}/{owner}/{repository}.git'
    if access_token:
        repo_url = f'{access_token}@{repo_url}'

    return f'https://{repo_url}'


def fetch_repo(owner, repository, branch, github_token=''):  # nosec
    '''
    Clones the GitHub repository specified by owner and repository
    into CLONE_DIR_PATH.
    '''
    logger = get_logger('clone')

    owner = shlex.quote(owner)
    repository = shlex.quote(repository)
    branch = shlex.quote(branch)

    command = (
        f'git clone -b {branch} --single-branch --depth 1 '
        f'{fetch_url(owner, repository, github_token)} '
        f'{CLONE_DIR_PATH}'
    )

    return run(logger, command)


def update_repo(clone_dir):
    '''
    Updates the repo with the full git history
    '''
    logger = get_logger('update')

    logger.info('Fetching full git history')

    command = 'git pull --unshallow'

    return run(logger, command, cwd=clone_dir)

'''
Fetch tasks and helpers
'''
import shlex
import subprocess  # nosec

from log_utils import get_logger
from runner import run
from common import (REPO_BASE_URL, CLONE_DIR_PATH)
from steps import StepException


def fetch_url(owner, repository, access_token='',
              source_code_platform='', source_code_platform_domain='',
              source_code_platform_token=''):  # nosec
    '''
    Creates a URL to a remote git repository.
    If `access_token` is specified, it will be included in the authentication
    section of the returned URL.

    >>> fetch_url('owner', 'repo')
    'https://github.com/owner/repo.git'

    >>> fetch_url('owner2', 'repo2', 'secret-token')
    'https://secret-token@github.com/owner2/repo2.git'

    >>> fetch_url('owner3', 'repo3', 'secret-token3',  \\
    ... 'source_code_platform3', 'source_code_platform_domain3', 'source_code_platform_token3')
    'https://source_code_platform_token3@source_code_platform_domain3/owner3/repo3.git'
    '''
    base_url = source_code_platform_domain if source_code_platform else REPO_BASE_URL
    repo_url = f'{base_url}/{owner}/{repository}.git'
    if token := source_code_platform_token if source_code_platform else access_token:
        repo_url = f'{token}@{repo_url}'

    return f'https://{repo_url}'



def fetch_repo(  # noqa: E303
        owner, repository, branch, access_token='',
        source_code_platform='', source_code_platform_domain='',
        source_code_platform_token=''):  # nosec
    '''
    Clones the GitHub repository specified by owner and repository
    into CLONE_DIR_PATH.
    '''
    logger = get_logger('clone')

    owner = shlex.quote(owner)
    repository = shlex.quote(repository)
    branch = shlex.quote(branch)

    clone_env = {
        'HOME': '/home'
    }

    url = fetch_url(owner, repository, access_token,
                    source_code_platform, source_code_platform_domain, source_code_platform_token)
    logger.info(f'Fetch URL: {url}')

    command = (
        f'git clone -b {branch} --single-branch --depth 1 '
        f'{url} '
        f'{CLONE_DIR_PATH}'
    )

    return run(logger, command, env=clone_env, check=False)


def update_repo(clone_dir):
    '''
    Updates the repo with the full git history
    '''
    logger = get_logger('update')

    logger.info('Fetching full git history')

    command = 'git pull --unshallow'

    return run(logger, command, cwd=clone_dir)


def fetch_commit_sha(clone_dir):
    '''
    fetch the last commitSHA
    '''
    try:
        logger = get_logger('clone')
        logger.info('Fetching commit details ...')
        # prior to running commands on the repo, make sure it isn't "dubious"
        # "detected dubious ownership in repository"
        git_command = shlex.split(f'git config --global --add safe.directory {clone_dir}')
        subprocess.run(  # nosec
            git_command,
            shell=False,
            check=True,
            stdout=subprocess.PIPE,
            universal_newlines=True,
            cwd=clone_dir
        )
        command = shlex.split('git log -1')  # get last commit only
        process = subprocess.run(  # nosec
            command,
            shell=False,
            check=True,
            stdout=subprocess.PIPE,
            universal_newlines=True,
            cwd=clone_dir
        )
        commit_log = process.stdout
        commit_sha = commit_log.split()[1]
        logger.info(f'commit {commit_sha}')
        return commit_sha
    except Exception:
        raise StepException('There was a problem fetching the commit hash for this build')

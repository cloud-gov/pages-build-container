'''
Clone tasks and helpers
'''
import os
import shlex

from invoke import task, call

from log_utils import get_logger
from .common import (REPO_BASE_URL, CLONE_DIR_PATH,
                     SITE_BUILD_DIR_PATH, clean)


LOGGER = get_logger('CLONE')


def clone_url(owner, repository, access_token=''):
    '''
    Creates a URL to a remote git repository.
    If `access_token` is specified, it will be included in the authentication
    section of the returned URL.

    >>> clone_url('owner', 'repo')
    'https://github.com/owner/repo.git'

    >>> clone_url('owner2', 'repo2', 'secret-token')
    'https://secret-token@github.com/owner2/repo2.git'
    '''
    repo_url = f'{REPO_BASE_URL}/{owner}/{repository}.git'
    if access_token:
        repo_url = f'{access_token}@{repo_url}'

    return f'https://{repo_url}'


def _clone_repo(ctx, owner, repository, branch):
    '''
    Clones the GitHub repository specified by owner and repository
    into CLONE_DIR_PATH.

    Expects GITHUB_TOKEN to be in the environment.
    '''

    LOGGER.info(f'Cloning {owner}/{repository}/{branch} to {CLONE_DIR_PATH}')

    github_token = os.environ['GITHUB_TOKEN']

    # escape-quote the value in case there's anything weird
    branch = shlex.quote(branch)

    ctx.run(
        f'git clone -b {branch} --single-branch '
        f'{clone_url(owner, repository, github_token)} '
        f'{CLONE_DIR_PATH}'
    )


# 'Exported' clone-repo task
clone_repo = task(
    pre=[call(clean, which=CLONE_DIR_PATH)],
    post=[
        # Remove _site if it exists
        call(clean, which=SITE_BUILD_DIR_PATH),
    ],
    help={
        "owner": "Owner of the repository to clone",
        "repository": "Name of the repository to clone",
    },
    name='clone-repo'
)(_clone_repo)


@task
def push_repo_remote(ctx, owner, repository, branch,
                     remote_name='destination'):
    '''
    Pushes the git repo in CLONE_DIR_PATH to a new remote destination.

    Expects GITHUB_TOKEN to be in the environment.
    '''
    LOGGER.info(f'Pushing cloned repository to {owner}/{repository}/{branch}')

    github_token = os.environ['GITHUB_TOKEN']

    with ctx.cd(CLONE_DIR_PATH):
        ctx.run(f'git remote add {remote_name} '
                f'{clone_url(owner, repository, github_token)}')
        ctx.run(f'git push {remote_name} {branch}:master')

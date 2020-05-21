'''
Clone tasks and helpers
'''
import os
import shlex
from invoke import task, call

from .common import (REPO_BASE_URL, CLONE_DIR_PATH,
                     SITE_BUILD_DIR_PATH, clean)


def clone_url(owner, repository, access_token=''):  # nosec
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


def _clone_repo(ctx, owner, repository, branch, depth=''):
    '''
    Clones the GitHub repository specified by owner and repository
    into CLONE_DIR_PATH.

    Expects GITHUB_TOKEN to be in the environment.
    '''
    print(f'Cloning {owner}/{repository}/{branch} to {CLONE_DIR_PATH}')

    github_token = os.environ['GITHUB_TOKEN']

    # escape-quote the value in case there's anything weird
    branch = shlex.quote(branch)

    ctx.run(
        f'git clone -b {branch} --single-branch {depth} '
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
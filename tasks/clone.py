'''
Clone tasks and helpers
'''
import os

from invoke import task, call

from log_utils import logging

from .common import (REPO_BASE_URL, CLONE_DIR_PATH,
                     SITE_BUILD_DIR_PATH, clean)


LOGGER = logging.getLogger('CLONE')


def clone_url(owner, repository, access_token):
    '''Creates a URL to a remote git repository'''
    return f'https://{access_token}@{REPO_BASE_URL}/{owner}/{repository}.git'


def _clone_repo(ctx, owner, repository, branch):
    '''
    Clones the GitHub repository specified by owner and repository into CLONE_DIR_PATH.

    Expects GITHUB_TOKEN to be in the environment.
    '''

    LOGGER.info(f'Cloning {owner}/{repository}/{branch} to {CLONE_DIR_PATH}')

    github_token = os.environ['GITHUB_TOKEN']

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
def push_repo_remote(ctx, owner, repository, branch, remote_name='destination'):
    '''
    Pushes the git repo in CLONE_DIR_PATH to a new remote destination.

    Expects GITHUB_TOKEN to be in the environment.
    '''
    LOGGER.info(f'Pushing cloned repository to {owner}/{repository}/{branch}')

    github_token = os.environ['GITHUB_TOKEN']

    with ctx.cd(CLONE_DIR_PATH):
        ctx.run(f'git remote add {remote_name} {clone_url(owner, repository, github_token)}')
        ctx.run(f'git push {remote_name} {branch}')

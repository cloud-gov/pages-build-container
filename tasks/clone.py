'''
Clone tasks and helpers
'''
from invoke import task, call

from .common import (REPO_BASE_URL, CLONE_DIR_PATH,
                     SITE_BUILD_DIR_PATH, clean)

from logs import logging


LOGGER = logging.getLogger('CLONE')


def clone_url(owner, repository, access_token):
    '''Creates a URL to a remote git repository'''
    return f'https://{access_token}@{REPO_BASE_URL}/{owner}/{repository}.git'

@task(
    pre=[call(clean, which=CLONE_DIR_PATH)],
    post=[
        # Remove _site if it exists
        call(clean, which=SITE_BUILD_DIR_PATH),
    ],
    help={
        "owner": "Owner of the repository to clone",
        "repository": "Name of the repository to clone",
    }
)
def clone_repo(ctx, owner, repository, github_token, branch):
    '''Clones the GitHub repository specified by owner and repository into CLONE_DIR_PATH'''
    LOGGER.info(f'Cloning {owner}/{repository}/{branch} to {CLONE_DIR_PATH}')
    ctx.run(
        f'git clone -b {branch} --single-branch '
        f'{clone_url(owner, repository, github_token)} '
        f'{CLONE_DIR_PATH}'
    )


@task
def push_repo_remote(ctx, owner, repository, github_token, branch, remote_name='destination'):
    '''Pushes the git repo in CLONE_DIR_PATH to a new remote destination'''
    LOGGER.info(f'Pushing cloned repository to {owner}/{repository}/{branch}')
    with ctx.cd(CLONE_DIR_PATH):
        ctx.run(f'git remote add {remote_name} {clone_url(owner, repository, github_token)}')
        ctx.run(f'git push {remote_name} {branch}')

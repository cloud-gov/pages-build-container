'''Main task entrypoint'''

import os

from datetime import datetime

from invoke import task
from dotenv import load_dotenv

from log_utils import logging


LOGGER = logging.getLogger('MAIN')


def run_task(ctx, task_name, flags_dict=None):
    '''
    Uses `ctx.run` to call the specified `task_name` with the 
    argument flags given in `flags_dict`, if specified.
    '''
    flag_args = []
    if flags_dict:
        for flag, val in flags_dict.items():
            flag_args.append(f"{flag}='{val}'")

    command = f'inv {task_name} {" ".join(flag_args)}'
    LOGGER.info(f'Calling sub-task: {command}')
    ctx.run(command)

@task
def main(ctx):
    '''
    Main task to run a full site build process.

    All values needed for the build are loaded from
    environment variables.
    '''
    # pylint: disable=C0103
    # TODO: use logging methods in logs/remote_logs

    LOGGER.info('Running full build process')

    BASE_DIR = os.path.dirname(os.path.dirname(__file__))
    DOTENV_PATH = os.path.join(BASE_DIR, '.env')

    if os.path.exists(DOTENV_PATH):
        LOGGER.info('Loading environment from .env file')
        load_dotenv(DOTENV_PATH)

    AWS_ACCESS_KEY_ID = os.environ['AWS_ACCESS_KEY_ID']
    AWS_DEFAULT_REGION = os.environ['AWS_DEFAULT_REGION']
    AWS_SECRET_ACCESS_KEY = os.environ['AWS_SECRET_ACCESS_KEY']
    BUCKET = os.environ['BUCKET']
    BASEURL = os.environ['BASEURL']
    CACHE_CONTROL = os.environ['CACHE_CONTROL']
    BRANCH = os.environ['BRANCH']
    CONFIG = os.environ['CONFIG']
    REPOSITORY = os.environ['REPOSITORY']
    OWNER = os.environ['OWNER']
    SITE_PREFIX = os.environ['SITE_PREFIX']
    GITHUB_TOKEN = os.environ['GITHUB_TOKEN']
    GENERATOR = os.environ['GENERATOR']


    CALLBACK = os.environ['CALLBACK']
    FEDERALIST_BUILDER_CALLBACK = os.environ['FEDERALIST_BUILDER_CALLBACK']

    # https://federalist-staging.18f.gov/v0/build/<build_id>/status/<token>
    STATUS_CALLBACK = os.environ['STATUS_CALLBACK']
    # https://federalist-staging.18f.gov/v0/build/<build_id>/log/<same_token>
    LOG_CALLBACK = os.environ['LOG_CALLBACK']

    # Optional environment variables
    SOURCE_REPO = os.getenv('SOURCE_REPO')
    SOURCE_OWNER = os.getenv('SOURCE_OWNER')


    # Unfortunately, pyinvoke doesn't have a great way to call tasks from
    # within other tasks. If you call them directly, their pre- and post-
    # dependencies are not executed.
    #
    # Here's the GitHub issue about this:
    # https://github.com/pyinvoke/invoke/issues/170
    #
    # So rather than calling the task function through python, we'll
    # call it instead using `ctx.run('invoke the_task ...')`

    start_time = datetime.now()

    ##
    # CLONE
    #
    if SOURCE_OWNER and SOURCE_REPO:
        # First clone the source (ie, template) repository
        clone_source_flags = {
            '--owner': SOURCE_OWNER,
            '--repository': SOURCE_REPO,
            '--github-token': GITHUB_TOKEN,
            '--branch': BRANCH,
        }
        run_task(ctx, 'clone-repo', clone_source_flags)
        
        # Then push the cloned source repo up to the destination repo.
        # Note that the destination repo must already exist but be empty.
        # The Federalist web app takes care of that operation.
        push_repo_flags = {
            '--owner': OWNER,
            '--repository': REPOSITORY,
            '--github-token': GITHUB_TOKEN,
            '--branch': BRANCH,
        }
        run_task(ctx, 'push-repo-remote', push_repo_flags)
    else:
        # Just clone the given repository
        clone_flags = {
            '--owner': OWNER,
            '--repository': REPOSITORY,
            '--github-token': GITHUB_TOKEN,
            '--branch': BRANCH,
        }
        run_task(ctx, 'clone-repo', clone_flags)
    
    ##
    # BUILD
    #
    build_flags = {
        '--branch': BRANCH,
        '--owner': OWNER,
        '--repository': REPOSITORY,
        '--site-prefix': SITE_PREFIX,
        '--base-url': BASEURL,
    }
    if GENERATOR == 'jekyll':
        build_flags['--config'] = CONFIG
        run_task(ctx, 'build-jekyll', build_flags)
    elif GENERATOR == 'hugo':
        # extra: --hugo-version (not yet used)
        run_task(ctx, 'build-hugo', build_flags)
    elif GENERATOR == 'static':
        # no build arguments are needed
        run_task(ctx, 'build-static')
    else:
        raise ValueError(f'Invalid GENERATOR: {GENERATOR}')

    ##
    # PUBLISH
    #
    publish_flags = {
        '--base-url': BASEURL,
        '--site-prefix': SITE_PREFIX,
        '--bucket': BUCKET,
        '--cache-control': CACHE_CONTROL,
        '--aws-region': AWS_DEFAULT_REGION,
        '--access-key-id': AWS_ACCESS_KEY_ID,
        '--secret-access-key': AWS_SECRET_ACCESS_KEY,
    }
    run_task(ctx, 'publish', publish_flags)

    delta = datetime.now() - start_time
    delta_mins = int(delta.total_seconds() // 60)
    delta_leftover_secs = int(delta.total_seconds() % 60)
    LOGGER.info(f'Total build time: {delta_mins}m {delta_leftover_secs}s')

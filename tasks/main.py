'''Main task entrypoint'''

import os

from datetime import datetime

from invoke import task, UnexpectedExit
from stopit import TimeoutException, SignalTimeout as Timeout

from log_utils import get_logger
from log_utils.remote_logs import (
    post_output_log, post_build_complete,
    post_build_error, post_build_timeout)
from .common import load_dotenv, delta_to_mins_secs

LOGGER = get_logger('MAIN')

TIMEOUT_SECONDS = 20 * 60  # 20 minutes


def replace_private_values(text, private_values,
                           replace_string='[PRIVATE VALUE HIDDEN]'):
    '''
    Replaces instances of the strings in `private_values` list
    with `replace_string`.

    >>> replace_private_values('18F boop Rulez boop', ['boop'])
    '18F [PRIVATE VALUE HIDDEN] Rulez [PRIVATE VALUE HIDDEN]'

    >>> replace_private_values('18F boop Rulez beep',
    ...                        ['boop', 'beep'], 'STUFF')
    '18F STUFF Rulez STUFF'
    '''
    for priv_val in private_values:
        text = text.replace(priv_val, replace_string)

    return text


def run_task(ctx, task_name, private_values, log_callback,
             flags_dict=None, env=None):
    '''
    Uses `ctx.run` to call the specified `task_name` with the
    argument flags given in `flags_dict` and `env`, if specified.

    The result's stdout is posted to log_callback, with `private_values`
    removed.
    '''
    flag_args = []
    if flags_dict:
        for flag, val in flags_dict.items():
            flag_args.append(f"{flag}='{val}'")

    command = f'inv {task_name} {" ".join(flag_args)}'

    run_kwargs = {}
    if env:
        run_kwargs['env'] = env

    result = ctx.run(command, **run_kwargs)

    output = replace_private_values(result.stdout, private_values)

    post_output_log(log_callback, source=task_name, output=output)

    return result


@task
def main(ctx):
    '''
    Main task to run a full site build process.

    All values needed for the build are loaded from
    environment variables.
    '''
    # (variable naming)
    # pylint: disable=C0103

    # keep track of total time
    start_time = datetime.now()

    # Load from .env for development
    load_dotenv()

    # These environment variables will be set into the environment
    # by federalist-builder.

    # During development, we can use a `.env` file (loaded above)
    # to make it easier to specify variables.

    AWS_DEFAULT_REGION = os.environ['AWS_DEFAULT_REGION']
    BUCKET = os.environ['BUCKET']
    BASEURL = os.environ['BASEURL']
    CACHE_CONTROL = os.environ['CACHE_CONTROL']
    BRANCH = os.environ['BRANCH']
    CONFIG = os.environ['CONFIG']
    REPOSITORY = os.environ['REPOSITORY']
    OWNER = os.environ['OWNER']
    SITE_PREFIX = os.environ['SITE_PREFIX']
    GENERATOR = os.environ['GENERATOR']

    AWS_ACCESS_KEY_ID = os.environ['AWS_ACCESS_KEY_ID']
    AWS_SECRET_ACCESS_KEY = os.environ['AWS_SECRET_ACCESS_KEY']
    GITHUB_TOKEN = os.environ['GITHUB_TOKEN']

    # List of private strings to be removed from any posted logs
    private_values = [AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, GITHUB_TOKEN]

    # Optional environment variables
    SOURCE_REPO = os.getenv('SOURCE_REPO')
    SOURCE_OWNER = os.getenv('SOURCE_OWNER')

    # Ex: https://federalist-builder.fr.cloud.gov/builds/<token>/callback
    FEDERALIST_BUILDER_CALLBACK = os.environ['FEDERALIST_BUILDER_CALLBACK']

    # Ex: https://federalist-staging.18f.gov/v0/build/<build_id>/status/<token>
    STATUS_CALLBACK = os.environ['STATUS_CALLBACK']

    # Ex: https://federalist-staging.18f.gov/v0/build/<build_id>/log/<token>
    LOG_CALLBACK = os.environ['LOG_CALLBACK']

    try:
        # throw a timeout exception after TIMEOUT_SECONDS
        with Timeout(TIMEOUT_SECONDS, swallow_exc=False):
            LOGGER.info(f'Running build for {OWNER}/{REPOSITORY}/{BRANCH}')

            # Unfortunately, pyinvoke doesn't have a great way to call tasks
            # from within other tasks. If you call them directly,
            # their pre- and post-dependencies are not executed.
            #
            # Here's the GitHub issue about this:
            # https://github.com/pyinvoke/invoke/issues/170
            #
            # So rather than calling the task functions through python, we'll
            # call them instead using `ctx.run('invoke the_task ...')` via the
            # helper `run_task` method.

            ##
            # CLONE
            #
            if SOURCE_OWNER and SOURCE_REPO:
                # First clone the source (ie, template) repository
                clone_source_flags = {
                    '--owner': SOURCE_OWNER,
                    '--repository': SOURCE_REPO,
                    '--branch': BRANCH,
                }

                run_task(ctx, 'clone-repo',
                         log_callback=LOG_CALLBACK,
                         private_values=private_values,
                         flags_dict=clone_source_flags,
                         env={'GITHUB_TOKEN': GITHUB_TOKEN})

                # Then push the cloned source repo up to the destination repo.
                # Note that the dest repo must already exist but be empty.
                # The Federalist web app takes care of that operation.
                push_repo_flags = {
                    '--owner': OWNER,
                    '--repository': REPOSITORY,
                    '--branch': BRANCH,
                }

                run_task(ctx, 'push-repo-remote',
                         log_callback=LOG_CALLBACK,
                         private_values=private_values,
                         flags_dict=push_repo_flags,
                         env={'GITHUB_TOKEN': GITHUB_TOKEN})
            else:
                # Just clone the given repository
                clone_flags = {
                    '--owner': OWNER,
                    '--repository': REPOSITORY,
                    '--branch': BRANCH,
                }

                run_task(ctx, 'clone-repo',
                         log_callback=LOG_CALLBACK,
                         private_values=private_values,
                         flags_dict=clone_flags,
                         env={'GITHUB_TOKEN': GITHUB_TOKEN})

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

            # Run the npm `federalist` task (if it is defined)
            run_task(ctx, 'run-federalist-script',
                     log_callback=LOG_CALLBACK,
                     private_values=private_values,
                     flags_dict=build_flags)

            # Run the appropriate build engine based on GENERATOR
            if GENERATOR == 'jekyll':
                build_flags['--config'] = CONFIG
                run_task(ctx, 'build-jekyll',
                         log_callback=LOG_CALLBACK,
                         private_values=private_values,
                         flags_dict=build_flags)
            elif GENERATOR == 'hugo':
                # extra: --hugo-version (not yet used)
                run_task(ctx, 'build-hugo',
                         log_callback=LOG_CALLBACK,
                         private_values=private_values,
                         flags_dict=build_flags)
            elif GENERATOR == 'static':
                # no build arguments are needed
                run_task(ctx, 'build-static',
                         log_callback=LOG_CALLBACK,
                         private_values=private_values)
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
            }

            publish_env = {
                'AWS_ACCESS_KEY_ID': AWS_ACCESS_KEY_ID,
                'AWS_SECRET_ACCESS_KEY': AWS_SECRET_ACCESS_KEY,
            }

            run_task(ctx, 'publish',
                     log_callback=LOG_CALLBACK,
                     private_values=private_values,
                     flags_dict=publish_flags,
                     env=publish_env)

            delta_string = delta_to_mins_secs(datetime.now() - start_time)
            LOGGER.info(
                f'Total build time: {delta_string}')

            # Finished!
            post_build_complete(STATUS_CALLBACK,
                                FEDERALIST_BUILDER_CALLBACK)

    except TimeoutException:
        LOGGER.info('Build has timed out')
        post_build_timeout(LOG_CALLBACK,
                           STATUS_CALLBACK,
                           FEDERALIST_BUILDER_CALLBACK)
    except UnexpectedExit as err:
        err_string = replace_private_values(err.result.stderr,
                                            private_values)

        LOGGER.info(f'Exception raised during build:')
        LOGGER.info(err_string)

        post_build_error(LOG_CALLBACK,
                         STATUS_CALLBACK,
                         FEDERALIST_BUILDER_CALLBACK,
                         err_string)
    except Exception as err:  # pylint: disable=W0703
        err_string = str(err)
        err_string = replace_private_values(err_string,
                                            private_values)
        LOGGER.info('Unexpected exception raised during build:')
        LOGGER.info(err_string)

        err_message = ('Unexpected error. Please try again and '
                       'contact federalist-support if it persists.')

        post_build_error(LOG_CALLBACK,
                         STATUS_CALLBACK,
                         FEDERALIST_BUILDER_CALLBACK,
                         err_message)

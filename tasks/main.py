'''Main task entrypoint'''

import os
import shlex
import logging
from datetime import datetime
from invoke import Context, UnexpectedExit
from stopit import TimeoutException, SignalTimeout as Timeout

from log_utils import (delta_to_mins_secs, get_logger, init_logging,
                       StreamToLogger)
from log_utils.remote_logs import (
    post_build_complete, post_build_error, post_build_timeout,
    should_skip_logging, post_build_processing)

TIMEOUT_SECONDS = 45 * 60  # 45 minutes


def run_task(ctx, task_name, log_attrs={}, flags_dict=None, env=None):
    '''
    Uses `ctx.run` to call the specified `task_name` with the
    argument flags given in `flags_dict` and `env`, if specified.

    The result's stdout and stderr are routed to the logger.
    '''
    flag_args = []
    if flags_dict:
        for flag, val in flags_dict.items():
            # quote val to prevent bash-breaking characters like '
            quoted_val = shlex.quote(val)
            flag_args.append(f"{flag}={quoted_val}")

    command = f'inv {task_name} {" ".join(flag_args)}'

    run_kwargs = {}
    if env:
        run_kwargs['env'] = env

    logger = get_logger(task_name, log_attrs)
    ctx.config.run.out_stream = StreamToLogger(logger)
    ctx.config.run.err_stream = StreamToLogger(logger, logging.ERROR)

    ctx.run(command, **run_kwargs)


def main():
    '''
    Main task to run a full site build process.

    All values needed for the build are loaded from
    environment variables.
    '''
    # (variable naming)
    # pylint: disable=C0103

    # keep track of total time
    start_time = datetime.now()

    AWS_DEFAULT_REGION = os.environ['AWS_DEFAULT_REGION']
    BUCKET = os.environ['BUCKET']
    BASEURL = os.environ['BASEURL']
    BUILD_ID = os.environ['BUILD_ID']
    CACHE_CONTROL = os.environ['CACHE_CONTROL']
    BRANCH = os.environ['BRANCH']
    CONFIG = os.environ['CONFIG']
    REPOSITORY = os.environ['REPOSITORY']
    OWNER = os.environ['OWNER']
    SITE_PREFIX = os.environ['SITE_PREFIX']
    GENERATOR = os.environ['GENERATOR']
    AWS_ACCESS_KEY_ID = os.environ['AWS_ACCESS_KEY_ID']
    AWS_SECRET_ACCESS_KEY = os.environ['AWS_SECRET_ACCESS_KEY']

    # Optional environment variables
    SOURCE_REPO = os.getenv('SOURCE_REPO', '')
    SOURCE_OWNER = os.getenv('SOURCE_OWNER', '')

    # GITHUB_TOKEN can be empty if a non-Federalist user
    # makes a commit to a repo and thus initiates a build for a
    # Federalist site
    GITHUB_TOKEN = os.getenv('GITHUB_TOKEN', '')

    # Ex: https://federalist-builder.fr.cloud.gov/builds/<token>/callback
    FEDERALIST_BUILDER_CALLBACK = os.environ['FEDERALIST_BUILDER_CALLBACK']

    # Ex: https://federalist-staging.18f.gov/v0/build/<build_id>/status/<token>
    STATUS_CALLBACK = os.environ['STATUS_CALLBACK']

    # Necessary to log to database
    DATABASE_URL = os.getenv('DATABASE_URL', '')

    BUILD_INFO = f'{OWNER}/{REPOSITORY}@id:{BUILD_ID}'

    priv_vals = private_values()

    logattrs = {
        'branch': BRANCH,
        'buildid': BUILD_ID,
        'owner': OWNER,
        'repository': REPOSITORY,
    }

    init_logging(priv_vals, logattrs, db_url=DATABASE_URL,
                 skip_logging=should_skip_logging())

    LOGGER = get_logger('main', logattrs)

    def run(task, args=None, env=None):
        run_task(Context(), task, logattrs, args, env)

    try:
        post_build_processing(STATUS_CALLBACK)
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
            # CLONE and/or PUSH
            #
            clone_env = {'GITHUB_TOKEN': GITHUB_TOKEN}

            if SOURCE_OWNER and SOURCE_REPO:
                # First clone the source (ie, template) repository

                clone_source_flags = {
                    '--owner': SOURCE_OWNER,
                    '--repository': SOURCE_REPO,
                    '--branch': BRANCH,
                }

                run('clone-repo', clone_source_flags, clone_env)

                # Then push the cloned source repo up to the destination repo.
                # Note that the dest repo must already exist but be empty.
                # The Federalist web app takes care of that operation.
                push_repo_flags = {
                    '--owner': OWNER,
                    '--repository': REPOSITORY,
                    '--branch': BRANCH,
                }

                run('push-repo-remote', push_repo_flags, clone_env)
            else:
                # Just clone the given repository
                clone_flags = {
                    '--owner': OWNER,
                    '--repository': REPOSITORY,
                    '--branch': BRANCH,
                    '--depth': '--depth 1',
                }

                run('clone-repo', clone_flags, clone_env)

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
            run('run-federalist-script', build_flags)

            # Run the appropriate build engine based on GENERATOR
            if GENERATOR == 'jekyll':
                build_flags['--config'] = CONFIG
                run('build-jekyll', build_flags)
            elif GENERATOR == 'hugo':
                # extra: --hugo-version (not yet used)
                run('build-hugo', build_flags)
            elif GENERATOR == 'static':
                # no build arguments are needed
                run('build-static')
            elif (GENERATOR == 'node.js' or GENERATOR == 'script only'):
                LOGGER.info('build already ran in \'npm run federalist\'')
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

            run('publish', publish_flags, publish_env)

            delta_string = delta_to_mins_secs(datetime.now() - start_time)
            LOGGER.info(f'Total build time: {delta_string}')

            # Finished!
            post_build_complete(STATUS_CALLBACK, FEDERALIST_BUILDER_CALLBACK)

    except TimeoutException:
        LOGGER.warning(f'Build({BUILD_INFO}) has timed out')
        post_build_timeout(STATUS_CALLBACK, FEDERALIST_BUILDER_CALLBACK)
    except UnexpectedExit as err:
        err_string = str(err)

        # log the original exception
        LOGGER.warning(f'Exception raised during build({BUILD_INFO}):'
                       + err_string)

        post_build_error(STATUS_CALLBACK,
                         FEDERALIST_BUILDER_CALLBACK,
                         err_string)
    except Exception as err:  # pylint: disable=W0703
        # Getting here means something really weird has happened
        # since all errors caught during tasks should be caught
        # in the previous block as `UnexpectedExit` exceptions.
        err_string = str(err)

        # log the original exception
        LOGGER.warning(f'Unexpected exception raised during build('
                       + BUILD_INFO + '): '
                       + err_string)

        err_message = (f'Unexpected build({BUILD_INFO}) error. Please try'
                       ' again and contact federalist-support'
                       ' if it persists.')

        post_build_error(STATUS_CALLBACK,
                         FEDERALIST_BUILDER_CALLBACK,
                         err_message)


def private_values():
    priv_vals = [
        os.environ['AWS_ACCESS_KEY_ID'],
        os.environ['AWS_SECRET_ACCESS_KEY']
    ]
    GITHUB_TOKEN = os.getenv('GITHUB_TOKEN', '')
    if GITHUB_TOKEN:
        priv_vals.append(GITHUB_TOKEN)

    return priv_vals

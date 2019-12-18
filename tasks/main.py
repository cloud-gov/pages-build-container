'''Main task entrypoint'''

import os
import shlex

from datetime import datetime

from invoke import task, UnexpectedExit
from stopit import TimeoutException, SignalTimeout as Timeout

from log_utils import get_logger
from log_utils.remote_logs import (
    post_output_log, post_build_complete,
    post_build_error, post_build_timeout)
from log_utils.delta_to_mins_secs import delta_to_mins_secs
from log_utils.load_dotenv import load_dotenv


TIMEOUT_SECONDS = 45 * 60  # 45 minutes


def format_output(stdout_str, stderr_str):
    '''
    Convenience method for combining strings of stdout and stderr.

    >>> format_output('stdout', 'stderr')
    '>> STDOUT:\\nstdout\\n---------------------------\\n>> STDERR:\\nstderr'

    >>> format_output('abc', 'def')
    '>> STDOUT:\\nabc\\n---------------------------\\n>> STDERR:\\ndef'
    '''
    output = f'>> STDOUT:\n{stdout_str}'
    output += '\n---------------------------\n'
    output += f'>> STDERR:\n{stderr_str}'
    return output


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


def find_custom_error_message(err_string):
    '''
    Returns a custom error message based on the current
    contents of `err_string`, if one exists.

    Otherwise, just return the supplied `err_string`.

    >>> msg = find_custom_error_message('boop InvalidAccessKeyId')
    >>> 'S3 keys were rotated' in msg
    True

    >>> find_custom_error_message('boop')
    'boop'
    '''
    if "InvalidAccessKeyId" in err_string:
        err_string = (
            'Whoops, our S3 keys were rotated during your '
            'build and became out of date. This was not a '
            'problem with your site build, but if you restart '
            'the failed build it should work on the next try. '
            'Sorry for the inconvenience!'
        )

    return err_string


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
            # quote val to prevent bash-breaking characters like '
            quoted_val = shlex.quote(val)
            flag_args.append(f"{flag}={quoted_val}")

    command = f'inv {task_name} {" ".join(flag_args)}'

    run_kwargs = {}
    if env:
        run_kwargs['env'] = env

    result = ctx.run(command, **run_kwargs)

    # Add both STDOUT and STDERR to the output logs
    output = format_output(result.stdout, result.stderr)

    # Replace instances of any private_values that may be present
    output = replace_private_values(output, private_values)

    post_output_log(log_callback, source=task_name, output=output)

    return result


@task
def main(ctx):
    '''
    Main task to run a full site build process.

    All values needed for the build are loaded from
    environment variables.
    '''
    load_dotenv()
    LOGGER = get_logger('MAIN')

    # (variable naming)
    # pylint: disable=C0103

    # keep track of total time
    start_time = datetime.now()

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

    # List of private strings to be removed from any posted logs
    private_values = [AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY]

    # Optional environment variables
    SOURCE_REPO = os.getenv('SOURCE_REPO', '')
    SOURCE_OWNER = os.getenv('SOURCE_OWNER', '')

    # GITHUB_TOKEN can be empty if a non-Federalist user
    # makes a commit to a repo and thus initiates a build for a
    # Federalist site
    GITHUB_TOKEN = os.getenv('GITHUB_TOKEN', '')
    if GITHUB_TOKEN:
        # only include it in list of values to strip from log output
        # if it exists
        private_values.append(GITHUB_TOKEN)

    # Ex: https://federalist-builder.fr.cloud.gov/builds/<token>/callback
    FEDERALIST_BUILDER_CALLBACK = os.environ['FEDERALIST_BUILDER_CALLBACK']

    # Ex: https://federalist-staging.18f.gov/v0/build/<build_id>/status/<token>
    STATUS_CALLBACK = os.environ['STATUS_CALLBACK']

    # Ex: https://federalist-staging.18f.gov/v0/build/<build_id>/log/<token>
    LOG_CALLBACK = os.environ['LOG_CALLBACK']

    BUILD_ID = os.environ['BUILD_ID']

    BUILD_INFO = f'{OWNER}/{REPOSITORY}@id:{BUILD_ID}'

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
                    '--depth': '--depth 1',
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
        LOGGER.exception(f'Build({BUILD_INFO}) has timed out')
        post_build_timeout(LOG_CALLBACK,
                           STATUS_CALLBACK,
                           FEDERALIST_BUILDER_CALLBACK)
    except UnexpectedExit as err:
        # Combine the error's stdout and stderr into one string
        err_string = format_output(err.result.stdout, err.result.stderr)

        # replace any private values that might be in the error message
        err_string = replace_private_values(err_string,
                                            private_values)

        # log the original exception
        LOGGER.exception(f'Exception raised during build({BUILD_INFO}):'
                         + err_string)

        # replace the message with a custom one, if it exists
        err_string = find_custom_error_message(err_string)

        post_build_error(LOG_CALLBACK,
                         STATUS_CALLBACK,
                         FEDERALIST_BUILDER_CALLBACK,
                         err_string)
    except Exception as err:  # pylint: disable=W0703
        # Getting here means something really weird has happened
        # since all errors caught during tasks should be caught
        # in the previous block as `UnexpectedExit` exceptions.
        err_string = str(err)
        err_string = replace_private_values(err_string,
                                            private_values)

        # log the original exception
        LOGGER.exception(f'Unexpected exception raised during build('
                         + BUILD_INFO + '): '
                         + err_string)

        err_message = (f'Unexpected build({BUILD_INFO}) error. Please try'
                       ' again and contact federalist-support'
                       ' if it persists.')

        post_build_error(LOG_CALLBACK,
                         STATUS_CALLBACK,
                         FEDERALIST_BUILDER_CALLBACK,
                         err_message)

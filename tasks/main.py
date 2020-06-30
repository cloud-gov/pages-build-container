'''Main entrypoint'''

import json
import os
import shlex
from datetime import datetime
from stopit import TimeoutException, SignalTimeout as Timeout

from log_utils import delta_to_mins_secs, get_logger, init_logging
from log_utils.remote_logs import (
    post_build_complete, post_build_error, post_build_timeout,
    should_skip_logging, post_build_processing)

from crypto.decrypt import decrypt

from steps import (
    build_hugo, build_jekyll, build_static,
    download_hugo, fetch_repo, publish, run_federalist_script,
    setup_bundler, setup_node, setup_ruby
)


TIMEOUT_SECONDS = 45 * 60  # 45 minutes


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
    BRANCH = shlex.quote(os.environ['BRANCH'])
    CONFIG = os.environ['CONFIG']
    REPOSITORY = shlex.quote(os.environ['REPOSITORY'])
    OWNER = shlex.quote(os.environ['OWNER'])
    SITE_PREFIX = os.environ['SITE_PREFIX']
    GENERATOR = os.environ['GENERATOR']
    AWS_ACCESS_KEY_ID = os.environ['AWS_ACCESS_KEY_ID']
    AWS_SECRET_ACCESS_KEY = os.environ['AWS_SECRET_ACCESS_KEY']
    USER_ENVIRONMENT_VARIABLES = json.loads(
        os.getenv('USER_ENVIRONMENT_VARIABLES', '[]')
    )
    USER_ENVIRONMENT_VARIABLE_KEY = os.environ['USER_ENVIRONMENT_VARIABLE_KEY']

    # GITHUB_TOKEN can be empty if a non-Federalist user
    # makes a commit to a repo and thus initiates a build for a
    # Federalist site
    GITHUB_TOKEN = os.getenv('GITHUB_TOKEN', '')

    # Ex: https://federalist-builder.fr.cloud.gov/builds/<token>/callback
    FEDERALIST_BUILDER_CALLBACK = os.environ['FEDERALIST_BUILDER_CALLBACK']

    # Ex: https://federalist-staging.18f.gov/v0/build/<build_id>/status/<token>
    STATUS_CALLBACK = os.getenv('STATUS_CALLBACK', '')

    # Necessary to log to database
    DATABASE_URL = os.getenv('DATABASE_URL', '')

    BUILD_INFO = f'{OWNER}/{REPOSITORY}@id:{BUILD_ID}'

    decrypted_uevs = [{
        'name': uev['name'],
        'value': decrypt(uev['ciphertext'], USER_ENVIRONMENT_VARIABLE_KEY)
    } for uev in USER_ENVIRONMENT_VARIABLES]

    priv_vals = private_values([uev['value'] for uev in decrypted_uevs])

    logattrs = {
        'branch': BRANCH,
        'buildid': BUILD_ID,
        'owner': OWNER,
        'repository': REPOSITORY,
    }

    init_logging(priv_vals, logattrs, db_url=DATABASE_URL, skip_logging=should_skip_logging())

    LOGGER = get_logger('main')

    def handle_fail(returncode, msg):
        if returncode != 0:
            LOGGER.error(msg)
            post_build_error(STATUS_CALLBACK, FEDERALIST_BUILDER_CALLBACK, msg)
            exit(1)

    try:
        post_build_processing(STATUS_CALLBACK)
        # throw a timeout exception after TIMEOUT_SECONDS
        with Timeout(TIMEOUT_SECONDS, swallow_exc=False):
            LOGGER.info(f'Running build for {OWNER}/{REPOSITORY}/{BRANCH}')

            ##
            # FETCH
            #
            handle_fail(
                fetch_repo(OWNER, REPOSITORY, BRANCH, GITHUB_TOKEN),
                'There was a problem fetching the repository, see the above logs for details.'
            )

            ##
            # BUILD
            #
            handle_fail(
                setup_node(),
                'There was a problem setting up Node, see the above logs for details.'
            )

            # Run the npm `federalist` task (if it is defined)
            handle_fail(
                run_federalist_script(
                    BRANCH, OWNER, REPOSITORY, SITE_PREFIX, BASEURL, decrypted_uevs
                ),
                'There was a problem running the federalist script, see the above logs for details.'
            )

            # Run the appropriate build engine based on GENERATOR
            if GENERATOR == 'jekyll':
                handle_fail(
                    setup_ruby(),
                    'There was a problem setting up Ruby, see the above logs for details.'
                )

                handle_fail(
                    setup_bundler(),
                    'There was a problem setting up Bundler, see the above logs for details.'
                )

                handle_fail(
                    build_jekyll(
                        BRANCH, OWNER, REPOSITORY, SITE_PREFIX, BASEURL, CONFIG, decrypted_uevs
                    ),
                    'There was a problem running Jekyll, see the above logs for details.'
                )

            elif GENERATOR == 'hugo':
                # extra: --hugo-version (not yet used)
                handle_fail(
                    download_hugo(),
                    'There was a problem downloading Hugo, see the above logs for details.'
                )

                handle_fail(
                    build_hugo(
                        BRANCH, OWNER, REPOSITORY, SITE_PREFIX, BASEURL, decrypted_uevs
                    ),
                    'There was a problem running Hugo, see the above logs for details.'
                )

            elif GENERATOR == 'static':
                # no build arguments are needed
                build_static()

            elif (GENERATOR == 'node.js' or GENERATOR == 'script only'):
                LOGGER.info('build already ran in \'npm run federalist\'')

            else:
                raise ValueError(f'Invalid GENERATOR: {GENERATOR}')

            ##
            # PUBLISH
            #
            publish(BASEURL, SITE_PREFIX, BUCKET, CACHE_CONTROL, AWS_DEFAULT_REGION,
                    AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY)

            delta_string = delta_to_mins_secs(datetime.now() - start_time)
            LOGGER.info(f'Total build time: {delta_string}')

            # Finished!
            post_build_complete(STATUS_CALLBACK, FEDERALIST_BUILDER_CALLBACK)

    except TimeoutException:
        LOGGER.warning(f'Build({BUILD_INFO}) has timed out')
        post_build_timeout(STATUS_CALLBACK, FEDERALIST_BUILDER_CALLBACK)

    except Exception as err:  # pylint: disable=W0703
        # Getting here means something really weird has happened
        # since all errors caught during tasks should be caught
        # in the previous block as `UnexpectedExit` exceptions.
        err_string = str(err)

        # log the original exception
        LOGGER.warning('Unexpected exception raised during build('
                       + BUILD_INFO + '): '
                       + err_string)

        err_message = (f'Unexpected build({BUILD_INFO}) error. Please try'
                       ' again and contact federalist-support'
                       ' if it persists.')

        post_build_error(STATUS_CALLBACK,
                         FEDERALIST_BUILDER_CALLBACK,
                         err_message)


def private_values(user_values):
    priv_vals = [
        os.environ['AWS_ACCESS_KEY_ID'],
        os.environ['AWS_SECRET_ACCESS_KEY']
    ]
    GITHUB_TOKEN = os.getenv('GITHUB_TOKEN', '')
    if GITHUB_TOKEN:
        priv_vals.append(GITHUB_TOKEN)

    return priv_vals + user_values

'''Main entrypoint'''

import os
import sys
from datetime import datetime
from stopit import TimeoutException, SignalTimeout as Timeout

from common import WORKING_DIR_PATH

from log_utils import delta_to_mins_secs, get_logger, init_logging
from log_utils.remote_logs import (
    post_build_complete, post_build_error,
    post_build_timeout, post_build_processing
)

from crypto.decrypt import decrypt

from steps import (
    build_hugo, build_jekyll, build_static,
    download_hugo, fetch_repo, publish, run_federalist_script,
    setup_bundler, setup_node, setup_ruby, StepException
)


TIMEOUT_SECONDS = 45 * 60  # 45 minutes

GENERATORS = ['hugo', 'jekyll', 'node.js', 'static']


def build(
    aws_access_key_id,
    aws_default_region,
    aws_secret_access_key,
    federalist_builder_callback,
    status_callback,
    baseurl,
    branch,
    bucket,
    build_id,
    config,
    generator,
    github_token,
    owner,
    repository,
    site_prefix,
    user_environment_variables=[]
):
    '''
    Main task to run a full site build process.

    All values needed for the build are loaded from
    environment variables.
    '''
    # keep track of total time
    start_time = datetime.now()

    # Make the working directory if it doesn't exist
    WORKING_DIR_PATH.mkdir(exist_ok=True)

    logger = None

    cache_control = os.getenv('CACHE_CONTROL', 'max-age=60')
    database_url = os.environ['DATABASE_URL']
    user_environment_variable_key = os.environ['USER_ENVIRONMENT_VARIABLE_KEY']

    try:
        post_build_processing(status_callback)
        # throw a timeout exception after TIMEOUT_SECONDS
        with Timeout(TIMEOUT_SECONDS, swallow_exc=False):
            build_info = f'{owner}/{repository}@id:{build_id}'

            decrypted_uevs = decrypt_uevs(user_environment_variable_key, user_environment_variables)

            priv_vals = [uev['value'] for uev in decrypted_uevs]
            priv_vals.append(aws_access_key_id)
            priv_vals.append(aws_secret_access_key)
            if github_token:
                priv_vals.append(github_token)

            logattrs = {
                'branch': branch,
                'buildid': build_id,
                'owner': owner,
                'repository': repository,
            }

            init_logging(priv_vals, logattrs, database_url)

            logger = get_logger('main')

            def run_step(returncode, msg):
                if returncode != 0:
                    raise StepException(msg)

            logger.info(f'Running build for {owner}/{repository}/{branch}')

            if generator not in GENERATORS:
                raise ValueError(f'Invalid generator: {generator}')

            ##
            # FETCH
            #
            run_step(
                fetch_repo(owner, repository, branch, github_token),
                'There was a problem fetching the repository, see the above logs for details.'
            )

            ##
            # BUILD
            #
            run_step(
                setup_node(),
                'There was a problem setting up Node, see the above logs for details.'
            )

            # Run the npm `federalist` task (if it is defined)
            run_step(
                run_federalist_script(
                    branch, owner, repository, site_prefix, baseurl, decrypted_uevs
                ),
                'There was a problem running the federalist script, see the above logs for details.'
            )

            # Run the appropriate build engine based on generator
            if generator == 'jekyll':
                run_step(
                    setup_ruby(),
                    'There was a problem setting up Ruby, see the above logs for details.'
                )

                run_step(
                    setup_bundler(),
                    'There was a problem setting up Bundler, see the above logs for details.'
                )

                run_step(
                    build_jekyll(
                        branch, owner, repository, site_prefix, baseurl, config, decrypted_uevs
                    ),
                    'There was a problem running Jekyll, see the above logs for details.'
                )

            elif generator == 'hugo':
                # extra: --hugo-version (not yet used)
                run_step(
                    download_hugo(),
                    'There was a problem downloading Hugo, see the above logs for details.'
                )

                run_step(
                    build_hugo(
                        branch, owner, repository, site_prefix, baseurl, decrypted_uevs
                    ),
                    'There was a problem running Hugo, see the above logs for details.'
                )

            elif generator == 'static':
                # no build arguments are needed
                build_static()

            elif (generator == 'node.js' or generator == 'script only'):
                logger.info('build already ran in \'npm run federalist\'')

            else:
                raise ValueError(f'Invalid generator: {generator}')

            ##
            # PUBLISH
            #
            publish(baseurl, site_prefix, bucket, cache_control, aws_default_region,
                    aws_access_key_id, aws_secret_access_key)

            delta_string = delta_to_mins_secs(datetime.now() - start_time)
            logger.info(f'Total build time: {delta_string}')

            # Finished!
            post_build_complete(status_callback, federalist_builder_callback)

            sys.exit(0)

    except StepException as err:
        '''
        Thrown when a step itself fails, usually because a command exited
        with a non-zero return code
        '''
        logger.error(str(err))
        post_build_error(status_callback, federalist_builder_callback, str(err))
        sys.exit(1)

    except TimeoutException:
        logger.warning(f'Build({build_info}) has timed out')
        post_build_timeout(status_callback, federalist_builder_callback)

    except Exception as err:  # pylint: disable=W0703
        # Getting here means something really weird has happened
        # since all errors caught during tasks should be caught
        # in the previous block as `UnexpectedExit` exceptions.
        err_string = str(err)

        # log the original exception
        msg = f'Unexpected exception raised during build({build_info}): {err_string}'
        if logger:
            logger.warning(msg)
        else:
            print(msg)

        err_message = (
            f'Unexpected build({build_info}) error. Please try '
            'again and contact federalist-support if it persists.'
        )

        post_build_error(status_callback,
                         federalist_builder_callback,
                         err_message)


def decrypt_uevs(key, uevs):
    return [{
        'name': uev['name'],
        'value': decrypt(uev['ciphertext'], key)
    } for uev in uevs]

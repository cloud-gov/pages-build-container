'''main task entrypoint'''

import os
import json
import base64
import requests

from invoke import task
from dotenv import load_dotenv

from logs import logging

from .clone import clone_repo, push_repo_remote

LOGGER = logging.getLogger('MAIN')

def b64string(s):
    '''Base64 encodes a string as utf-8'''
    return base64.b64encode(s.encode('utf-8'))

def post_output_log(log_callback_url, source, output, limit=500000):
    # Replicates log_output() function in main.sh
    if len(output) > limit:
        output = 'output suppressed due to length'

    requests.post(
        log_callback_url,
        data=json.dumps({
            'source': source,
            'output': b64string(output),
        })
    )

def post_status(status_callback_url, status, output):
    requests.post(
        status_callback_url,
        data=json.dumps({
            'status': status,
            'message': b64string(output),
        })
    )


def post_build_complete(builder_callback_url, status_callback_url):
    post_status(status_callback_url,
                status=0,
                output=''
    )

    # Send a DELETE to the Federalist build scheduler to alert that the container is available
    requests.delete(builder_callback_url)


def post_build_error(log_callback_url, status_callback_url, builder_callback_url, error_output):
    # TODO: status callback also?
    output = error_output

    post_output_log(
        log_callback_url,
        source='ERROR',
        output=output
    )

    # Post to the Federalist web application endpoint with status and output
    post_status(status_callback_url,
                status=1,
                output=output
    )

    # Send a DELETE to the Federalist build scheduler to alert that the container is available
    requests.delete(builder_callback_url)


def post_build_timeout(log_callback_url, status_callback_url, builder_callback_url):
    # TODO: status callback also?
    output = 'The build did not complete. It may have timed out.'

    post_output_log(
        log_callback_url,
        source='ERROR',
        output=output
    )

    # Post to the Federalist web application endpoint with status and output
    post_status(status_callback_url,
                status=1,
                output=output
    )

    # Send a DELETE to the Federalist build scheduler to alert that the container is available
    requests.delete(builder_callback_url)


@task
def main(ctx):
    LOGGER.info('Running full build process')

    BASE_DIR = os.path.dirname(os.path.dirname(__file__))
    DOTENV_PATH = os.path.join(BASE_DIR, '.env')

    if os.path.exists(DOTENV_PATH):
        LOGGER.info('Loading environment from .env file')
        load_dotenv(DOTENV_PATH)

    AWS_ACCESS_KEY_ID = os.environ['AWS_ACCESS_KEY_ID']
    AWS_DEFAULT_REGION = os.environ['AWS_DEFAULT_REGION']
    AWS_SECRET_ACCESS_KEY = os.environ['AWS_SECRET_ACCESS_KEY']
    CALLBACK = os.environ['CALLBACK']
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
    FEDERALIST_BUILDER_CALLBACK = os.environ['FEDERALIST_BUILDER_CALLBACK']


    # https://federalist-staging.18f.gov/v0/build/<build_id>/status/<token>
    STATUS_CALLBACK = os.environ['STATUS_CALLBACK']
    # https://federalist-staging.18f.gov/v0/build/<build_id>/log/<same_token>
    LOG_CALLBACK = os.environ['LOG_CALLBACK']

    # Optional environment variables
    SOURCE_REPO = os.getenv('SOURCE_REPO')
    SOURCE_OWNER = os.getenv('SOURCE_OWNER')

    if SOURCE_OWNER and SOURCE_REPO:
        # First clone the source (ie, template) repository
        clone_repo(ctx, owner=SOURCE_OWNER, repository=SOURCE_REPO,
            github_token=GITHUB_TOKEN, branch=BRANCH)

        # Then push the cloned source repo up to the destination repo.
        # Note that the destination repo must already exist but be empty.
        # The Federalist web app takes care of that operation.
        push_repo_remote(ctx, owner=OWNER, repository=REPOSITORY,
            github_token=GITHUB_TOKEN, branch=BRANCH)

    else:
        # Just clone the given repository
        clone_repo(ctx, owner=OWNER, repository=REPOSITORY,
            github_token=GITHUB_TOKEN, branch=BRANCH)

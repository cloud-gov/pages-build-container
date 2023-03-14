'''Functions for sending remote logs'''

import base64
import requests

from .common import (STATUS_COMPLETE, STATUS_ERROR, STATUS_PROCESSING)


def b64string(text):
    '''
    Base64 encodes a string as utf-8

    >>> b64string('boop')
    'Ym9vcA=='
    '''
    return base64.b64encode(text.encode('utf-8')).decode('utf-8')


def post_status(status_callback_url, status, output='', commit_sha=None):
    '''
    POSTs `status` and `output` to the `status_callback_url`
    '''
    requests.post(
        status_callback_url,
        json={
            'status': status,
            'message': b64string(output),
            'commit_sha': commit_sha,
        },
        timeout=10
    )


def post_build_complete(status_callback_url, commit_sha):
    '''
    POST a STATUS_COMPLETE status to the status_callback_url
    '''
    post_status(status_callback_url, status=STATUS_COMPLETE, commit_sha=commit_sha)


def post_build_error(status_callback_url, error_output, commit_sha=None):
    '''
    POST a STATUS_ERROR status with message to the status_callback_url
    '''
    # Post to the Pages web application endpoint with status and output
    post_status(
        status_callback_url, status=STATUS_ERROR, output=error_output, commit_sha=commit_sha
    )


def post_build_processing(status_callback_url):
    '''
    POST a STATUS_PROCESSING status to the status_callback_url
    '''
    post_status(status_callback_url, status=STATUS_PROCESSING)


def post_build_timeout(status_callback_url, commit_sha=None):
    '''
    POST a STATUS_ERROR status with timeout message to the status_callback_url
    '''
    output = 'The build did not complete. It may have timed out.'

    # Post to the Pages web application with status and output
    post_status(status_callback_url, status=STATUS_ERROR, output=output, commit_sha=commit_sha)

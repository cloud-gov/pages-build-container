'''Functions for sending remote logs'''

import os
import base64
import requests

from .common import (STATUS_COMPLETE, STATUS_ERROR, STATUS_PROCESSING)


def require_services():
    return not skip_services()


def skip_services():
    return os.getenv('NO_SERVICES', False) in ('true', 'True')


def b64string(text):
    '''
    Base64 encodes a string as utf-8

    >>> b64string('boop')
    'Ym9vcA=='
    '''
    return base64.b64encode(text.encode('utf-8')).decode('utf-8')


def post_status(status_callback_url, status, output=''):
    '''
    POSTs `status` and `output` to the `status_callback_url`
    '''
    if skip_services():
        return

    requests.post(
        status_callback_url,
        json={
            'status': status,
            'message': b64string(output),
        }
    )


def post_build_complete(status_callback_url, builder_callback_url):
    '''
    POSTs a STATUS_CODE_COMPLETE status to the status_callback_url
    and issues a DELETE to the builder_callback_url.
    '''
    if skip_services():
        return

    post_status(status_callback_url, status=STATUS_COMPLETE)

    # Send a DELETE to the Federalist build scheduler to alert that the
    # container is available
    requests.delete(builder_callback_url)


def post_build_error(status_callback_url, builder_callback_url, error_output):
    '''
    Sends build error notifications and output to the given callbacks.
    '''
    if skip_services():
        return

    # Post to the Federalist web application endpoint with status and output
    post_status(status_callback_url, status=STATUS_ERROR, output=error_output)

    # Send a DELETE to the Federalist build scheduler to alert that
    # the container is available
    requests.delete(builder_callback_url)


def post_build_processing(status_callback_url):
    '''
    POSTs a STATUS_CODE_BEGIN status to the status_callback_url
    and issues a DELETE to the builder_callback_url.
    '''
    if skip_services():
        return

    post_status(status_callback_url, status=STATUS_PROCESSING)


def post_build_timeout(status_callback_url, builder_callback_url):
    '''
    Sends timeout error notifications to the given callbacks.
    '''
    output = 'The build did not complete. It may have timed out.'

    if skip_services():
        return

    # Post to the Federalist web application with status and output
    post_status(status_callback_url, status=STATUS_ERROR, output=output)

    # Send a DELETE to the Federalist build scheduler to alert that the
    # container is available
    requests.delete(builder_callback_url)

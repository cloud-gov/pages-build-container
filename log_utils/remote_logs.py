'''Functions for sending remote logs'''

import base64
import requests


STATUS_CODE_COMPLETE = 0
STATUS_CODE_ERROR = 1


def b64string(text):
    '''
    Base64 encodes a string as utf-8

    >>> b64string('boop')
    'Ym9vcA=='
    '''
    return base64.b64encode(text.encode('utf-8')).decode('utf-8')


def post_output_log(log_callback_url, source, output, limit=500000,
                    limit_msg='output suppressed due to length'):
    '''
    POSTs an `output` log from `source` to the `log_callback_url`.

    If the `output` length is greater than `limit`, then instead
    `limit_msg` is sent.
    '''
    # Replicates log_output() function in main.sh
    if len(output) > limit:
        output = limit_msg

    requests.post(
        log_callback_url,
        json={
            'source': source,
            'output': b64string(output),
        }
    )


def post_status(status_callback_url, status, output):
    '''
    POSTs `status` and `output` to the `status_callback_url`
    '''
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
    post_status(
        status_callback_url,
        status=STATUS_CODE_COMPLETE,
        output='')

    # Send a DELETE to the Federalist build scheduler to alert that the
    # container is available
    requests.delete(builder_callback_url)


def post_build_error(log_callback_url, status_callback_url,
                     builder_callback_url, error_output):
    '''
    Sends build error notifications and output to the given callbacks.
    '''
    output = error_output

    post_output_log(
        log_callback_url,
        source='ERROR',
        output=output)

    # Post to the Federalist web application endpoint with status and output
    post_status(status_callback_url,
                status=STATUS_CODE_ERROR,
                output=output)

    # Send a DELETE to the Federalist build scheduler to alert that
    # the container is available
    requests.delete(builder_callback_url)


def post_build_timeout(log_callback_url, status_callback_url,
                       builder_callback_url):
    '''
    Sends timeout error notifications to the given callbacks.
    '''
    output = 'The build did not complete. It may have timed out.'

    post_output_log(
        log_callback_url,
        source='ERROR',
        output=output)

    # Post to the Federalist web application endpoint with status
    # and output
    post_status(status_callback_url,
                status=STATUS_CODE_ERROR,
                output=output)

    # Send a DELETE to the Federalist build scheduler to alert that the
    # container is available
    requests.delete(builder_callback_url)

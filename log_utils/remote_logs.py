'''Functions for sending remote logs'''

import os
import base64
import requests


def should_skip_logging():
    '''
    Reads SKIP_LOGGING env var to determine if logging
    and status callbacks should be called.
    '''
    return os.getenv('SKIP_LOGGING', False) in ('true', 'True')


def b64string(text):
    '''
    Base64 encodes a string as utf-8

    >>> b64string('boop')
    'Ym9vcA=='
    '''
    return base64.b64encode(text.encode('utf-8')).decode('utf-8')


def post_output_log(log_callback_url, source, output, chunk_size=200000):
    '''
    POSTs `output` logs from `source` to the `log_callback_url` in chunks
    of length `chunk_size`.
    '''
    n = chunk_size
    output_chunks = [output[i:i+n] for i in range(0, len(output), n)]

    if not should_skip_logging():
        for chunk in output_chunks:
            requests.post(
                log_callback_url,
                json={
                    'source': source,
                    'output': b64string(chunk),
                }
            )


def post_status(status_callback_url, status, output):
    '''
    POSTs `status` and `output` to the `status_callback_url`
    '''
    if not should_skip_logging():
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
    if not should_skip_logging():
        post_status(
            status_callback_url,
            status='complete',
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

    if not should_skip_logging():
        post_output_log(
            log_callback_url,
            source='ERROR',
            output=output)

        # Post to the Federalist web application endpoint with status
        # and output
        post_status(status_callback_url,
                    status='error',
                    output=output)

    # Send a DELETE to the Federalist build scheduler to alert that
    # the container is available
    requests.delete(builder_callback_url)


def post_build_processing(status_callback_url):
    '''
    POSTs a STATUS_CODE_BEGIN status to the status_callback_url
    and issues a DELETE to the builder_callback_url.
    '''
    if not should_skip_logging():
        post_status(
            status_callback_url,
            status='processing',
            output='')

def post_build_timeout(log_callback_url, status_callback_url,
                       builder_callback_url):
    '''
    Sends timeout error notifications to the given callbacks.
    '''
    output = 'The build did not complete. It may have timed out.'

    if not should_skip_logging():
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

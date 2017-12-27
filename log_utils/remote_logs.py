'''Functions for sending remote logs'''

import os
import base64
import requests


STATUS_CODE_COMPLETE = 0
STATUS_CODE_ERROR = 1


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


def truncate_text(text, limit=50000):
    '''
    Truncates the given `text` to the specified `limit` so
    that at most, `limit` number of characters will be in the
    returned value.

    >>> text = 'boop'
    >>> truncate_text(text, limit=3)
    'boo'

    A truncation message is appended if there is room within
    the `limit`.

    >>> text = ''.join('x' for i in range(0, 100))
    >>> truncate_text(text, limit=50)
    'xxxxxxxxxxxxxxxxxx\\nOutput truncated due to length.'

    >>> text = 'federalist is c00l'
    >>> truncate_text(text, limit=20)
    'federalist is c00l'
    '''
    trunc_msg = f'\nOutput truncated due to length.'
    if len(trunc_msg) > limit:
        return text[:limit]

    if len(text + trunc_msg) > limit:
        cutoff = limit - len(trunc_msg)
        text = text[:cutoff] + trunc_msg
    return text


def post_output_log(log_callback_url, source, output, limit=500000):
    '''
    POSTs an `output` log from `source` to the `log_callback_url`.

    If the output length is greater than the limit, then it is truncated
    to that limit (see `truncate_text` function).
    '''
    output = truncate_text(output, limit)

    if not should_skip_logging():
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

    # Send a DELETE to the Federalist build scheduler to alert that
    # the container is available
    requests.delete(builder_callback_url)


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

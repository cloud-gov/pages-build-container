'''Functions for sending remote logs'''

import json
import base64
import requests

def b64string(text):
    '''Base64 encodes a string as utf-8'''
    return base64.b64encode(text.encode('utf-8'))


# TODO: re-examine original sh file to make sure
# these do the same thing

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
        data=json.dumps({
            'source': source,
            'output': b64string(output),
        })
    )


def post_status(status_callback_url, status, output):
    '''
    POSTs `status` and `output` to the `status_callback_url`
    '''
    requests.post(
        status_callback_url,
        data=json.dumps({
            'status': status,
            'message': b64string(output),
        })
    )


def post_build_complete(builder_callback_url, status_callback_url):
    post_status(
        status_callback_url,
        status=0,
        output='')

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

'''
Setup nice logs.
Clients should use the `get_logger` method to get a logger instance.
'''

import os
import sys
import logging

LOG_FORMATTER = logging.Formatter(
    "{asctime} {levelname} [{name}] @buildId: {buildid} @owner: {owner} @repo: {repo} @branch: {branch}: {message}",
    datefmt='%Y-%m-%d %H:%M:%S',
    style='{'
)

LOG_HANDLER = logging.StreamHandler(sys.stdout)
LOG_HANDLER.setFormatter(LOG_FORMATTER)


def get_logger(name):
    '''
    Gets a logger instance configured with our formatter and handler
    for the given name.
    '''
    logger = logging.getLogger(name)
    logger.setLevel(os.environ.get('LOGLEVEL', logging.INFO))
    logger.addHandler(LOG_HANDLER)

    BRANCH = os.environ['BRANCH']
    BUILD_ID = os.environ['BUILD_ID']
    OWNER = os.environ['OWNER']
    REPO = os.environ['REPOSITORY']

    return logging.LoggerAdapter(logger, {
        'buildid': BUILD_ID,
        'owner': OWNER,
        'repo': REPO,
        'branch': BRANCH
    })

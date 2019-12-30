'''
Setup nice logs.
Clients should use the `get_logger` method to get a logger instance.
'''

import os
import sys
import logging
import logging.handlers

from .db_handler import DBHandler
from .batch_http_handler import BatchHTTPHandler
from .remote_logs import should_skip_logging


class LogFilter(logging.Filter):
    def filter(self, record):
        private_values = [
            os.environ['AWS_ACCESS_KEY_ID'],
            os.environ['AWS_SECRET_ACCESS_KEY']
        ]
        GITHUB_TOKEN = os.getenv('GITHUB_TOKEN', '')
        if GITHUB_TOKEN:
            private_values.append(GITHUB_TOKEN)

        for priv_val in private_values:
            record.msg = record.msg.replace(
                priv_val, '[PRIVATE VALUE HIDDEN]')

        if "InvalidAccessKeyId" in record.msg:
            record.msg = (
                'Whoops, our S3 keys were rotated during your '
                'build and became out of date. This was not a '
                'problem with your site build, but if you restart '
                'the failed build it should work on the next try. '
                'Sorry for the inconvenience!'
            )

        return len(record.msg) > 0


class Formatter(logging.Formatter):
    '''
    A more forgiving formatter that will fill in blank values if our custom
    attributes are missing
    '''
    def format(self, record):
        '''
        Add missing values before formatting as normal
        '''
        keys = ['buildid', 'owner', 'repo', 'branch']
        for key in keys:
            if (key not in record.__dict__):
                record.__dict__[key] = ''

        return super().format(record)


class StreamToLogger:
    def __init__(self, logger, log_level=logging.INFO):
        self.logger = logger
        self.log_level = log_level

    def write(self, buf):
        for line in buf.rstrip().splitlines():
            self.logger.log(self.log_level, line.rstrip())

    def flush(self):
        pass


def get_logger(name):
    '''
    Gets a logger instance configured with our formatter and handler
    for the given name.
    '''
    logger = logging.getLogger(name)

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


class HTTPHandler(BatchHTTPHandler):
    def mapLogRecord(self, record):
        keys = [
            'name', 'levelname', 'buildid', 'owner',
            'repo', 'branch', 'message', 'asctime'
        ]

        return {k: getattr(record, k, '') for k in keys}


def init_logging():
    date_format = '%Y-%m-%d %H:%M:%S'
    style_format = '{'

    long_format = ('{asctime} '
                   '{levelname} '
                   '[{name}] '
                   '@buildId: {buildid} '
                   '@owner: {owner} '
                   '@repo: {repo} '
                   '@branch: {branch} '
                   '@message: {message}')

    short_format = ('{asctime} '
                    '{levelname} '
                    '[{name}] '
                    '{message}')

    stream_handler = logging.StreamHandler(sys.stdout)
    stream_handler.setFormatter(
        Formatter(long_format, datefmt=date_format, style=style_format))
    stream_handler.setLevel(logging.INFO)
    stream_handler.addFilter(LogFilter())

    handlers = [stream_handler]

    if not should_skip_logging():
        LOG_HTTP_HOST = os.environ.get('LOG_HTTP_HOST', '')
        if LOG_HTTP_HOST:
            host = LOG_HTTP_HOST.rstrip('/')
            url = '/' + os.environ.get('LOG_HTTP_PATH', '').lstrip('/')
            buffered_lines = os.environ.get('LOG_HTTP_BATCH_SIZE', 10)
            http_handler = HTTPHandler(buffered_lines, host, url)
            http_handler.setLevel(logging.INFO)
            http_handler.addFilter(LogFilter())
            handlers.append(http_handler)

    if not should_skip_logging():
        DB_URL = os.environ.get('DB_URL', '')
        if DB_URL:
            db_handler = DBHandler(DB_URL, os.environ['BUILD_ID'])
            db_handler.setFormatter(
                logging.Formatter(
                    short_format, datefmt=date_format, style=style_format))
            db_handler.setLevel(logging.INFO)
            db_handler.addFilter(LogFilter())
            handlers.append(db_handler)

    logging.basicConfig(level=logging.INFO, handlers=handlers)

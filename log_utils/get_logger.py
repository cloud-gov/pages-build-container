'''
Setup nice logs.
Clients should use the `get_logger` method to get a logger instance.
'''

import os
import sys
import logging
import logging.handlers

from .db_handler import DBHandler
from .remote_logs import should_skip_logging


class LogFilter(logging.Filter):
    def __init__(self, priv_vals, mask='[PRIVATE VALUE HIDDEN]'):
        self.priv_vals = priv_vals
        self.mask = mask
        logging.Filter.__init__(self)

    def filter(self, record):
        for priv_val in self.priv_vals:
            record.msg = record.msg.replace(priv_val, self.mask)

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
    def __init__(self, keys, *args, **kwargs):
        self.keys = keys
        logging.Formatter.__init__(self, *args, **kwargs)

    def format(self, record):
        '''
        Add missing values before formatting as normal
        '''
        for key in self.keys:
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


def init_logging():
    date_fmt = '%Y-%m-%d %H:%M:%S'
    style_fmt = '{'

    long_fmt = ('{asctime} '
                '{levelname} '
                '[{name}] '
                '@buildId: {buildid} '
                '@owner: {owner} '
                '@repo: {repo} '
                '@branch: {branch} '
                '@message: {message}')

    short_fmt = ('{asctime} {levelname} [{name}] {message}')

    extra_attrs = ['buildid', 'owner', 'repo', 'branch']

    private_values = [
        os.environ['AWS_ACCESS_KEY_ID'],
        os.environ['AWS_SECRET_ACCESS_KEY']
    ]
    GITHUB_TOKEN = os.getenv('GITHUB_TOKEN', '')
    if GITHUB_TOKEN:
        private_values.append(GITHUB_TOKEN)

    log_filter = LogFilter(private_values)

    log_level = logging.INFO

    stream_formatter = Formatter(extra_attrs, long_fmt, date_fmt, style_fmt)

    stream_handler = logging.StreamHandler(sys.stdout)
    stream_handler.setFormatter(stream_formatter)
    stream_handler.setLevel(log_level)
    stream_handler.addFilter(log_filter)

    handlers = [stream_handler]

    if not should_skip_logging():
        DB_URL = os.environ.get('DB_URL', '')
        buildId = os.environ['BUILD_ID']
        if DB_URL:
            db_formatter = logging.Formatter(short_fmt, date_fmt, style_fmt)

            db_handler = DBHandler(DB_URL, buildId)
            db_handler.setFormatter(db_formatter)
            db_handler.setLevel(log_level)
            db_handler.addFilter(log_filter)

            handlers.append(db_handler)

    logging.basicConfig(level=log_level, handlers=handlers)

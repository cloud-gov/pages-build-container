'''
Setup nice logs.
Clients should use the `get_logger` method to get a logger instance.
'''

import os
import sys
import logging
import logging.handlers


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

    short_format = '{asctime} {levelname}: {message}'

    stream_handler = logging.StreamHandler(sys.stdout)
    stream_handler.setFormatter(
        logging.Formatter(
            long_format, datefmt=date_format, style=style_format))
    stream_handler.setLevel(logging.INFO)
    stream_handler.addFilter(LogFilter())

    # not used...yet
    host = ''
    url = ''
    http_handler = logging.handlers.HTTPHandler(host, url, method='POST')
    http_handler.setFormatter(
        logging.Formatter(
            short_format, datefmt=date_format, style=style_format))
    http_handler.setLevel(logging.INFO)
    http_handler.addFilter(LogFilter())

    logging.basicConfig(
        level=logging.DEBUG,
        handlers=[stream_handler]
    )

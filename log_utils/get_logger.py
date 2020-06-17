'''
Setup nice logs.
Clients should use the `get_logger` method to get a logger instance.
'''

import sys
import logging
import logging.handlers

from .db_handler import DBHandler

DEFAULT_LOG_LEVEL = logging.INFO

LOG_ATTRS = {}


class LogFilter(logging.Filter):
    '''
    For every log message, replaces any of the values found in `priv_values`
    with the provided or default `mask` text. In addition, this prevents empty
    messages from being logged at all.
    '''
    DEFAULT_MASK = '[PRIVATE VALUE HIDDEN]'
    INVALID_ACCESS_KEY = 'InvalidAccessKeyId'

    def __init__(self, priv_vals, mask=DEFAULT_MASK):
        self.priv_vals = priv_vals
        self.mask = mask
        logging.Filter.__init__(self)

    def filter(self, record):
        for priv_val in self.priv_vals:
            record.msg = record.msg.replace(priv_val, self.mask)

        if self.INVALID_ACCESS_KEY in record.msg:
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
    DEFAULT_LEVEL = logging.INFO

    def __init__(self, logger, log_level=DEFAULT_LEVEL):
        self.logger = logger
        self.log_level = log_level

    def write(self, buf):
        for line in buf.rstrip().splitlines():
            self.logger.log(self.log_level, line.rstrip())

    def flush(self):
        pass


def get_logger(name, attrs=None):
    '''
    Gets a logger instance configured with our formatter and handler
    for the given name.
    '''
    logger = logging.getLogger(name)

    if not attrs:
        attrs = LOG_ATTRS

    return logging.LoggerAdapter(logger, attrs)


def init_logging(private_values, attrs={}, db_url=None, skip_logging=False):
    global LOG_ATTRS
    LOG_ATTRS = attrs

    date_fmt = '%Y-%m-%d %H:%M:%S'
    style_fmt = '{'
    short_fmt = '{asctime} {levelname} [{name}] {message}'
    long_fmt = '{asctime} {levelname} [{name}] '
    for key in attrs.keys():
        long_fmt = long_fmt + '@' + key + ': {' + key + '} '

    long_fmt = long_fmt + '@message: {message}'

    extra_attrs = attrs.keys()

    log_filter = LogFilter(private_values)

    log_level = DEFAULT_LOG_LEVEL

    stream_formatter = Formatter(extra_attrs, long_fmt, date_fmt, style_fmt)

    stream_handler = logging.StreamHandler(sys.stdout)
    stream_handler.setFormatter(stream_formatter)
    stream_handler.setLevel(log_level)
    stream_handler.addFilter(log_filter)

    handlers = [stream_handler]

    if not skip_logging and db_url:
        build_id = attrs['buildid']
        db_formatter = logging.Formatter(short_fmt, date_fmt, style_fmt)

        db_handler = DBHandler(db_url, build_id)
        db_handler.setFormatter(db_formatter)
        db_handler.setLevel(log_level)
        db_handler.addFilter(log_filter)

        handlers.append(db_handler)

    logging.basicConfig(level=log_level, handlers=handlers)

import logging

from log_utils.get_logger import LogFilter


class TestLogFilter():
    def test_it_filters_message_with_default_mask(self):
        priv_values = ['foobar']
        msg = 'hellofoobar'

        filter = LogFilter(priv_values)
        record = logging.makeLogRecord({'msg': msg})
        result = filter.filter(record)

        assert(result is True)
        assert(record.getMessage() == f'hello{LogFilter.DEFAULT_MASK}')

    def test_it_filters_message_with_custom_mask(self):
        priv_values = ['foobar']
        mask = 'TheNumber42'
        msg = 'hellofoobar'

        filter = LogFilter(priv_values, mask)
        record = logging.makeLogRecord({'msg': msg})
        result = filter.filter(record)

        assert(result is True)
        assert(record.getMessage() == f'hello{mask}')

    def test_it_does_not_log_empty_messages(self):
        priv_values = []
        msg = ''

        filter = LogFilter(priv_values)
        record = logging.makeLogRecord({'msg': msg})
        result = filter.filter(record)

        assert(result is False)

    def test_it_replaces_message_invalid_access_key(self):
        priv_values = []
        msg = f'hello{LogFilter.INVALID_ACCESS_KEY}'

        filter = LogFilter(priv_values)
        record = logging.makeLogRecord({'msg': msg})
        result = filter.filter(record)

        assert(result is True)
        assert(record.getMessage() == (
            'Whoops, our S3 keys were rotated during your '
            'build and became out of date. This was not a '
            'problem with your site build, but if you restart '
            'the failed build it should work on the next try. '
            'Sorry for the inconvenience!'
        ))

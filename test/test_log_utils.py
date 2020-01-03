import logging
from unittest.mock import Mock, patch

from log_utils.get_logger import (
    LogFilter, Formatter, StreamToLogger, get_logger)


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


class TestFormatter():
    @patch('logging.Formatter.format')
    def test_it_populates_empty_strings_if_key_is_missing(self, mock_format):
        keys = ['foobar']

        formatter = Formatter(keys)
        record = logging.makeLogRecord({})

        formatter.format(record)

        assert(record.foobar == '')
        mock_format.assert_called_once_with(record)

    @patch('logging.Formatter.format')
    def test_it_ignores_key_if_present(self, mock_format):
        keys = ['foobar']

        formatter = Formatter(keys)
        record = logging.makeLogRecord({'foobar': 'Hello!'})

        formatter.format(record)

        assert(record.foobar == 'Hello!')
        mock_format.assert_called_once_with(record)


class TestStreamLogger():
    def test_it_writes_to_provided_logger_with_default_level(self):
        mock_logger = Mock()
        mock_logger.log = Mock()
        message = 'foo'

        streamLogger = StreamToLogger(mock_logger)

        streamLogger.write(message)
        mock_logger.log.assert_called_once_with(StreamToLogger.DEFAULT_LEVEL,
                                                message)

    def test_it_writes_to_provided_logger_with_provided_level(self):
        mock_logger = Mock()
        mock_logger.log = Mock()
        message = 'foo'
        level = logging.WARN

        streamLogger = StreamToLogger(mock_logger, level)

        streamLogger.write(message)

        mock_logger.log.assert_called_once_with(level, message)

    def test_it_breaks_lines_and_strips_trailing_whitespace(self):
        mock_logger = Mock()
        mock_logger.log = Mock()
        message = 'foo \nbar    '

        streamLogger = StreamToLogger(mock_logger)

        streamLogger.write(message)

        assert(mock_logger.log.call_count == 2)
        mock_logger.log.assert_any_call(StreamToLogger.DEFAULT_LEVEL, 'foo')
        mock_logger.log.assert_any_call(StreamToLogger.DEFAULT_LEVEL, 'bar')

    def test_it_has_a_flush_method(self):
        streamLogger = StreamToLogger(Mock())

        flush = getattr(streamLogger, 'flush')
        assert(callable(flush) is True)


class TestGetLogger():
    def test_it_returns_a_logger_with_an_adapter_with_extras(self):
        name = 'foobar'
        attrs = {'foo': 'bar'}

        adapter = get_logger(name, attrs)

        assert(type(adapter) == logging.LoggerAdapter)
        assert(adapter.logger.name == name)
        assert(adapter.extra == attrs)

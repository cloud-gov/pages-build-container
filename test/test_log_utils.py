import logging
from unittest.mock import patch
from time import sleep

from log_utils.get_logger import (
    LogFilter, Formatter, get_logger, init_logging,
    set_log_attrs, DEFAULT_LOG_LEVEL)
from log_utils.db_handler import DBHandler
from log_utils.monitoring import RepeatTimer, log_monitoring_metrics


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


class TestGetLogger():
    def test_it_returns_a_logger_with_an_adapter_with_extras(self):
        name = 'foobar'
        attrs = {'foo': 'bar'}
        set_log_attrs(attrs)

        adapter = get_logger(name)

        assert(type(adapter) == logging.LoggerAdapter)
        assert(adapter.logger.name == name)
        assert(adapter.extra == attrs)


@patch('psycopg2.connect')
@patch('logging.basicConfig')
class TestInitLogging():
    def test_it_adds_a_stream_and_db_handlers(self, mock_basic_config, _):
        init_logging([], {'buildid': 1234}, 'foo')

        _, kwargs = mock_basic_config.call_args

        assert(kwargs['level'] == DEFAULT_LOG_LEVEL)
        assert(len(kwargs['handlers']) == 2)
        assert(type(kwargs['handlers'][0]) == logging.StreamHandler)
        assert(type(kwargs['handlers'][1]) == DBHandler)


@patch('log_utils.monitoring.log_monitoring_metrics')
class TestMonitorLogging():
    def test_it_calls_logger_on_schedule(self, mock_metrics_logger):
        logger = get_logger('test')
        thread = RepeatTimer(1, mock_metrics_logger, [logger])
        thread.start()
        sleep(5)
        mock_metrics_logger.assert_called_with(logger)
        thread.cancel()

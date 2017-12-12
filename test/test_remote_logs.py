from unittest.mock import patch

from log_utils.remote_logs import (
    b64string,
    post_output_log, post_build_complete,
    post_build_error, post_build_timeout)


MOCK_LOG_URL = 'https://log.example.com'
MOCK_STATUS_URL = 'https://status.example.com'
MOCK_BUILDER_URL = 'https://builder.example.com'


class TestPostOutputLog():
    @patch('requests.post')
    def test_it_works(self, mock_post):
        post_output_log(MOCK_LOG_URL, 'test', 'test output')
        mock_post.assert_called_once_with(MOCK_LOG_URL, json={
            'source': 'test',
            'output': b64string('test output'),
        })

    @patch('requests.post')
    def test_log_is_truncated(self, mock_post):
        post_output_log(MOCK_LOG_URL, 'test', 'boopboop', limit=4)
        mock_post.assert_called_once_with(MOCK_LOG_URL, json={
            'source': 'test',
            'output': b64string('boop'),
        })


@patch('requests.post')
@patch('requests.delete')
def test_post_build_complete(mock_del, mock_post):
    post_build_complete(MOCK_STATUS_URL, MOCK_BUILDER_URL)
    mock_post.assert_called_once_with(
        MOCK_STATUS_URL, json={'status': 0, 'message': ''})
    mock_del.assert_called_once_with(MOCK_BUILDER_URL)


@patch('requests.post')
@patch('requests.delete')
def test_post_build_error(mock_del, mock_post):
    post_build_error(MOCK_LOG_URL, MOCK_STATUS_URL,
                     MOCK_BUILDER_URL, 'error message')

    assert mock_post.call_count == 2
    mock_post.assert_any_call(
        MOCK_LOG_URL,
        json={'source': 'ERROR', 'output': b64string('error message')}
    )

    mock_post.assert_any_call(
        MOCK_STATUS_URL,
        json={'status': 1, 'message': b64string('error message')}
    )

    mock_del.assert_called_once_with(MOCK_BUILDER_URL)


@patch('requests.post')
@patch('requests.delete')
def test_post_build_timeout(mock_del, mock_post):
    post_build_timeout(MOCK_LOG_URL, MOCK_STATUS_URL, MOCK_BUILDER_URL)

    expected_output = b64string(
        'The build did not complete. It may have timed out.')

    assert mock_post.call_count == 2
    mock_post.assert_any_call(
        MOCK_LOG_URL,
        json={'source': 'ERROR', 'output': expected_output}
    )

    mock_post.assert_any_call(
        MOCK_STATUS_URL,
        json={'status': 1, 'message': expected_output}
    )

    mock_del.assert_called_once_with(MOCK_BUILDER_URL)

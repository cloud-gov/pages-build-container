import pytest

from unittest.mock import patch

from log_utils.remote_logs import (
    b64string, post_build_complete,
    post_build_error, post_build_timeout,
    post_build_processing, should_skip_logging)

from log_utils.common import (STATUS_COMPLETE, STATUS_ERROR, STATUS_PROCESSING)

MOCK_STATUS_URL = 'https://status.example.com'
MOCK_BUILDER_URL = 'https://builder.example.com'


@pytest.mark.parametrize('skip_logging, expected', [
    ('true', True),
    ('True', True),
    ('other', False),
    ('', False),
    (None, False),
])
def test_should_skip_logging(skip_logging, expected, monkeypatch):
    monkeypatch.setenv('SKIP_LOGGING', skip_logging)
    assert should_skip_logging() == expected


class TestPostBuildComplete():
    @patch('requests.post')
    @patch('requests.delete')
    def test_it_works(self, mock_del, mock_post):
        post_build_complete(MOCK_STATUS_URL, MOCK_BUILDER_URL)
        mock_post.assert_called_once_with(
            MOCK_STATUS_URL, json={'status': STATUS_COMPLETE, 'message': ''})
        mock_del.assert_called_once_with(MOCK_BUILDER_URL)

    @patch('requests.post')
    @patch('requests.delete')
    def test_it_does_not_post_status_if_SKIP_LOGGING(self, mock_del, mock_post,
                                                     monkeypatch):
        monkeypatch.setenv('SKIP_LOGGING', 'true')
        post_build_complete(MOCK_STATUS_URL, MOCK_BUILDER_URL)
        # the status POST should not be called
        mock_post.assert_not_called()
        # but the builder DELETE should still be called
        mock_del.assert_called_once_with(MOCK_BUILDER_URL)


class TestPostBuildProcessing():
    @patch('requests.post')
    def test_it_works(self, mock_post):
        post_build_processing(MOCK_STATUS_URL)
        mock_post.assert_called_once_with(
            MOCK_STATUS_URL, json={'status': STATUS_PROCESSING, 'message': ''})

    @patch('requests.post')
    def test_it_does_not_post_status_if_SKIP_LOGGING(self, mock_post,
                                                     monkeypatch):
        monkeypatch.setenv('SKIP_LOGGING', 'true')
        post_build_processing(MOCK_STATUS_URL)
        # the status POST should not be called
        mock_post.assert_not_called()


class TestPostBuildError():
    @patch('requests.post')
    @patch('requests.delete')
    def test_it_works(self, mock_del, mock_post):
        post_build_error(MOCK_STATUS_URL, MOCK_BUILDER_URL, 'error msg')

        assert mock_post.call_count == 2
        mock_post.assert_any_call(
            json={'source': 'ERROR', 'output': b64string('error msg')}
        )

        mock_post.assert_any_call(
            MOCK_STATUS_URL,
            json={'status': STATUS_ERROR, 'message': b64string('error msg')}
        )

        mock_del.assert_called_once_with(MOCK_BUILDER_URL)

    @patch('requests.post')
    @patch('requests.delete')
    def test_it_does_not_post_logs_or_status_if_SKIP_LOGGING(
            self, mock_del, mock_post, monkeypatch):
        monkeypatch.setenv('SKIP_LOGGING', 'true')
        post_build_error(MOCK_STATUS_URL,
                         MOCK_BUILDER_URL, 'error message')
        mock_post.assert_not_called()
        # but the builder DELETE should still be called
        mock_del.assert_called_once_with(MOCK_BUILDER_URL)


class TestPostBuildTimeout():
    @patch('requests.post')
    @patch('requests.delete')
    def test_it_works(self, mock_del, mock_post):
        post_build_timeout(MOCK_STATUS_URL, MOCK_BUILDER_URL)

        expected_output = b64string(
            'The build did not complete. It may have timed out.')

        assert mock_post.call_count == 1
        mock_post.assert_any_call(
            MOCK_STATUS_URL,
            json={'status': STATUS_ERROR, 'message': expected_output}
        )

        mock_del.assert_called_once_with(MOCK_BUILDER_URL)

    @patch('requests.post')
    @patch('requests.delete')
    def test_it_does_not_post_logs_or_status_if_SKIP_LOGGING(
            self, mock_del, mock_post, monkeypatch):
        monkeypatch.setenv('SKIP_LOGGING', 'true')
        post_build_timeout(MOCK_STATUS_URL, MOCK_BUILDER_URL)
        mock_post.assert_not_called()
        # but the builder DELETE should still be called
        mock_del.assert_called_once_with(MOCK_BUILDER_URL)

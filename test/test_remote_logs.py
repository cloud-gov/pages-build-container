from unittest.mock import patch

from log_utils.remote_logs import (
    b64string, post_build_complete,
    post_build_error, post_build_timeout,
    post_build_processing)

from log_utils.common import (STATUS_COMPLETE, STATUS_ERROR, STATUS_PROCESSING)

MOCK_STATUS_URL = 'https://status.example.com'


class TestPostBuildComplete():
    @patch('requests.post')
    @patch('requests.delete')
    def test_it_works(self, mock_del, mock_post):
        commit_sha = 'testSha1'
        post_build_complete(MOCK_STATUS_URL, commit_sha)
        mock_post.assert_called_once_with(
            MOCK_STATUS_URL,
            json={'status': STATUS_COMPLETE, 'message': '', 'commit_sha': commit_sha},
            timeout=10
        )


class TestPostBuildProcessing():
    @patch('requests.post')
    def test_it_works(self, mock_post):
        post_build_processing(MOCK_STATUS_URL)
        mock_post.assert_called_once_with(
            MOCK_STATUS_URL,
            json={'status': STATUS_PROCESSING, 'message': '', 'commit_sha': None},
            timeout=10
        )


class TestPostBuildError():
    @patch('requests.post')
    @patch('requests.delete')
    def test_it_works(self, mock_del, mock_post):
        commit_sha = 'testSha2'
        post_build_error(MOCK_STATUS_URL, 'error msg', commit_sha)

        assert mock_post.call_count == 1

        mock_post.assert_any_call(
            MOCK_STATUS_URL,
            json={
                'status': STATUS_ERROR, 'message': b64string('error msg'), 'commit_sha': commit_sha
            },
            timeout=10
        )


class TestPostBuildTimeout():
    @patch('requests.post')
    @patch('requests.delete')
    def test_it_works(self, mock_del, mock_post):
        commit_sha = 'testSha3'
        post_build_timeout(MOCK_STATUS_URL, commit_sha)

        expected_output = b64string(
            'The build did not complete. It may have timed out.')

        assert mock_post.call_count == 1
        mock_post.assert_any_call(
            MOCK_STATUS_URL,
            json={'status': STATUS_ERROR, 'message': expected_output, 'commit_sha': commit_sha},
            timeout=10
        )

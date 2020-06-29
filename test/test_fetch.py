from unittest.mock import patch

from steps import fetch_repo
from common import CLONE_DIR_PATH


@patch('steps.fetch.run')
@patch('steps.fetch.get_logger')
class TestCloneRepo():
    def test_runs_expected_cmds(self, mock_get_logger, mock_run):
        owner = 'owner-1'
        repository = 'repo-1'
        branch = 'main'

        command = (f'git clone -b {branch} --single-branch --depth 1 '
                   f'https://github.com/{owner}/{repository}.git '
                   f'{CLONE_DIR_PATH}')

        fetch_repo(owner, repository, branch)

        mock_get_logger.assert_called_once_with('clone')

        mock_run.assert_called_once_with(mock_get_logger.return_value, command)

    def test_runs_expected_cmds_with_gh_token(self, mock_get_logger, mock_run):
        owner = 'owner-2'
        repository = 'repo-2'
        branch = 'staging'
        github_token = 'ABC123'

        command = (f'git clone -b {branch} --single-branch --depth 1 '
                   f'https://{github_token}@github.com/{owner}/{repository}.git '
                   f'{CLONE_DIR_PATH}')

        fetch_repo(owner, repository, branch, github_token)

        mock_get_logger.assert_called_once_with('clone')

        mock_run.assert_called_once_with(mock_get_logger.return_value, command)

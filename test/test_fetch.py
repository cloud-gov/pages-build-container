from unittest.mock import patch
import subprocess  # nosec

from steps import fetch_repo, update_repo, fetch_commit_sha
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


@patch('steps.fetch.run')
@patch('steps.fetch.get_logger')
class TestUpdateRepo():
    def test_runs_expected_cmds(self, mock_get_logger, mock_run):
        clone_dir = 'clone_dir'

        command = 'git pull --unshallow'

        update_repo(clone_dir)

        mock_get_logger.assert_called_once_with('update')

        mock_run.assert_called_once_with(mock_get_logger.return_value, command, cwd=clone_dir)

@patch('steps.fetch.subprocess.run')
@patch('steps.fetch.get_logger')
class TestFetchCommitSHA():
    def test_runs_expected_cmds(self, mock_get_logger, mock_run):
        mock_run.return_value = subprocess.CompletedProcess(stdout='commit testSha blah blah blah', args = [], returncode=0)
        clone_dir = 'clone_dir'

        command = 'git log -1'
        commit_sha = fetch_commit_sha(clone_dir)

        mock_get_logger.assert_called_once_with('clone')
        mock_run.assert_called_once_with(command, shell=True, check=True, stdout=subprocess.PIPE, universal_newlines=True, cwd=clone_dir)
        assert commit_sha == 'testSha'


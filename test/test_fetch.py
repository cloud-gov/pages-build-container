import logging
import unittest
from unittest.mock import patch
# import subprocess  # nosec
import pytest

from steps import fetch_repo, update_repo
from common import CLONE_DIR_PATH

clone_env = {
    'HOME': '/home'
}


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

        mock_run.assert_called_once_with(mock_get_logger.return_value, command, env=clone_env, check=False)  # noqa: 501

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

        mock_run.assert_called_once_with(mock_get_logger.return_value, command, env=clone_env, check=False)  # noqa: 501

    def test_runs_expected_cmds_with_source_code_platform_config_github(
            self, mock_get_logger, mock_run):
        owner = 'owner-1'
        repository = 'repo-1'
        branch = 'main'
        github_token = 'ABC123'
        source_code_platform = 'github'
        source_code_platform_domain = 'github.com2'
        source_code_platform_token = ''

        command = (f'git clone -b {branch} --single-branch --depth 1 '
                   f'https://github.com2/{owner}/{repository}.git '
                   f'{CLONE_DIR_PATH}')

        fetch_repo(owner, repository, branch, github_token,
                   source_code_platform, source_code_platform_domain, source_code_platform_token)

        mock_get_logger.assert_called_once_with('clone')

        mock_run.assert_called_once_with(mock_get_logger.return_value, command, env=clone_env, check=False)  # noqa: 501

    def test_runs_expected_cmds_with_source_code_platform_config_github_with_token(
            self, mock_get_logger, mock_run):
        owner = 'owner-1'
        repository = 'repo-1'
        branch = 'main'
        github_token = 'ABC123'
        source_code_platform = 'github'
        source_code_platform_domain = 'github2.com'
        source_code_platform_token = 'source_code_platform_ABC123'

        command = (f'git clone -b {branch} --single-branch --depth 1 '
                   f'https://{source_code_platform_token}@github2.com/{owner}/{repository}.git '
                   f'{CLONE_DIR_PATH}')

        fetch_repo(owner, repository, branch, github_token,
                   source_code_platform, source_code_platform_domain, source_code_platform_token)

        mock_get_logger.assert_called_once_with('clone')

        mock_run.assert_called_once_with(mock_get_logger.return_value, command, env=clone_env, check=False)  # noqa: 501

    def test_runs_expected_cmds_with_source_code_platform_config_workshop(
            self, mock_get_logger, mock_run):
        owner = 'owner-1'
        repository = 'repo-1'
        branch = 'main'
        github_token = 'ABC123'
        source_code_platform = 'workshop'
        source_code_platform_domain = 'workshop.cloud.gov'
        source_code_platform_token = ''

        command = (f'git clone -b {branch} --single-branch --depth 1 '
                   f'https://{source_code_platform_domain}/{owner}/{repository}.git '
                   f'{CLONE_DIR_PATH}')

        fetch_repo(owner, repository, branch, github_token,
                   source_code_platform, source_code_platform_domain, source_code_platform_token)

        mock_get_logger.assert_called_once_with('clone')

        mock_run.assert_called_once_with(mock_get_logger.return_value, command, env=clone_env, check=False)  # noqa: 501

    def test_runs_expected_cmds_with_source_code_platform_config_workshop_with_token(
            self, mock_get_logger, mock_run):
        owner = 'owner-1'
        repository = 'repo-1'
        branch = 'main'
        github_token = 'ABC123'
        source_code_platform = 'workshop'
        source_code_platform_domain = 'workshop.cloud.gov'
        source_code_platform_token = 'source_code_platform_ABC123'

        command = (f'git clone -b {branch} --single-branch --depth 1 '
                   f'https://{source_code_platform_token}@'
                   f'{source_code_platform_domain}/{owner}/{repository}.git '
                   f'{CLONE_DIR_PATH}')

        fetch_repo(owner, repository, branch, github_token,
                   source_code_platform, source_code_platform_domain, source_code_platform_token)

        mock_get_logger.assert_called_once_with('clone')

        mock_run.assert_called_once_with(mock_get_logger.return_value, command, env=clone_env, check=False)  # noqa: 501


class TestCloneRepoNoMock(unittest.TestCase):
    @pytest.fixture(autouse=True)
    def inject_fixtures(self, caplog):
        self._caplog = caplog

    def test_no_github_permission_warning(self):
        owner = 'cloud-gov'
        repository = 'cg-site'
        branch = 'master'

        # TODO: this is a totally useless test because the CI runner doesn't have git
        with self._caplog.at_level(logging.INFO):
            fetch_repo(owner, repository, branch)

        assert self._caplog.text
        assert 'Permission denied' not in self._caplog.text


@patch('steps.fetch.run')
@patch('steps.fetch.get_logger')
class TestUpdateRepo():
    def test_runs_expected_cmds(self, mock_get_logger, mock_run):
        clone_dir = 'clone_dir'

        command = 'git pull --unshallow'

        update_repo(clone_dir)

        mock_get_logger.assert_called_once_with('update')

        mock_run.assert_called_once_with(mock_get_logger.return_value, command, cwd=clone_dir)


# @patch('steps.fetch.subprocess.run')
# @patch('steps.fetch.get_logger')
# class TestFetchCommitSHA():
#     def test_runs_expected_cmds(self, mock_get_logger, mock_run):
#         mock_run.return_value = subprocess.CompletedProcess([], 0, 'commit testSha blah blah')
#         clone_dir = 'clone_dir'

#         command = ['git', 'log', '-1']
#         commit_sha = fetch_commit_sha(clone_dir)

#         mock_get_logger.assert_called_once_with('clone')
#         mock_run.assert_called_once_with(
#             command,
#             shell=False,  # nosec
#             check=True,
#             stdout=subprocess.PIPE,
#             universal_newlines=True,
#             cwd=clone_dir
#         )
#         assert commit_sha == 'testSha'

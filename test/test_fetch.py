import shlex
from unittest.mock import Mock

from steps import fetch_repo
from tasks.common import CLONE_DIR_PATH


class TestCloneRepo():
    def test_runs_expected_cmds(self):
        owner = 'owner-1'
        repository = 'repo-1'
        branch = 'main'

        mockRun = Mock()

        command = (f'git clone -b {branch} --single-branch --depth 1 '
                   f'https://github.com/{owner}/{repository}.git '
                   f'{CLONE_DIR_PATH}')

        fetch_repo(mockRun, owner, repository, branch)

        mockRun.assert_called_once_with(shlex.split(command))

    def test_runs_expected_cmds_with_gh_token(self):
        owner = 'owner-2'
        repository = 'repo-2'
        branch = 'staging'
        github_token = 'ABC123'

        mockRun = Mock()

        command = (f'git clone -b {branch} --single-branch --depth 1 '
                   f'https://{github_token}@github.com/{owner}/{repository}.git '
                   f'{CLONE_DIR_PATH}')

        fetch_repo(mockRun, owner, repository, branch, github_token)

        mockRun.assert_called_once_with(shlex.split(command))

import pytest

from invoke import MockContext, Result

from tasks import clone_repo
from tasks.common import CLONE_DIR_PATH


class TestCloneRepo():
    @pytest.mark.parametrize('owner, repo, branch, dp', [
        ('owner-1', 'repo-1', 'master', '--depth 1'),
        ('owner-2', 'repo-2', 'funkybranch', None),
    ])
    def test_runs_expected_cmds(self, monkeypatch, owner, repo, branch, dp):
        monkeypatch.setenv('GITHUB_TOKEN', 'fake-token')
        clone_cmd = (f'git clone -b {branch} --single-branch {dp} '
                     f'https://fake-token@github.com/{owner}/{repo}.git '
                     f'{CLONE_DIR_PATH}')
        ctx = MockContext(run={
            clone_cmd: Result()
        })
        clone_repo(ctx, owner=owner, repository=repo, branch=branch, depth=dp)
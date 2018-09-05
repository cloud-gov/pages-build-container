import pytest

from invoke import MockContext, Result

from tasks import clone_repo, push_repo_remote
from tasks.common import CLONE_DIR_PATH


class TestCloneRepo():
    @pytest.mark.parametrize('owner, repo, branch', [
        ('owner-1', 'repo-1', 'master'),
        ('owner-2', 'repo-2', 'funkybranch'),
    ])
    def test_it_runs_expected_commands(self, monkeypatch, owner, repo, branch):
        monkeypatch.setenv('GITHUB_TOKEN', 'fake-token')
        clone_cmd = (f'git clone -b {branch} --single-branch --depth=1 '
                     f'https://fake-token@github.com/{owner}/{repo}.git '
                     f'{CLONE_DIR_PATH}')
        ctx = MockContext(run={
            clone_cmd: Result()
        })
        clone_repo(ctx, owner=owner, repository=repo, branch=branch)


class TestPushRepoRemote():
    @pytest.mark.parametrize('owner, repo, branch, remote', [
        ('owner-1', 'repo-1', 'master', 'remote-1'),
        ('owner-2', 'repo-2', 'funkybranch', 'remote-2'),
    ])
    def test_it_runs_expected_commands(self, monkeypatch, owner,
                                       repo, branch, remote):
        monkeypatch.setenv('GITHUB_TOKEN', 'fake-token')

        # expected commands to run
        add_remote_cmd = (f'git remote add {remote} '
                          f'https://fake-token@github.com/{owner}/{repo}.git')
        push_cmd = f'git push {remote} {branch}:master'

        ctx = MockContext(run={
            add_remote_cmd: Result(),
            push_cmd: Result()
        })
        push_repo_remote(ctx, owner=owner, repository=repo, branch=branch,
                         remote_name=remote)

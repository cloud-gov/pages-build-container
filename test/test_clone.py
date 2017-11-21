import os

from invoke import MockContext, Result

from tasks import clone_repo, push_repo_remote


class TestCloneRepo():
    def test_it_is_callable(self):
        os.environ['GITHUB_TOKEN'] = 'fake_token'
        ctx = MockContext(run=Result('git clone result'))
        clone_repo(ctx, owner='owner', repository='repo', branch='master')


class TestPushRepoRemote():
    def test_it_is_callable(self):
        os.environ['GITHUB_TOKEN'] = 'fake_token'

        ctx = MockContext(run=[
            Result('git remote add result'),
            Result('git push result')
            ]
        )
        push_repo_remote(ctx, owner='owner', repository='repo',
                         branch='branch', remote_name='boop')

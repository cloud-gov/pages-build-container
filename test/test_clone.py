import os

from invoke import MockContext, Result

from tasks import clone_repo

# See http://docs.pyinvoke.org/en/latest/concepts/testing.html


def test_clone():
    # TODO
    os.environ['GITHUB_TOKEN'] = 'fake_token'
    ctx = MockContext(run=Result("TODO\n"))
    clone_repo(ctx, owner='owner', repository='repo', branch='master')

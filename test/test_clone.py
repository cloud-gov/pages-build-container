from invoke import MockContext, Result

from tasks import clean, clone_repo

# See http://docs.pyinvoke.org/en/latest/concepts/testing.html

# TODO
def test_clone():
    c = MockContext(run=Result("TODO\n"))
    clone_repo(c, owner='owner', repository='repo', branch='master',
               github_token='token')

# TODO
def test_clean():
    pass

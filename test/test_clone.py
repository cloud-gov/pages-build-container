from invoke import MockContext, Result

from tasks import clean, clone

# See http://docs.pyinvoke.org/en/latest/concepts/testing.html

# TODO
def test_clone():
    c = MockContext(run=Result("TODO\n"))
    clone(c, 'owner', 'repo', 'token')

# TODO
def test_clean():
    pass

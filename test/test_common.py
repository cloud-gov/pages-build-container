import shutil

import pytest

from invoke import MockContext

import tasks
from .support import patch_dir


@pytest.fixture
def patch_clone_dir(monkeypatch):
    yield from patch_dir(monkeypatch, tasks.common, 'CLONE_DIR_PATH')


class TestClean():
    def test_cleans_clone_dir_by_default(self, monkeypatch, patch_clone_dir):
        ctx = MockContext()

        def mock_rmtree(which, ignore_errors=False):
            assert str(which) == str(patch_clone_dir)

        monkeypatch.setattr(shutil, 'rmtree', mock_rmtree)
        tasks.clean(ctx)
        # clear the patch so that the temp patch_clone_dir
        # will also be properly deleted upon exit
        monkeypatch.undo()

    def test_cleans_specified_dir(self, monkeypatch):
        ctx = MockContext()

        def mock_rmtree(which, ignore_errors=False):
            assert str(which) == '/whatever'

        monkeypatch.setattr(shutil, 'rmtree', mock_rmtree)
        tasks.clean(ctx, which='/whatever')

        # clear the patch so that the temp patch_clone_dir
        # will also be properly deleted upon exit
        monkeypatch.undo()

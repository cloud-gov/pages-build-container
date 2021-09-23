import json
import os
import repo_config
import pytest
from .support import create_file, patch_dir
import steps


@pytest.fixture
def patch_clone_dir(monkeypatch):
    yield from patch_dir(monkeypatch, steps.build, 'CLONE_DIR_PATH')


class TestRepoConfig():
    def test_it_loads_federalist_json_when_it_exists(self, patch_clone_dir):
        filename = 'federalist.json'
        json_contents = json.dumps({
            'name': filename,
        })
        create_file(patch_clone_dir / filename, contents=json_contents)
        result = repo_config.from_json_file(patch_clone_dir)
        assert result.config['name'] == filename
        assert len(os.listdir(patch_clone_dir)) == 1

    def test_it_loads_pages_json_when_it_exists(self, patch_clone_dir):
        filename = 'pages.json'
        json_contents = json.dumps({
            'name': filename,
        })
        create_file(patch_clone_dir / filename, contents=json_contents)
        result = repo_config.from_json_file(patch_clone_dir)
        assert result.config['name'] == filename
        assert len(os.listdir(patch_clone_dir)) == 1

    def test_it_loads_pages_json_when_federalist_json_also_exists(self, patch_clone_dir):
        filename = 'federalist.json'
        json_contents = json.dumps({
            'name': filename,
        })
        create_file(patch_clone_dir / filename, contents=json_contents)
        filename = 'pages.json'
        json_contents = json.dumps({
            'name': filename,
        })
        create_file(patch_clone_dir / filename, contents=json_contents)
        result = repo_config.from_json_file(patch_clone_dir)
        assert result.config['name'] == 'pages.json'
        assert len(os.listdir(patch_clone_dir)) == 2

import json
import os
from contextlib import ExitStack
from unittest.mock import Mock

import pytest
import requests_mock
from invoke import MockContext, Result

import tasks
from tasks.build import (GEMFILE, HUGO_BIN, JEKYLL_CONFIG_YML, NVMRC,
                         PACKAGE_JSON, RUBY_VERSION, node_context,
                         HUGO_VERSION, BUNDLER_VERSION)

from .support import create_file, patch_dir

# TODO: Figure out how to test/ensure that pre-tasks are properly
# specified


@pytest.fixture
def patch_clone_dir(monkeypatch):
    yield from patch_dir(monkeypatch, tasks.build, 'CLONE_DIR_PATH')


@pytest.fixture
def patch_working_dir(monkeypatch):
    yield from patch_dir(monkeypatch, tasks.build, 'WORKING_DIR_PATH')


@pytest.fixture
def patch_site_build_dir(monkeypatch):
    yield from patch_dir(monkeypatch, tasks.build, 'SITE_BUILD_DIR_PATH')


class TestSetupNode():
    def test_it_uses_nvmrc_file_if_it_exists(self, patch_clone_dir):
        create_file(patch_clone_dir / NVMRC, contents='6')
        ctx = MockContext(run={
            'nvm install': Result(),
        })
        tasks.setup_node(ctx)

    def test_installs_production_deps(self, patch_clone_dir):
        create_file(patch_clone_dir / PACKAGE_JSON)
        ctx = MockContext(run={
            'node --version': Result(),
            'npm --version': Result(),
            'npm install --production': Result(),
        })
        tasks.setup_node(ctx)


class TestNodeContext():
    def test_default_node_context(self):
        ctx = MockContext()
        context_stack = node_context(ctx)
        assert type(context_stack) == ExitStack
        assert len(context_stack._exit_callbacks) == 1

    def test_it_appends_nvm_when_nvmrc_exists(self, patch_clone_dir):
        create_file(patch_clone_dir / NVMRC, '4.2')
        ctx = MockContext()
        context_stack = node_context(ctx)
        assert type(context_stack) == ExitStack
        assert len(context_stack._exit_callbacks) == 2

    def test_node_context_accepts_more_contexts(self):
        ctx = MockContext()
        context_stack = node_context(ctx, ctx.cd('boop'))
        assert type(context_stack) == ExitStack
        assert len(context_stack._exit_callbacks) == 2


class TestRunFederalistScript():
    def test_it_runs_federalist_script_when_it_exists(self, patch_clone_dir):
        package_json_contents = json.dumps({
            'scripts': {
                'federalist': 'echo hi',
            },
        })
        create_file(patch_clone_dir / PACKAGE_JSON, package_json_contents)
        ctx = MockContext(run={
            'npm run federalist': Result(),
        })
        tasks.run_federalist_script(ctx, branch='branch', owner='owner',
                                    repository='repo',
                                    site_prefix='site/prefix',
                                    base_url='/site/prefix')

    def test_it_does_not_run_otherwise(self, patch_clone_dir):
        ctx = MockContext()
        kwargs = dict(branch='branch', owner='owner',
                      repository='repo',
                      site_prefix='site/prefix',
                      base_url='/site/prefix')
        tasks.run_federalist_script(ctx, **kwargs)


class TestSetupRuby():
    def test_it_is_callable(self):
        ctx = MockContext(run={
            'ruby -v': Result(),
        })
        tasks.setup_ruby(ctx)

    def test_it_uses_ruby_version_if_it_exists(self, patch_clone_dir):
        create_file(patch_clone_dir / RUBY_VERSION, '2.3')
        ctx = MockContext(run={
            'rvm install 2.3': Result(),
            'ruby -v': Result(),
        })
        tasks.setup_ruby(ctx)

        # ruby_version should be strippeed and quoted as well
        create_file(patch_clone_dir / RUBY_VERSION, '  $2.2  ')
        ctx = MockContext(run={
            "rvm install '$2.2'": Result(),
            'ruby -v': Result(),
        })
        tasks.setup_ruby(ctx)


class TestSetupBundler():
    def test_it_uses_bundler_version_if_it_exists(self, patch_clone_dir):
        ctx = MockContext(run={
            'gem install bundler --version "<2"': Result(),
        })
        tasks.setup_bundler(ctx)

        create_file(patch_clone_dir / BUNDLER_VERSION, '2.0.1')
        ctx = MockContext(run={
            'gem install bundler --version "2.0.1"': Result(),
        })
        tasks.setup_bundler(ctx)


class TestBuildJekyll():
    def test_it_is_callable(self, patch_clone_dir):
        ctx = MockContext(run=[
            Result('gem install jekyll result'),
            Result('jekyll version result'),
            Result('jekyll build result'),
        ])

        contents = 'hi: test'
        create_file(patch_clone_dir / JEKYLL_CONFIG_YML, contents)
        tasks.build_jekyll(ctx, branch='branch', owner='owner',
                           repository='repo', site_prefix='site/prefix',
                           config='boop: beep', base_url='/site/prefix')

    def test_jekyll_build_is_called_correctly(self, patch_clone_dir):
        ctx = MockContext()
        ctx.run = Mock()

        conf_path = patch_clone_dir / JEKYLL_CONFIG_YML
        conf_contents = 'hi: test'
        create_file(conf_path, conf_contents)

        tasks.build_jekyll(ctx, branch='branch', owner='owner',
                           repository='repo', site_prefix='site/prefix',
                           config='boop: beep', base_url='/site/prefix')

        assert ctx.run.call_count == 3

        jekyll_build_call_args = ctx.run.call_args_list[2]
        args, kwargs = jekyll_build_call_args

        # Make sure the call to jekyll build is correct
        assert args[0] == 'jekyll build --destination /work/site_repo/_site'

        # Make sure the env is as expected
        assert kwargs['env'] == {'BRANCH': 'branch',
                                 'OWNER': 'owner',
                                 'REPOSITORY': 'repo',
                                 'SITE_PREFIX': 'site/prefix',
                                 'BASEURL': '/site/prefix',
                                 'LANG': 'en_US.UTF-8',
                                 'JEKYLL_ENV': 'production'}

        # Check that the config file has had baseurl, branch, and custom
        # config added
        with conf_path.open() as f:
            assert f.read() == ('hi: test\nbaseurl: /site/prefix\n'
                                'branch: branch\nboop: beep\n')

    def test_gemfile_is_used_if_it_exists(self, monkeypatch, patch_clone_dir):
        monkeypatch.setattr(tasks.build, 'SITE_BUILD_DIR_PATH', '/boop')
        create_file(patch_clone_dir / GEMFILE, '')
        ctx = MockContext(run={
            'gem install bundler --version "<2"': Result(),
            'bundle install': Result(),
            'bundle exec jekyll -v': Result(),
            f'bundle exec jekyll build --destination /boop': Result(),
        })
        tasks.build_jekyll(ctx, branch='branch', owner='owner',
                           repository='repo', site_prefix='site/prefix')


class TestDownloadHugo():
    def test_it_is_callable(self, patch_working_dir, patch_clone_dir):
        create_file(patch_clone_dir / HUGO_VERSION, '0.44')
        tar_cmd = (f'tar -xzf {patch_working_dir}/hugo.tar.gz -C '
                   f'{patch_working_dir}')
        chmod_cmd = f'chmod +x {patch_working_dir}/hugo'
        ctx = MockContext(run={
            tar_cmd: Result(),
            chmod_cmd: Result(),
        })
        with requests_mock.Mocker() as m:
            m.get(
                'https://github.com/gohugoio/hugo/releases/download'
                '/v0.44/hugo_0.44_Linux-64bit.tar.gz', text='fake-data')
            tasks.download_hugo(ctx)


class TestBuildHugo():
    def test_it_calls_hugo_as_expected(self, monkeypatch, patch_working_dir):
        def mock_download(ctx):
            pass

        monkeypatch.setattr(tasks.build, 'download_hugo', mock_download)
        hugo_path = patch_working_dir / HUGO_BIN
        hugo_call = (f'{hugo_path} --source /work/site_repo '
                     f'--destination /work/site_repo/_site')
        ctx = MockContext(run={
            f'{hugo_path} version': Result(),
            hugo_call: Result(),
        })
        with requests_mock.Mocker() as m:
            m.get(
                'https://github.com/gohugoio/hugo/releases/download'
                '/v0.48/hugo_0.48_Linux-64bit.tar.gz')
            kwargs = dict(branch='branch', owner='owner',
                          repository='repo', site_prefix='site/prefix')
            tasks.build_hugo(ctx, **kwargs)

            # and with base_url specified
            kwargs['base_url'] = '/test_base'
            hugo_call += f' --baseUrl /test_base'
            ctx = MockContext(run={
                f'{hugo_path} version': Result(),
                hugo_call: Result(),
            })
            tasks.build_hugo(ctx, **kwargs)


class TestBuildstatic():
    def test_it_moves_files_correctly(self, patch_site_build_dir,
                                      patch_clone_dir):
        ctx = MockContext()
        for i in range(0, 10):
            create_file(patch_clone_dir / f'file_{i}.txt', str(i))

        assert len(os.listdir(patch_clone_dir)) == 10
        assert len(os.listdir(patch_site_build_dir)) == 0

        tasks.build_static(ctx)

        assert len(os.listdir(patch_clone_dir)) == 0
        assert len(os.listdir(patch_site_build_dir)) == 10

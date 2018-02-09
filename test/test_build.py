import requests_mock

from unittest.mock import Mock
from contextlib import ExitStack

from pyfakefs.fake_filesystem_unittest import Patcher
from invoke import MockContext, Result

from tasks import (setup_node, run_federalist_script, setup_ruby,
                   build_jekyll, download_hugo, build_hugo, build_static)

from tasks.build import node_context

# TODO: use pyfakefs to setup PACKAGE_JSON_PATH, NVM_SH_PATH, etc
# so we can test those code paths


class TestSetupNode():
    def test_it_is_callable(self):
        ctx = MockContext(run=[
            Result('node version result'),
            Result('npm version result'),
            Result('npm install result'),
        ])
        setup_node(ctx)


class TestNodeContext():
    def test_default_node_context(self):
        ctx = MockContext()
        context_stack = node_context(ctx)
        assert type(context_stack) == ExitStack
        assert len(context_stack._exit_callbacks) == 1

    def test_node_context_accepts_more_contexts(self):
        ctx = MockContext()
        context_stack = node_context(ctx, ctx.cd('boop'))
        assert type(context_stack) == ExitStack
        assert len(context_stack._exit_callbacks) == 2


class TestRunFederalistScript():
    def test_it_is_callable(self):
        ctx = MockContext()
        run_federalist_script(ctx, branch='branch', owner='owner',
                              repository='repo', site_prefix='site/prefix',
                              base_url='/site/prefix')


class TestSetupRuby():
    def test_it_is_callable(self):
        ctx = MockContext(run=Result('ruby -v result'))
        setup_ruby(ctx)


class TestBuildJekyll():
    def test_it_is_callable(self, fs):
        ctx = MockContext(run=[
            Result('gem install jekyll result'),
            Result('jekyll version result'),
            Result('jekyll build result'),
        ])

        with Patcher() as patcher:
            patcher.fs.CreateFile('/tmp/site_repo/_config.yml',
                                  contents='hi: test')

            build_jekyll(ctx, branch='branch', owner='owner',
                         repository='repo', site_prefix='site/prefix',
                         config='boop: beep', base_url='/site/prefix')

    def test_jekyll_build_is_called_correctly(self, fs):
        ctx = MockContext(run=[
            Result('gem install jekyll result'),
            Result('jekyll version result'),
            Result('jekyll build result'),
        ])

        ctx.run = Mock()

        with Patcher() as patcher:
            patcher.fs.CreateFile('/tmp/site_repo/_config.yml',
                                  contents='hi: test')

            build_jekyll(ctx, branch='branch', owner='owner',
                         repository='repo', site_prefix='site/prefix',
                         config='boop: beep', base_url='/site/prefix')

            assert ctx.run.call_count == 3

            jekyll_build_call_args = ctx.run.call_args_list[2]
            args, kwargs = jekyll_build_call_args

            # Make sure the call to jekyll build is correct
            assert args[0] == 'jekyll build --destination /tmp/site_repo/_site'

            # Make sure the env is as expected
            assert kwargs['env'] == {'BRANCH': 'branch',
                                     'OWNER': 'owner',
                                     'REPOSITORY': 'repo',
                                     'SITE_PREFIX': 'site/prefix',
                                     'BASEURL': '/site/prefix',
                                     'LANG': 'en_US.UTF-8',}


class TestDownloadHugo():
    def test_it_is_callable(self):
        ctx = MockContext(run=[
            Result('tar result'),
            Result('chmod result'),
        ])
        with requests_mock.Mocker() as m:
            m.get(
                'https://github.com/gohugoio/hugo/releases/download'
                '/v0.23/hugo_0.23_Linux-64bit.tar.gz')
            download_hugo(ctx)

    def test_it_accepts_other_versions(self):
        ctx = MockContext(run=[
            Result('tar result'),
            Result('chmod result'),
        ])
        with requests_mock.Mocker() as m:
            m.get(
                'https://github.com/gohugoio/hugo/releases/download'
                '/v0.25/hugo_0.25_Linux-64bit.tar.gz')
            download_hugo(ctx, version='0.25')


class TestBuildHugo():
    def test_it_is_callable(self):
        ctx = MockContext(run=[
            Result('tar result'),
            Result('chmod result'),
            Result('hugo version result'),
            Result('hugo build result'),
        ])
        with requests_mock.Mocker() as m:
            m.get(
                'https://github.com/gohugoio/hugo/releases/download'
                '/v0.23/hugo_0.23_Linux-64bit.tar.gz')
            build_hugo(ctx, branch='branch', owner='owner',
                       repository='repo', site_prefix='site/prefix',
                       base_url='/site/prefix', hugo_version='0.23')


class TestBuildstatic():
    def test_it_is_callable(self):
        ctx = MockContext()
        build_static(ctx)

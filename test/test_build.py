import json
import os
from io import StringIO
from unittest.mock import call, patch
from subprocess import CalledProcessError  # nosec

import pytest
import requests_mock
import requests
import yaml

import steps
from steps import (
    build_hugo, build_jekyll, build_static, download_hugo,
    run_build_script, setup_bundler, setup_node, setup_ruby
)
from steps.build import (
    build_env, is_supported_ruby_version, BUNDLER_VERSION, GEMFILE,
    HUGO_BIN, HUGO_VERSION, JEKYLL_CONFIG_YML,
    NVMRC, PACKAGE_JSON, RUBY_VERSION
)

from .support import create_file, patch_dir


@pytest.fixture
def patch_clone_dir(monkeypatch):
    yield from patch_dir(monkeypatch, steps.build, 'CLONE_DIR_PATH')


@pytest.fixture
def patch_working_dir(monkeypatch):
    yield from patch_dir(monkeypatch, steps.build, 'WORKING_DIR_PATH')


@pytest.fixture
def patch_site_build_dir(monkeypatch):
    yield from patch_dir(monkeypatch, steps.build, 'SITE_BUILD_DIR_PATH')


@pytest.fixture
def patch_ruby_min_version(monkeypatch):
    monkeypatch.setenv('RUBY_VERSION_MIN', '2.6.6')


@patch('steps.build.run')
@patch('steps.build.get_logger')
class TestSetupNode():
    def test_it_uses_nvmrc_file_if_it_exists(self, mock_get_logger, mock_run, patch_clone_dir):
        create_file(patch_clone_dir / NVMRC, contents='6')

        result = setup_node()

        assert result == 0

        mock_get_logger.assert_called_once_with('setup-node')

        mock_logger = mock_get_logger.return_value

        mock_logger.info.assert_called_with(
            'Checking node version specified in .nvmrc'
        )

    def test_installs_deps(self, mock_get_logger, mock_run, patch_clone_dir):
        create_file(patch_clone_dir / PACKAGE_JSON)

        result = setup_node()

        assert result == 0

        mock_get_logger.assert_called_once_with('setup-node')

        mock_logger = mock_get_logger.return_value

        mock_logger.info.assert_has_calls([
            call('Using default node version'),
            call('Installing dependencies in package.json')
        ])

        def callp(cmd):
            return call(mock_logger, cmd, cwd=patch_clone_dir, env={}, check=True, node=True)

        mock_run.assert_has_calls([
            callp('echo Node version: $(node --version)'),
            callp('echo NPM version: $(npm --version)'),
            callp('npm set audit false'),
            callp('npm ci'),
        ])

    def test_returns_code_when_err(self, mock_get_logger, mock_run):
        mock_run.side_effect = CalledProcessError(1, 'command')

        result = setup_node()

        assert result == 1


@patch('steps.build.run')
@patch('steps.build.get_logger')
class TestRunBuildScript():
    def test_it_runs_federalist_script_when_it_exists(self, mock_get_logger, mock_run,
                                                      patch_clone_dir):
        package_json_contents = json.dumps({
            'scripts': {
                'federalist': 'echo federalist',
            },
        })
        create_file(patch_clone_dir / PACKAGE_JSON, package_json_contents)

        kwargs = dict(
            branch='branch',
            owner='owner',
            repository='repo',
            site_prefix='site/prefix',
            base_url='/site/prefix'
        )

        result = run_build_script(**kwargs)

        assert result == mock_run.return_value

        mock_get_logger.assert_called_once_with('run-federalist-script')

        mock_logger = mock_get_logger.return_value

        mock_logger.info.assert_called_with(
            'Running federalist build script in package.json'
        )

        mock_run.assert_called_once_with(
            mock_logger,
            'npm run federalist',
            cwd=patch_clone_dir,
            env=build_env(*kwargs.values()),
            node=True
        )

    def test_it_runs_pages_script_when_it_exists(self, mock_get_logger, mock_run,
                                                 patch_clone_dir):
        package_json_contents = json.dumps({
            'scripts': {
                'pages': 'echo pages',
            },
        })
        create_file(patch_clone_dir / PACKAGE_JSON, package_json_contents)

        kwargs = dict(
            branch='branch',
            owner='owner',
            repository='repo',
            site_prefix='site/prefix',
            base_url='/site/prefix'
        )

        result = run_build_script(**kwargs)

        assert result == mock_run.return_value

        mock_get_logger.assert_called_once_with('run-pages-script')

        mock_logger = mock_get_logger.return_value

        mock_logger.info.assert_called_with(
            'Running pages build script in package.json'
        )

        mock_run.assert_called_once_with(
            mock_logger,
            'npm run pages',
            cwd=patch_clone_dir,
            env=build_env(*kwargs.values()),
            node=True
        )

    def test_it_only_runs_pages_script_when_both_exist(self, mock_get_logger, mock_run,
                                                       patch_clone_dir):
        package_json_contents = json.dumps({
            'scripts': {
                'pages': 'echo pages',
                'federalist': 'echo federalist',
            },
        })
        create_file(patch_clone_dir / PACKAGE_JSON, package_json_contents)

        kwargs = dict(
            branch='branch',
            owner='owner',
            repository='repo',
            site_prefix='site/prefix',
            base_url='/site/prefix'
        )

        result = run_build_script(**kwargs)

        assert result == mock_run.return_value

        mock_get_logger.assert_called_once_with('run-pages-script')

        mock_logger = mock_get_logger.return_value

        mock_logger.info.assert_called_with(
            'Running pages build script in package.json'
        )

        mock_run.assert_called_once_with(
            mock_logger,
            'npm run pages',
            cwd=patch_clone_dir,
            env=build_env(*kwargs.values()),
            node=True
        )

    def test_it_does_not_run_otherwise(self, mock_get_logger, mock_run):
        result = run_build_script('b', 'o', 'r', 'sp')

        assert result == 0

        mock_get_logger.assert_not_called()
        mock_run.assert_not_called()


@patch('steps.build.run')
@patch('steps.build.get_logger')
@patch('steps.build.is_supported_ruby_version')
class TestSetupRuby():
    def test_no_ruby_version_file(self, mock_is_supported_ruby_version,
                                  mock_get_logger, mock_run, patch_clone_dir):

        mock_is_supported_ruby_version.return_value = 1

        result = setup_ruby()

        assert result == mock_run.return_value

        mock_get_logger.assert_called_once_with('setup-ruby')

        mock_logger = mock_get_logger.return_value

        mock_run.assert_called_once_with(
            mock_logger,
            'echo Ruby version: $(ruby -v)',
            cwd=patch_clone_dir,
            env={},
            ruby=True
        )

    def test_it_uses_ruby_version_if_it_exists(self,
                                               mock_is_supported_ruby_version,
                                               mock_get_logger, mock_run,
                                               patch_clone_dir):

        mock_is_supported_ruby_version.return_value = 1

        version = '2.3'

        create_file(patch_clone_dir / RUBY_VERSION, version)

        mock_run.return_value = 0

        result = setup_ruby()

        assert result == 0

        mock_get_logger.assert_called_once_with('setup-ruby')

        mock_logger = mock_get_logger.return_value

        def callp(cmd):
            return call(mock_logger, cmd, cwd=patch_clone_dir, env={}, ruby=True)

        mock_run.assert_has_calls([
            callp(f'rvm install {version}'),
            callp('echo Ruby version: $(ruby -v)')
        ])

    def test_it_strips_and_quotes_ruby_version(self,
                                               mock_is_supported_ruby_version,
                                               mock_get_logger, mock_run,
                                               patch_clone_dir):

        mock_is_supported_ruby_version.return_value = 1

        version = '  $2.3  '

        create_file(patch_clone_dir / RUBY_VERSION, version)

        mock_run.return_value = 0

        result = setup_ruby()

        assert result == 0

        mock_get_logger.assert_called_once_with('setup-ruby')

        mock_logger = mock_get_logger.return_value

        def callp(cmd):
            return call(mock_logger, cmd, cwd=patch_clone_dir, env={}, ruby=True)

        mock_logger.info.assert_has_calls([
            call('Using ruby version in .ruby-version'),
        ])

        mock_run.assert_has_calls([
            callp("rvm install '$2.3'"),
            callp('echo Ruby version: $(ruby -v)'),
        ])

    def test_it_returns_error_code_when_rvm_install_fails(self,
                                                          mock_is_supported_ruby_version,
                                                          mock_get_logger, mock_run,
                                                          patch_clone_dir):

        mock_is_supported_ruby_version.return_value = 1

        version = '2.3'

        mock_run.return_value = 1

        create_file(patch_clone_dir / RUBY_VERSION, version)

        result = setup_ruby()

        assert result == 1

        mock_get_logger.assert_called_once_with('setup-ruby')

        mock_logger = mock_get_logger.return_value

        mock_logger.info.assert_has_calls([
            call('Using ruby version in .ruby-version'),
        ])

        mock_run.assert_called_once_with(
            mock_logger, 'rvm install 2.3', cwd=patch_clone_dir, env={}, ruby=True
        )

    def test_it_outputs_warning_if_eol_approaching(self,
                                                   mock_is_supported_ruby_version,
                                                   mock_get_logger, mock_run,
                                                   patch_ruby_min_version):

        min_ruby_version = os.getenv('RUBY_VERSION_MIN')

        mock_run.return_value = 1

        result = is_supported_ruby_version(min_ruby_version)

        assert result == 1

        mock_logger = mock_get_logger.return_value

        mock_logger.warning.assert_has_calls([
            call(
                f'WARNING: Ruby {min_ruby_version} will soon reach end-of-life, at which point Federalist will no longer support it.'),  # noqa: E501
            call('Please upgrade to an actively supported version, see https://www.ruby-lang.org/en/downloads/branches/ for details.')  # noqa: E501
        ])

    def test_it_outputs_warning_if_not_supported(self,
                                                 mock_is_supported_ruby_version,
                                                 mock_get_logger, mock_run):
        version = '2.3'

        mock_run.return_value = 0

        result = is_supported_ruby_version(version)

        assert result == 0

        mock_logger = mock_get_logger.return_value

        mock_logger.error.assert_has_calls([
            call('ERROR: Unsupported ruby version specified in .ruby-version.'),
            call('Please upgrade to an actively supported version, see https://www.ruby-lang.org/en/downloads/branches/ for details.')  # noqa: E501
        ])


@patch('steps.build.run')
@patch('steps.build.get_logger')
class TestSetupBundler():
    def test_when_no_gemfile_just_load_jekyll(self, mock_get_logger, mock_run, patch_clone_dir):
        result = setup_bundler()

        assert result == mock_run.return_value

        mock_get_logger.assert_called_once_with('setup-bundler')

        mock_logger = mock_get_logger.return_value

        mock_logger.info.assert_has_calls([
            call('No Gemfile found, installing Jekyll.')
        ])

        mock_run.assert_called_once_with(
            mock_logger, 'gem install jekyll --no-document', cwd=patch_clone_dir, env={}, ruby=True
        )

    def test_it_uses_default_version_if_only_gemfile_exits(self, mock_get_logger,
                                                           mock_run, patch_clone_dir):
        default_version = '<2'
        create_file(patch_clone_dir / GEMFILE, 'foo')

        mock_run.return_value = 0

        result = setup_bundler()

        assert result == 0

        mock_get_logger.assert_called_once_with('setup-bundler')

        mock_logger = mock_get_logger.return_value

        mock_logger.info.assert_has_calls([
            call('Gemfile found, setting up bundler'),
            call('Installing dependencies in Gemfile'),
        ])

        def callp(cmd):
            return call(mock_logger, cmd, cwd=patch_clone_dir, env={}, ruby=True)

        mock_run.assert_has_calls([
            callp(f'gem install bundler --version "{default_version}"'),
            callp('bundle install'),
        ])

    def test_it_uses_bundler_version_if_gemfile_and_bundler_file_exists(self, mock_get_logger,
                                                                        mock_run, patch_clone_dir):
        version = '2.0.1'

        create_file(patch_clone_dir / GEMFILE, 'foo')
        create_file(patch_clone_dir / BUNDLER_VERSION, version)

        mock_run.return_value = 0

        result = setup_bundler()

        assert result == 0

        mock_get_logger.assert_called_once_with('setup-bundler')

        mock_logger = mock_get_logger.return_value

        mock_logger.info.assert_has_calls([
            call('Gemfile found, setting up bundler'),
            call('Using bundler version in .bundler-version'),
            call('Installing dependencies in Gemfile'),
        ])

        def callp(cmd):
            return call(mock_logger, cmd, cwd=patch_clone_dir, env={}, ruby=True)

        mock_run.assert_has_calls([
            callp(f'gem install bundler --version "{version}"'),
            callp('bundle install'),
        ])


@patch('steps.build.run')
@patch('steps.build.get_logger')
class TestBuildJekyll():
    def test_with_no_gemfile(self, mock_get_logger, mock_run, patch_clone_dir,
                             patch_site_build_dir):
        command = 'jekyll'

        create_file(patch_clone_dir / JEKYLL_CONFIG_YML, 'hi: test')

        kwargs = dict(
            branch='branch', owner='owner',
            repository='repo', site_prefix='site/prefix',
            base_url='/site/prefix', config=json.dumps(dict(boop='beep'))
        )

        result = build_jekyll(**kwargs)

        assert result == mock_run.return_value

        mock_get_logger.assert_has_calls([call('build-jekyll'), call('build-jekyll')])

        mock_logger = mock_get_logger.return_value

        env = build_env(
            kwargs['branch'], kwargs['owner'], kwargs['repository'],
            kwargs['site_prefix'], kwargs['base_url']
        )
        env['JEKYLL_ENV'] = 'production'

        mock_run.assert_has_calls([
            call(
                mock_logger,
                f'echo Building using Jekyll version: $({command} -v)',
                cwd=patch_clone_dir,
                env={},
                check=True,
                ruby=True,
            ),
            call(
                mock_logger,
                f'{command} build --destination {patch_site_build_dir}',
                cwd=patch_clone_dir,
                env=env,
                node=True,
                ruby=True,
            )
        ])

    def test_with_gemfile(self, mock_get_logger, mock_run, patch_clone_dir, patch_site_build_dir):
        command = 'bundle exec jekyll'

        create_file(patch_clone_dir / GEMFILE, 'foo')
        create_file(patch_clone_dir / JEKYLL_CONFIG_YML, 'hi: test')

        kwargs = dict(
            branch='branch', owner='owner',
            repository='repo', site_prefix='site/prefix',
            base_url='/site/prefix', config=json.dumps(dict(boop='beep'))
        )

        result = build_jekyll(**kwargs)

        assert result == mock_run.return_value

        mock_get_logger.assert_has_calls([call('build-jekyll'), call('build-jekyll')])

        mock_logger = mock_get_logger.return_value

        env = build_env(
            kwargs['branch'], kwargs['owner'], kwargs['repository'],
            kwargs['site_prefix'], kwargs['base_url']
        )
        env['JEKYLL_ENV'] = 'production'

        mock_run.assert_has_calls([
            call(
                mock_logger,
                f'echo Building using Jekyll version: $({command} -v)',
                cwd=patch_clone_dir,
                env={},
                check=True,
                ruby=True,
            ),
            call(
                mock_logger,
                f'{command} build --destination {patch_site_build_dir}',
                cwd=patch_clone_dir,
                env=env,
                node=True,
                ruby=True,
            )
        ])

    def test_config_file_is_updated(self, mock_get_logger, mock_run, patch_clone_dir,
                                    patch_site_build_dir):
        conf_path = patch_clone_dir / JEKYLL_CONFIG_YML
        create_file(conf_path, 'hi: test')

        kwargs = dict(
            branch='branch', owner='owner',
            repository='repo', site_prefix='site/prefix',
            config=json.dumps(dict(boop='beep')), base_url='/site/prefix'
        )

        build_jekyll(**kwargs)

        with conf_path.open() as f:
            config = yaml.safe_load(f)
            assert config['hi'] == 'test'
            assert config['baseurl'] == kwargs['base_url']
            assert config['branch'] == kwargs['branch']


@patch('steps.build.run')
@patch('steps.build.get_logger')
class TestDownloadHugo():
    def test_it_is_callable(self, mock_get_logger, mock_run, patch_working_dir, patch_clone_dir):
        version = '0.44'
        tar_cmd = f'tar -xzf {patch_working_dir}/hugo.tar.gz -C {patch_working_dir}'
        chmod_cmd = f'chmod +x {patch_working_dir}/hugo'
        dl_url = (
            'https://github.com/gohugoio/hugo/releases/download/v'
            f'{version}/hugo_{version}_Linux-64bit.tar.gz'
        )

        create_file(patch_clone_dir / HUGO_VERSION, version)

        with requests_mock.Mocker() as m:
            m.get(dl_url, text='fake-data')
            result = download_hugo()

        assert result == 0

        mock_get_logger.assert_called_once_with('download-hugo')

        mock_logger = mock_get_logger.return_value

        mock_logger.info.assert_has_calls([
            call('.hugo-version found'),
            call(f'Using hugo version in .hugo-version: {version}'),
            call(f'Downloading hugo version {version}')
        ])

        mock_run.assert_has_calls([
            call(mock_logger, tar_cmd, env={}, check=True),
            call(mock_logger, chmod_cmd, env={}, check=True)
        ])

    def test_it_is_callable_retry(self, mock_get_logger, mock_run, patch_working_dir,
                                  patch_clone_dir):
        version = '0.44'
        tar_cmd = f'tar -xzf {patch_working_dir}/hugo.tar.gz -C {patch_working_dir}'
        chmod_cmd = f'chmod +x {patch_working_dir}/hugo'
        dl_url = (
            'https://github.com/gohugoio/hugo/releases/download/v'
            f'{version}/hugo_{version}_Linux-64bit.tar.gz'
        )

        create_file(patch_clone_dir / HUGO_VERSION, version)

        with requests_mock.Mocker() as m:
            m.get(dl_url, [
                dict(exc=requests.exceptions.ConnectTimeout),
                dict(exc=requests.exceptions.ConnectTimeout),
                dict(exc=requests.exceptions.ConnectTimeout),
                dict(exc=requests.exceptions.ConnectTimeout),
                dict(text='fake-data')
            ])

            result = download_hugo()

        assert result == 0

        mock_get_logger.assert_called_once_with('download-hugo')

        mock_logger = mock_get_logger.return_value

        mock_logger.info.assert_has_calls([
            call('.hugo-version found'),
            call(f'Using hugo version in .hugo-version: {version}'),
            call(f'Downloading hugo version {version}'),
            call(f'Failed attempt #1 to download hugo version: {version}'),
            call(f'Failed attempt #2 to download hugo version: {version}'),
            call(f'Failed attempt #3 to download hugo version: {version}'),
            call(f'Failed attempt #4 to download hugo version: {version}'),
        ])

        mock_run.assert_has_calls([
            call(mock_logger, tar_cmd, env={}, check=True),
            call(mock_logger, chmod_cmd, env={}, check=True)
        ])

    def test_it_is_exception(self, mock_get_logger, mock_run, patch_working_dir, patch_clone_dir):
        version = '0.44'
        dl_url = (
            'https://github.com/gohugoio/hugo/releases/download/v'
            f'{version}/hugo_{version}_Linux-64bit.tar.gz'
        )

        create_file(patch_clone_dir / HUGO_VERSION, version)

        with pytest.raises(Exception):
            with requests_mock.Mocker() as m:
                m.get(dl_url, [
                    dict(exc=requests.exceptions.ConnectTimeout),
                    dict(exc=requests.exceptions.ConnectTimeout),
                    dict(exc=requests.exceptions.ConnectTimeout),
                    dict(exc=requests.exceptions.ConnectTimeout),
                    dict(exc=requests.exceptions.ConnectTimeout),
                ])

                download_hugo()

        mock_get_logger.assert_called_once_with('download-hugo')

        mock_logger = mock_get_logger.return_value

        mock_logger.info.assert_has_calls([
            call('.hugo-version found'),
            call(f'Using hugo version in .hugo-version: {version}'),
            call(f'Downloading hugo version {version}'),
            call(f'Failed attempt #1 to download hugo version: {version}'),
            call(f'Failed attempt #2 to download hugo version: {version}'),
            call(f'Failed attempt #3 to download hugo version: {version}'),
            call(f'Failed attempt #4 to download hugo version: {version}'),
            call(f'Failed attempt #5 to download hugo version: {version}'),
        ])

        mock_run.assert_not_called()


@patch('steps.build.run')
@patch('steps.build.get_logger')
class TestBuildHugo():
    def test_it_calls_hugo_as_expected(self, mock_get_logger, mock_run,
                                       patch_working_dir, patch_clone_dir,
                                       patch_site_build_dir):

        hugo_path = patch_working_dir / HUGO_BIN
        hugo_call = (
            f'{hugo_path} --source {patch_clone_dir} '
            f'--destination {patch_site_build_dir} '
            '--baseURL /site/prefix'
        )

        kwargs = dict(
            branch='branch',
            owner='owner',
            repository='repo',
            site_prefix='site/prefix',
            base_url='/site/prefix'
        )

        result = build_hugo(**kwargs)

        assert result == mock_run.return_value

        mock_get_logger.assert_called_once_with('build-hugo')

        mock_logger = mock_get_logger.return_value

        mock_logger.info.assert_called_with(
            'Building site with hugo'
        )

        mock_run.assert_has_calls([
            call(
                mock_logger,
                f'echo hugo version: $({hugo_path} version)',
                env={},
                check=True
            ),
            call(
                mock_logger,
                hugo_call,
                cwd=patch_clone_dir,
                env=build_env(*kwargs.values()),
                node=True
            )
        ])


class TestBuildstatic():
    def test_it_moves_files_correctly(self, patch_site_build_dir, patch_clone_dir):
        for i in range(0, 10):
            create_file(patch_clone_dir / f'file_{i}.txt', str(i))

        assert len(os.listdir(patch_clone_dir)) == 10
        assert len(os.listdir(patch_site_build_dir)) == 0

        build_static()

        assert len(os.listdir(patch_clone_dir)) == 0
        assert len(os.listdir(patch_site_build_dir)) == 10


class TestBuildEnv():
    def test_it_includes_default_values(self):
        branch = 'branch'
        owner = 'owner'
        repository = 'repo'
        site_prefix = 'prefix'
        base_url = 'url'

        result = build_env(branch, owner, repository, site_prefix, base_url)

        assert result == {
            'BRANCH': branch,
            'OWNER': owner,
            'REPOSITORY': repository,
            'SITE_PREFIX': site_prefix,
            'BASEURL': base_url,
            'LANG': 'en_US.UTF-8',
            'GATSBY_TELEMETRY_DISABLED': '1',
            'HOME': '/home/customer',
        }

    def test_it_includes_user_env_vars(self):
        branch = 'branch'
        owner = 'owner'
        repository = 'repo'
        site_prefix = 'prefix'
        base_url = 'url'
        user_env_vars = [
            {'name': 'FOO', 'value': 'bar'}
        ]

        result = build_env(branch, owner, repository, site_prefix,
                           base_url, user_env_vars)

        assert result['FOO'] == 'bar'

    @patch('sys.stdout', new_callable=StringIO)
    def test_it_ignores_and_warns_duplicate_user_env_vars(self, mock_stdout):
        # and it is case insensitive
        branch = 'branch'
        owner = 'owner'
        repository = 'repo'
        site_prefix = 'prefix'
        base_url = 'url'
        user_env_vars = [
            {'name': 'BASEURL', 'value': 'bar'},
            {'name': 'repository', 'value': 'baz'}
        ]

        result = build_env(branch, owner, repository, site_prefix,
                           base_url, user_env_vars)

        assert result['BASEURL'] == base_url
        assert result['REPOSITORY'] == repository
        assert ('user environment variable name `BASEURL` conflicts'
                ' with system environment variable, it will be ignored.'
                ) in mock_stdout.getvalue()
        assert ('user environment variable name `repository`'
                ' conflicts with system environment variable, it will be'
                ' ignored.') in mock_stdout.getvalue()

import json
import os
import shutil
from os import path
from pathlib import Path
import re
import requests
import shlex
from subprocess import CalledProcessError  # nosec
import time
import yaml

from common import (CLONE_DIR_PATH, SITE_BUILD_DIR, SITE_BUILD_DIR_PATH, WORKING_DIR_PATH)
from log_utils import get_logger
from runner import run

HUGO_BIN = 'hugo'
HUGO_VERSION = '.hugo-version'
NVMRC = '.nvmrc'
PACKAGE_JSON = 'package.json'
RUBY_VERSION = '.ruby-version'
GEMFILE = 'Gemfile'
JEKYLL_CONFIG_YML = '_config.yml'
BUNDLER_VERSION = '.bundler-version'

CERTS_PATH = Path('/etc/ssl/certs/ca-certificates.crt')
RVM_PATH = Path('/usr/local/rvm/scripts/rvm')


def build_env(branch, owner, repository, site_prefix, base_url,
              user_env_vars=[]):
    '''Creats a dict of environment variables to pass into a build context'''
    env = {
        'BRANCH': branch,
        'OWNER': owner,
        'REPOSITORY': repository,
        'SITE_PREFIX': site_prefix,
        'BASEURL': base_url,
        # necessary to make sure build engines use utf-8 encoding
        'LANG': 'en_US.UTF-8',
        'GATSBY_TELEMETRY_DISABLED': '1',
    }

    for uev in user_env_vars:
        name = uev['name']
        value = uev['value']
        if name in env or name.upper() in env:
            print(
                f'user environment variable name `{name}` conflicts '
                'with system environment variable, it will be ignored.'
            )
        else:
            env[name] = value

    return env


def build_static():
    '''Moves all files from CLONE_DIR into SITE_BUILD_DIR'''
    logger = get_logger('build-static')

    dir = path.join(CLONE_DIR_PATH, '.git')
    logger.info(f'Cleaning {dir}')
    shutil.rmtree(dir, ignore_errors=True)

    logger.info(f'Moving files to {SITE_BUILD_DIR}')

    # Make the site build directory first
    SITE_BUILD_DIR_PATH.mkdir(exist_ok=True)

    files = os.listdir(CLONE_DIR_PATH)

    for file in files:
        # don't move the SITE_BUILD_DIR dir into itself
        if file is not SITE_BUILD_DIR:
            shutil.move(str(CLONE_DIR_PATH / file),
                        str(SITE_BUILD_DIR_PATH))


def has_federalist_script():
    '''
    Checks for existence of the "federalist" script in the
    cloned repo's package.json.
    '''
    PACKAGE_JSON_PATH = CLONE_DIR_PATH / PACKAGE_JSON
    if PACKAGE_JSON_PATH.is_file():
        with PACKAGE_JSON_PATH.open() as json_file:
            package_json = json.load(json_file)
            return 'federalist' in package_json.get('scripts', {})

    return False


def setup_node():
    '''
    Sets up node and installs production dependencies.

    Uses the node version specified in the cloned repo's .nvmrc
    file if it is present.
    '''
    logger = get_logger('setup-node')

    def runp(cmd):
        return run(logger, cmd, cwd=CLONE_DIR_PATH, env={}, check=True, node=True)

    try:
        NVMRC_PATH = CLONE_DIR_PATH / NVMRC
        if NVMRC_PATH.is_file():
            # nvm will output the node and npm versions used
            logger.info('Checking node version specified in .nvmrc')
            runp("""
                RAW_VERSION=$(nvm version-remote $(cat .nvmrc))
                MAJOR_VERSION=$(echo $RAW_VERSION | cut -d. -f 1 | cut -dv -f 2)
                if [[ "$MAJOR_VERSION" =~ ^(10|12|14)$ ]]; then
                    echo "Switching to node version $RAW_VERSION specified in .nvmrc"
                    nvm install $RAW_VERSION
                    nvm alias default $RAW_VERSION
                else
                    echo "Unsupported node major version '$MAJOR_VERSION' specified in .nvmrc."
                    echo "Please upgrade to LTS major version 12 or 14, see https://nodejs.org/en/about/releases/ for details."
                    exit 1
                fi
            """)  # noqa: E501
        else:
            # output node and npm versions if the defaults are used
            logger.info('Using default node version')
            runp('nvm alias default $(nvm version)')
            runp('echo Node version: $(node --version)')
            runp('echo NPM version: $(npm --version)')

        PACKAGE_JSON_PATH = CLONE_DIR_PATH / PACKAGE_JSON
        if PACKAGE_JSON_PATH.is_file():
            logger.info('Installing production dependencies in package.json')
            runp('npm set audit false')
            runp('npm ci')

    except (CalledProcessError, OSError, ValueError):
        return 1

    return 0


def run_federalist_script(branch, owner, repository, site_prefix,
                          base_url='', user_env_vars=[]):
    '''
    Runs the npm "federalist" script if it is defined
    '''

    if has_federalist_script():
        logger = get_logger('run-federalist-script')
        logger.info('Running federalist build script in package.json')
        env = build_env(branch, owner, repository, site_prefix, base_url, user_env_vars)
        return run(logger, 'npm run federalist', cwd=CLONE_DIR_PATH, env=env, node=True)

    return 0


def download_hugo():
    logger = get_logger('download-hugo')

    HUGO_VERSION_PATH = CLONE_DIR_PATH / HUGO_VERSION
    if HUGO_VERSION_PATH.is_file():
        logger.info('.hugo-version found')
        hugo_version = ''
        with HUGO_VERSION_PATH.open() as hugo_vers_file:
            try:
                hugo_version = hugo_vers_file.readline().strip()
                hugo_version = shlex.quote(hugo_version)
                regex = r'^(extended_)?[\d]+(\.[\d]+)*$'
                hugo_version = re.search(regex, hugo_version).group(0)
            except Exception:
                raise RuntimeError('Invalid .hugo-version')

        if hugo_version:
            logger.info(f'Using hugo version in .hugo-version: {hugo_version}')
    else:
        raise RuntimeError(".hugo-version not found")
    '''
    Downloads the specified version of Hugo
    '''
    logger.info(f'Downloading hugo version {hugo_version}')
    failed_attempts = 0
    while (failed_attempts < 5):
        try:
            dl_url = ('https://github.com/gohugoio/hugo/releases/download/v'
                      + hugo_version.split('_')[-1] +
                      f'/hugo_{hugo_version}_Linux-64bit.tar.gz')
            response = requests.get(dl_url, verify=CERTS_PATH)

            hugo_tar_path = WORKING_DIR_PATH / 'hugo.tar.gz'
            with hugo_tar_path.open('wb') as hugo_tar:
                for chunk in response.iter_content(chunk_size=128):
                    hugo_tar.write(chunk)

            HUGO_BIN_PATH = WORKING_DIR_PATH / HUGO_BIN
            run(logger, f'tar -xzf {hugo_tar_path} -C {WORKING_DIR_PATH}', env={}, check=True)
            run(logger, f'chmod +x {HUGO_BIN_PATH}', env={}, check=True)
            return 0
        except Exception:
            failed_attempts += 1
            logger.info(
                f'Failed attempt #{failed_attempts} to download hugo version: {hugo_version}'
            )
            if failed_attempts == 5:
                raise RuntimeError(f'Unable to download hugo version: {hugo_version}')
            time.sleep(2)  # try again in 2 seconds


def build_hugo(branch, owner, repository, site_prefix,
               base_url='', user_env_vars=[]):
    '''
    Builds the cloned site with Hugo
    '''
    logger = get_logger('build-hugo')

    HUGO_BIN_PATH = WORKING_DIR_PATH / HUGO_BIN

    run(logger, f'echo hugo version: $({HUGO_BIN_PATH} version)', env={}, check=True)

    logger.info('Building site with hugo')

    hugo_args = f'--source {CLONE_DIR_PATH} --destination {SITE_BUILD_DIR_PATH}'
    if base_url:
        hugo_args += f' --baseURL {base_url}'

    env = build_env(branch, owner, repository, site_prefix, base_url, user_env_vars)
    return run(logger, f'{HUGO_BIN_PATH} {hugo_args}', cwd=CLONE_DIR_PATH, env=env, node=True)


def setup_ruby():
    '''
    Sets up RVM and installs ruby
    Uses the ruby version specified in .ruby-version if present
    '''
    logger = get_logger('setup-ruby')

    def runp(cmd):
        return run(logger, cmd, cwd=CLONE_DIR_PATH, env={}, ruby=True)

    returncode = 0

    RUBY_VERSION_PATH = CLONE_DIR_PATH / RUBY_VERSION
    if RUBY_VERSION_PATH.is_file():
        ruby_version = ''
        with RUBY_VERSION_PATH.open() as ruby_vers_file:
            ruby_version = ruby_vers_file.readline().strip()
            # escape-quote the value in case there's anything weird
            # in the .ruby-version file
            ruby_version = shlex.quote(ruby_version)
        if ruby_version:
            logger.info('Using ruby version in .ruby-version')
            returncode = runp(f'rvm install {ruby_version}')

    if returncode:
        return returncode

    return runp('echo Ruby version: $(ruby -v)')


def setup_bundler():
    logger = get_logger('setup-bundler')

    def runp(cmd):
        return run(logger, cmd, cwd=CLONE_DIR_PATH, env={}, ruby=True)

    GEMFILE_PATH = CLONE_DIR_PATH / GEMFILE

    if not GEMFILE_PATH.is_file():
        logger.info('No Gemfile found, installing Jekyll.')
        return runp('gem install jekyll --no-document')

    logger.info('Gemfile found, setting up bundler')

    version = '<2'

    BUNDLER_VERSION_PATH = CLONE_DIR_PATH / BUNDLER_VERSION

    if BUNDLER_VERSION_PATH.is_file():
        with BUNDLER_VERSION_PATH.open() as bundler_vers_file:
            try:
                bundler_vers = bundler_vers_file.readline().strip()
                # escape-quote the value in case there's anything weird
                # in the .bundler-version file
                bundler_vers = shlex.quote(bundler_vers)
                regex = r'^[\d]+(\.[\d]+)*$'
                bundler_vers = re.search(regex, bundler_vers).group(0)
                if bundler_vers:
                    logger.info('Using bundler version in .bundler-version')
                    version = bundler_vers
            except Exception:
                raise RuntimeError('Invalid .bundler-version')

    returncode = runp(f'gem install bundler --version "{version}"')

    if returncode:
        return returncode

    logger.info('Installing dependencies in Gemfile')
    return runp('bundle install')


def update_jekyll_config(federalist_config={}, custom_config_path=''):
    logger = get_logger('build-jekyll')

    JEKYLL_CONF_YML_PATH = CLONE_DIR_PATH / JEKYLL_CONFIG_YML

    config_yml = {}
    with JEKYLL_CONF_YML_PATH.open('r') as jekyll_conf_file:
        config_yml = yaml.safe_load(jekyll_conf_file)

    custom_config = {}
    if custom_config_path:
        try:
            custom_config = json.loads(custom_config_path)
        except json.JSONDecodeError:
            logger.error('Could not load/parse custom yaml config.')
            return 1

    config_yml = {**config_yml, **custom_config, **federalist_config}

    with JEKYLL_CONF_YML_PATH.open('w') as jekyll_conf_file:
        yaml.dump(config_yml, jekyll_conf_file, default_flow_style=False)

    return 0


def build_jekyll(branch, owner, repository, site_prefix,
                 base_url='', config='', user_env_vars=[]):
    '''
    Builds the cloned site with Jekyll
    '''
    logger = get_logger('build-jekyll')

    result = update_jekyll_config(
        dict(baseurl=base_url, branch=branch),
        config
    )

    if result != 0:
        return result

    jekyll_cmd = 'jekyll'

    GEMFILE_PATH = CLONE_DIR_PATH / GEMFILE
    if GEMFILE_PATH.is_file():
        jekyll_cmd = f'bundle exec {jekyll_cmd}'

    run(
        logger,
        f'echo Building using Jekyll version: $({jekyll_cmd} -v)',
        cwd=CLONE_DIR_PATH,
        env={},
        check=True,
        ruby=True
    )

    env = build_env(branch, owner, repository, site_prefix, base_url, user_env_vars)
    env['JEKYLL_ENV'] = 'production'

    return run(
        logger,
        f'{jekyll_cmd} build --destination {SITE_BUILD_DIR_PATH}',
        cwd=CLONE_DIR_PATH,
        env=env,
        node=True,
        ruby=True
    )

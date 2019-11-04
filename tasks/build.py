'''
Build tasks and helpers
'''

import json
import os
import shlex
import shutil
import re
from contextlib import ExitStack
from os import path
from pathlib import Path

import requests
from invoke import call, task

from log_utils import get_logger
from tasks.common import (CLONE_DIR_PATH, SITE_BUILD_DIR, SITE_BUILD_DIR_PATH,
                          WORKING_DIR_PATH, clean)

LOGGER = get_logger('BUILD')

NVM_SH_PATH = Path('/usr/local/nvm/nvm.sh')
RVM_PATH = Path('/usr/local/rvm/scripts/rvm')
CERTS_PATH = Path('/etc/ssl/certs/ca-certificates.crt')

HUGO_BIN = 'hugo'
NVMRC = '.nvmrc'
PACKAGE_JSON = 'package.json'
RUBY_VERSION = '.ruby-version'
GEMFILE = 'Gemfile'
JEKYLL_CONFIG_YML = '_config.yml'
HUGO_VERSION = '.hugo-version'
BUNDLER_VERSION = '.bundler-version'


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


@task
def setup_node(ctx):
    '''
    Sets up node and installs production dependencies.

    Uses the node version specified in the cloned repo's .nvmrc
    file if it is present.
    '''
    with ctx.cd(str(CLONE_DIR_PATH)):
        with ctx.prefix(f'source {NVM_SH_PATH}'):
            npm_command = 'npm'

            NVMRC_PATH = CLONE_DIR_PATH / NVMRC

            if NVMRC_PATH.is_file():
                # nvm will output the node and npm versions used
                LOGGER.info('Using node version specified in .nvmrc')
                ctx.run('nvm install')
                npm_command = f'nvm use && {npm_command}'
            else:
                # output node and npm versions if the defaults are used
                node_version_res = ctx.run(f'node --version', hide=True)
                LOGGER.info(f'Node version: {node_version_res.stdout}')
                npm_version_res = ctx.run(f'{npm_command} --version',
                                          hide=True)
                LOGGER.info(f'NPM version: {npm_version_res.stdout}')

            PACKAGE_JSON_PATH = CLONE_DIR_PATH / PACKAGE_JSON
            if PACKAGE_JSON_PATH.is_file():
                LOGGER.info('Installing production dependencies '
                            'in package.json')
                ctx.run(f'{npm_command} install --production')


def node_context(ctx, *more_contexts):
    '''
    Creates an ExitStack context manager that includes the
    pyinvoke ctx with nvm prefixes.

    Additionally supplied more_contexts (like `ctx.cd(...)`) will be
    included in the returned ExitStack.
    '''
    contexts = [
        ctx.prefix(f'source {NVM_SH_PATH}'),
    ]

    # Only use `nvm use` if `.nvmrc` exists.
    # The default node version will be used if `.nvmrc` is not present.
    NVMRC_PATH = CLONE_DIR_PATH / NVMRC
    if NVMRC_PATH.is_file():
        contexts.append(ctx.prefix('nvm use'))

    contexts += more_contexts
    stack = ExitStack()
    for context in contexts:
        stack.enter_context(context)
    return stack


def build_env(branch, owner, repository, site_prefix, base_url):
    '''Creats a dict of environment variables to pass into a build context'''
    return {
        'BRANCH': branch,
        'OWNER': owner,
        'REPOSITORY': repository,
        'SITE_PREFIX': site_prefix,
        'BASEURL': base_url,
        # necessary to make sure build engines use utf-8 encoding
        'LANG': 'en_US.UTF-8',
    }


@task(pre=[setup_node])
def run_federalist_script(ctx, branch, owner, repository, site_prefix,
                          base_url=''):
    '''
    Runs the npm "federalist" script if it is defined
    '''
    if has_federalist_script():
        with node_context(ctx, ctx.cd(str(CLONE_DIR_PATH))):
            LOGGER.info('Running federalist build script in package.json')
            ctx.run('npm run federalist',
                    env=build_env(branch, owner, repository, site_prefix,
                                  base_url))


@task
def setup_ruby(ctx):
    '''
    Sets up RVM and installs ruby
    Uses the ruby version specified in .ruby-version if present
    '''
    with ctx.prefix(f'source {RVM_PATH}'):
        RUBY_VERSION_PATH = CLONE_DIR_PATH / RUBY_VERSION
        if RUBY_VERSION_PATH.is_file():
            ruby_version = ''
            with RUBY_VERSION_PATH.open() as ruby_vers_file:
                ruby_version = ruby_vers_file.readline().strip()
                # escape-quote the value in case there's anything weird
                # in the .ruby-version file
                ruby_version = shlex.quote(ruby_version)
            if ruby_version:
                LOGGER.info('Using ruby version in .ruby-version')
                ctx.run(f'rvm install {ruby_version}')

        ruby_ver_res = ctx.run('ruby -v')
        LOGGER.info(f'Ruby version: {ruby_ver_res.stdout}')


@task
def setup_bundler(ctx):
    LOGGER.info('Setting up bundler')
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
                    LOGGER.info('Using bundler version in .bundler-version')
                    ctx.run(f'gem install bundler --version "{bundler_vers}"')
            except Exception:
                raise RuntimeError(f'Invalid .bundler-version')
    else:
        ctx.run('gem install bundler --version "<2"')


@task(pre=[setup_ruby])
def build_jekyll(ctx, branch, owner, repository, site_prefix,
                 config='', base_url=''):
    '''
    Builds the cloned site with Jekyll
    '''
    JEKYLL_CONF_YML_PATH = CLONE_DIR_PATH / JEKYLL_CONFIG_YML

    # Add baseurl, branch, and the custom config to _config.yml.
    # Use the 'a' option to create or append to an existing config file.
    with JEKYLL_CONF_YML_PATH.open('a') as jekyll_conf_file:
        jekyll_conf_file.writelines([
            '\n'
            f'baseurl: {base_url}\n',
            f'branch: {branch}\n',
            config,
            '\n',
        ])

    source_rvm = ctx.prefix(f'source {RVM_PATH}')
    with node_context(ctx, source_rvm, ctx.cd(str(CLONE_DIR_PATH))):
        jekyll_cmd = 'jekyll'

        GEMFILE_PATH = CLONE_DIR_PATH / GEMFILE
        if GEMFILE_PATH.is_file():
            setup_bundler(ctx)
            LOGGER.info('Installing dependencies in Gemfile')
            ctx.run('bundle install')
            jekyll_cmd = 'bundle exec ' + jekyll_cmd

        else:
            LOGGER.info('Installing Jekyll')
            ctx.run('gem install jekyll --no-document')

        jekyll_vers_res = ctx.run(f'{jekyll_cmd} -v')
        LOGGER.info(f'Building using Jekyll version: {jekyll_vers_res.stdout}')

        jekyll_build_env = build_env(branch, owner, repository, site_prefix,
                                     base_url)
        # Use JEKYLL_ENV to tell jekyll to run in production mode
        jekyll_build_env['JEKYLL_ENV'] = 'production'

        ctx.run(
            f'{jekyll_cmd} build --destination {SITE_BUILD_DIR_PATH}',
            env=jekyll_build_env
        )


@task
def download_hugo(ctx):
    HUGO_VERSION_PATH = CLONE_DIR_PATH / HUGO_VERSION
    if HUGO_VERSION_PATH.is_file():
        LOGGER.info(f'.hugo-version found')
        hugo_version = ''
        with HUGO_VERSION_PATH.open() as hugo_vers_file:
            try:
                hugo_version = hugo_vers_file.readline().strip()
                hugo_version = shlex.quote(hugo_version)
                regex = r'^(extended_)?[\d]+(\.[\d]+)*$'
                hugo_version = re.search(regex, hugo_version).group(0)
            except Exception:
                raise RuntimeError(f'Invalid .hugo-version')

        if hugo_version:
            LOGGER.info(f'Using hugo version in .hugo-version: {hugo_version}')
    else:
        raise RuntimeError(".hugo-version not found")
    '''
    Downloads the specified version of Hugo
    '''
    LOGGER.info(f'Downloading hugo version {hugo_version}')
    try:
        dl_url = (f'https://github.com/gohugoio/hugo/releases/download/v'
                  + hugo_version.split('_')[-1] +
                  f'/hugo_{hugo_version}_Linux-64bit.tar.gz')
        response = requests.get(dl_url, verify=CERTS_PATH)

        hugo_tar_path = WORKING_DIR_PATH / 'hugo.tar.gz'
        with hugo_tar_path.open('wb') as hugo_tar:
            for chunk in response.iter_content(chunk_size=128):
                hugo_tar.write(chunk)

        HUGO_BIN_PATH = WORKING_DIR_PATH / HUGO_BIN
        ctx.run(f'tar -xzf {hugo_tar_path} -C {WORKING_DIR_PATH}')
        ctx.run(f'chmod +x {HUGO_BIN_PATH}')
    except Exception:
        raise RuntimeError(f'Unable to download hugo version: {hugo_version}')


@task
def build_hugo(ctx, branch, owner, repository, site_prefix,
               base_url=''):
    '''
    Builds the cloned site with Hugo
    '''
    # Note that no pre/post-tasks will be called when calling
    # the download_hugo task this way
    download_hugo(ctx)

    HUGO_BIN_PATH = WORKING_DIR_PATH / HUGO_BIN

    hugo_vers_res = ctx.run(f'{HUGO_BIN_PATH} version')
    LOGGER.info(f'hugo version: {hugo_vers_res.stdout}')
    LOGGER.info('Building site with hugo')

    with node_context(ctx):  # in case some hugo plugin needs node
        hugo_args = (f'--source {CLONE_DIR_PATH} '
                     f'--destination {SITE_BUILD_DIR_PATH}')
        if base_url:
            hugo_args += f' --baseUrl {base_url}'

        ctx.run(
            f'{HUGO_BIN_PATH} {hugo_args}',
            env=build_env(branch, owner, repository,
                          site_prefix, base_url)
        )


@task(pre=[
    # Remove cloned repo's .git directory
    call(clean, which=path.join(CLONE_DIR_PATH, '.git')),
])
def build_static(ctx):
    '''Moves all files from CLONE_DIR into SITE_BUILD_DIR'''
    LOGGER.info(f'Moving files to {SITE_BUILD_DIR}')

    # Make the site build directory first
    SITE_BUILD_DIR_PATH.mkdir(exist_ok=True)

    files = os.listdir(CLONE_DIR_PATH)

    for file in files:
        # don't move the SITE_BUILD_DIR dir into itself
        if file is not SITE_BUILD_DIR:
            shutil.move(str(CLONE_DIR_PATH / file),
                        str(SITE_BUILD_DIR_PATH))

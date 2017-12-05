'''
Build tasks and helpers
'''

import os

from os import path

import json
import shutil

from contextlib import ExitStack
from pathlib import Path

import requests
from invoke import task, call

from log_utils import get_logger
from .common import (CLONE_DIR_PATH, SITE_BUILD_DIR,
                     WORKING_DIR, SITE_BUILD_DIR_PATH,
                     clean)


LOGGER = get_logger('BUILD')

NVM_SH_PATH = Path('/usr/local/nvm/nvm.sh')
RVM_PATH = Path('/usr/local/rvm/scripts/rvm')

HUGO_BIN = 'hugo'
HUGO_BIN_PATH = Path(path.join(WORKING_DIR), HUGO_BIN)

PACKAGE_JSON_PATH = Path(path.join(CLONE_DIR_PATH, 'package.json'))
NVMRC_PATH = Path(path.join(CLONE_DIR_PATH, '.nvmrc'))
RUBY_VERSION_PATH = Path(path.join(CLONE_DIR_PATH), '.ruby-version')
GEMFILE_PATH = Path(path.join(CLONE_DIR_PATH), 'Gemfile')
JEKYLL_CONF_YML_PATH = Path(path.join(CLONE_DIR_PATH, '_config.yml'))


def has_federalist_script():
    '''
    Checks for existence of the "federalist" script in the
    cloned repo's package.json.
    '''

    if PACKAGE_JSON_PATH.is_file():
        with open(PACKAGE_JSON_PATH) as json_file:
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

    with ctx.cd(CLONE_DIR_PATH):
        with ctx.prefix(f'source {NVM_SH_PATH}'):
            npm_command = 'npm'

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


def _run_federalist_script(ctx, branch, owner, repository,
                           site_prefix, base_url=''):
    '''
    Runs the npm "federalist" script if it is defined
    '''
    if PACKAGE_JSON_PATH.is_file() and has_federalist_script():
        with node_context(ctx, ctx.cd(CLONE_DIR_PATH)):
            LOGGER.info('Running federalist build script in package.json')
            ctx.run(
                'npm run federalist',
                env=build_env(branch, owner, repository,
                              site_prefix, base_url)
            )


# 'Exported' run_federalist_script task
run_federalist_script = task(
    pre=[setup_node], name='run-federalist-script')(_run_federalist_script)


@task
def setup_ruby(ctx):
    '''
    Sets up RVM and installs ruby
    Uses the ruby version specified in .ruby-version if present
    '''
    with ctx.prefix(f'source {RVM_PATH}'):
        if RUBY_VERSION_PATH.is_file():
            ruby_version = ''
            with open(RUBY_VERSION_PATH, 'r') as ruby_vers_file:
                ruby_version = ruby_vers_file.readline().strip()
            if ruby_version:
                LOGGER.info('Using ruby version in .ruby-version')
                ctx.run(f'rvm install {ruby_version}')

        ruby_ver_res = ctx.run('ruby -v')
        LOGGER.info(f'Ruby version: {ruby_ver_res.stdout}')


def _build_jekyll(ctx, branch, owner, repository, site_prefix,
                  config='', base_url=''):
    '''
    Builds the cloned site with Jekyll
    '''
    # Add baseurl, branch, and the custom config to _config.yml
    if JEKYLL_CONF_YML_PATH.is_file():
        with open(JEKYLL_CONF_YML_PATH, 'a') as jekyll_conf_file:
            jekyll_conf_file.writelines([
                '\n'
                f'baseurl: {base_url}\n',
                f'branch: {branch}\n',
                config,
                '\n',
            ])

    source_rvm = ctx.prefix(f'source {RVM_PATH}')
    with node_context(ctx, source_rvm, ctx.cd(CLONE_DIR_PATH)):
        jekyll_cmd = 'jekyll'

        if GEMFILE_PATH.is_file():
            LOGGER.info('Setting up bundler')
            ctx.run('gem install bundler')
            LOGGER.info('Installing dependencies in Gemfile')
            ctx.run('bundle install')
            jekyll_cmd = 'bundle exec ' + jekyll_cmd

        else:
            LOGGER.info('Installing Jekyll')
            ctx.run('gem install jekyll')

        jekyll_vers_res = ctx.run(f'{jekyll_cmd} -v')
        LOGGER.info(f'Building using Jekyll version: {jekyll_vers_res.stdout}')

        ctx.run(
            f'{jekyll_cmd} build --destination {SITE_BUILD_DIR_PATH}',
            env=build_env(branch, owner, repository, site_prefix, base_url)
        )


# 'Exported' build_jekyll task
build_jekyll = task(pre=[setup_ruby], name='build-jekyll')(_build_jekyll)


@task
def download_hugo(ctx, version='0.23'):
    '''
    Downloads the specified version of Hugo
    '''
    LOGGER.info(f'Downloading hugo version {version}')
    dl_url = (f'https://github.com/gohugoio/hugo/releases/download/'
              f'v{version}/hugo_{version}_Linux-64bit.tar.gz')
    response = requests.get(dl_url)
    hugo_tar_path = path.join(WORKING_DIR, 'hugo.tar.gz')
    with open(hugo_tar_path, 'wb') as hugo_tar:
        for chunk in response.iter_content(chunk_size=128):
            hugo_tar.write(chunk)

    ctx.run(f'tar -xzf {hugo_tar_path} -C {WORKING_DIR}')
    ctx.run(f'chmod +x {HUGO_BIN_PATH}')


@task
def build_hugo(ctx, branch, owner, repository, site_prefix,
               base_url='', hugo_version='0.23'):
    '''
    Builds the cloned site with Hugo
    '''
    # Note that no pre- or post-tasks will be called when calling
    # the download_hugo task this way
    download_hugo(ctx, hugo_version)

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


def _build_static(ctx):
    '''Moves all files from CLONE_DIR into SITE_BUILD_DIR'''
    LOGGER.info(f'Moving files to {SITE_BUILD_DIR}')
    os.makedirs(SITE_BUILD_DIR_PATH, exist_ok=True)
    files = os.listdir(CLONE_DIR_PATH)

    for file in files:
        # don't move the SITE_BUILD_DIR dir into itself
        if file is not SITE_BUILD_DIR:
            shutil.move(path.join(CLONE_DIR_PATH, file),
                        SITE_BUILD_DIR_PATH)


# 'Exported' build-static task
build_static = task(
    pre=[
        # Remove cloned repo's .git directory
        call(clean, which=path.join(CLONE_DIR_PATH, '.git')),
    ], name='build-static')(_build_static)

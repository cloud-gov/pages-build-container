'''
Build tasks and helpers
'''

import json
import shlex
import re
from contextlib import ExitStack
from pathlib import Path
from invoke import task

from common import (CLONE_DIR_PATH, SITE_BUILD_DIR_PATH)

NVM_SH_PATH = Path('/usr/local/nvm/nvm.sh')
RVM_PATH = Path('/usr/local/rvm/scripts/rvm')

NVMRC = '.nvmrc'
RUBY_VERSION = '.ruby-version'
GEMFILE = 'Gemfile'
JEKYLL_CONFIG_YML = '_config.yml'
BUNDLER_VERSION = '.bundler-version'


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


def build_env(branch, owner, repository, site_prefix, base_url,
              user_env_vars='[]'):
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

    for uev in json.loads(user_env_vars):
        name = uev['name']
        value = uev['value']
        if name in env or name.upper() in env:
            print(f'WARNING - user environment variable name `{name}` '
                  'conflicts with system environment variable, it will be '
                  'ignored.')
        else:
            env[name] = value

    return env


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
                print('Using ruby version in .ruby-version')
                ctx.run(f'rvm install {ruby_version}')

        ctx.run('echo Ruby version: $(ruby -v)')


@task
def setup_bundler(ctx):

    print('Setting up bundler')
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
                    print('Using bundler version in .bundler-version')
                    ctx.run(f'gem install bundler --version "{bundler_vers}"')
            except Exception:
                raise RuntimeError(f'Invalid .bundler-version')
    else:
        ctx.run('gem install bundler --version "<2"')


@task(pre=[setup_ruby])
def build_jekyll(ctx, branch, owner, repository, site_prefix,
                 config='', base_url='', user_env_vars='[]'):
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
            print('Installing dependencies in Gemfile')
            ctx.run('bundle install')
            jekyll_cmd = 'bundle exec ' + jekyll_cmd

        else:
            print('Installing Jekyll')
            ctx.run('gem install jekyll --no-document')

        ctx.run(f'echo Building using Jekyll version: $({jekyll_cmd} -v)')

        jekyll_build_env = build_env(branch, owner, repository, site_prefix,
                                     base_url, user_env_vars)
        # Use JEKYLL_ENV to tell jekyll to run in production mode
        jekyll_build_env['JEKYLL_ENV'] = 'production'

        ctx.run(
            f'{jekyll_cmd} build --destination {SITE_BUILD_DIR_PATH}',
            env=jekyll_build_env
        )

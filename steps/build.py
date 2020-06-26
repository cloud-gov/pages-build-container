import json
import os
import shutil
from os import path
from subprocess import CalledProcessError  # nosec

from common import (CLONE_DIR_PATH, SITE_BUILD_DIR, SITE_BUILD_DIR_PATH)
from log_utils import get_logger
from runner import run_with_node

NVMRC = '.nvmrc'
PACKAGE_JSON = 'package.json'
NVM_SH_PATH = '/usr/local/nvm/nvm.sh'


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
            print(f'WARNING - user environment variable name `{name}` '
                  'conflicts with system environment variable, it will be '
                  'ignored.')
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
        return run_with_node(logger, cmd, cwd=CLONE_DIR_PATH, env={}, check=True)

    try:
        NVMRC_PATH = CLONE_DIR_PATH / NVMRC
        if NVMRC_PATH.is_file():
            # nvm will output the node and npm versions used
            logger.info('Using node version specified in .nvmrc')
            runp('nvm install')
            runp('nvm use')
        else:
            # output node and npm versions if the defaults are used
            logger.info('Using default node version')
            runp('echo Node version: $(node --version)')
            runp('echo NPM version: $(npm --version)')

        PACKAGE_JSON_PATH = CLONE_DIR_PATH / PACKAGE_JSON
        if PACKAGE_JSON_PATH.is_file():
            logger.info('Installing production dependencies in package.json')
            runp('npm set audit false')
            runp('npm ci --production')

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
        return run_with_node(logger, 'npm run federalist', cwd=CLONE_DIR_PATH, env=env)

    return 0

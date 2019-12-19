from os import path
from pathlib import Path
from dotenv import load_dotenv

from log_utils import init_logging
from .common import clean
from .clone import clone_repo, push_repo_remote
from .build import (
    setup_node, setup_ruby, run_federalist_script, build_jekyll,
    build_hugo, build_static, download_hugo, setup_bundler)
from .publish import publish
from .main import main

__all__ = ['clean', 'clone_repo', 'push_repo_remote', 'setup_node',
           'setup_ruby', 'run_federalist_script', 'build_jekyll',
           'build_hugo', 'build_static', 'download_hugo',
           'publish', 'setup_bundler', 'main']

# First, and always, before any task, load the environment
DOTENV_PATH = Path(path.dirname(path.dirname(__file__))) / '.env'

if path.exists(DOTENV_PATH):
    print('Loading environment from .env file')
    load_dotenv(DOTENV_PATH)

init_logging()

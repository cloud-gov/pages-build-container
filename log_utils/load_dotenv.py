from os import path
from pathlib import Path
from dotenv import load_dotenv as _load_dotenv

BASE_DIR = Path(path.dirname(path.dirname(__file__)))
DOTENV_PATH = BASE_DIR / '.env'


def load_dotenv():  # pragma: no cover
    '''Loads environment from a .env file'''
    if path.exists(DOTENV_PATH):
        # LOGGER.info('Loading environment from .env file')
        _load_dotenv(DOTENV_PATH)

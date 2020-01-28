import getopt
import os
from pathlib import Path
import sys
from dotenv import load_dotenv
from tasks import main

def load_env():
    '''
    Load the environment from a .env file using `dotenv`.
    The file should only be present when running locally.

    Otherwise these environment variables will be set into the environment
    by federalist-builder.
    '''
    DOTENV_PATH = Path(os.path.dirname(__file__)) / '.env'

    if os.path.exists(DOTENV_PATH):
        print('Loading environment from .env file')
        load_dotenv(DOTENV_PATH)

flags = {
    'a': 'AWS_DEFAULT_REGION',
    'b': 'BUCKET',
    'c': 'BASEURL',
    'd': 'BUILD_ID',
    'e': 'CACHE_CONTROL',
    'f': 'BRANCH',
    'g': 'CONFIG',
    'h': 'REPOSITORY',
    'i': 'OWNER',
    'j': 'SITE_PREFIX',
    'k': 'GENERATOR',
    'l': 'AWS_ACCESS_KEY_ID',
    'm': 'AWS_SECRET_ACCESS_KEY',
    'n': 'FEDERALIST_BUILDER_CALLBACK',
    'o': 'STATUS_CALLBACK',
    # optional
    'p': 'SOURCE_REPO',
    'q': 'SOURCE_OWNER',
    'r': 'GITHUB_TOKEN',
    's': 'DATABASE_URL',
    't': 'SKIP_LOGGING'
}

if __name__ == "__main__":
    if len(sys.argv) > 1:
        print('Using command line arguments')
        try:
            short_opts = ':'.join(list(flags.keys())) + ':'
            opts, args = getopt.getopt(sys.argv[1:], short_opts)
        except getopt.GetoptError as err:
            print(err)
            usage()
            sys.exit(2)
        for opt, arg in opts:
            name = flags[opt[1:]]
            os.environ[name] = arg
        
    else:
        load_env()

    main()
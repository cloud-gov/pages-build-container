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
    'aws-access-key': 'AWS_ACCESS_KEY_ID',
    'aws-region': 'AWS_DEFAULT_REGION',
    'aws-secret-access-key': 'AWS_SECRET_ACCESS_KEY',
    'baseurl': 'BASEURL',
    'branch': 'BRANCH',
    'bucket': 'BUCKET',
    'build-id': 'BUILD_ID',
    'builder-callback': 'FEDERALIST_BUILDER_CALLBACK',
    'cache-control': 'CACHE_CONTROL',
    'config': 'CONFIG',
    'generator': 'GENERATOR',
    'github-token': 'GITHUB_TOKEN',
    'owner': 'OWNER',
    'repo': 'REPOSITORY',
    'site-prefix': 'SITE_PREFIX',
    'source-repo': 'SOURCE_REPO',
    'source-owner': 'SOURCE_OWNER',
    'status-callback': 'STATUS_CALLBACK',
    'skip-logging': 'SKIP_LOGGING'
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

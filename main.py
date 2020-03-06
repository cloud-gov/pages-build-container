import argparse
import json
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


if __name__ == "__main__":
    if len(sys.argv) > 1:
        parser = argparse.ArgumentParser(description='Run a federalist build')
        parser.add_argument('-p', '--params', dest='params', required=True,
                            help='A JSON encoded string',
                            metavar="'{\"foo\": \"bar\"}'")
        args = parser.parse_args()
        params = json.loads(args.params)
        for k,v in params.items():
            os.environ[k] = v

    else:
        load_env()

    main()

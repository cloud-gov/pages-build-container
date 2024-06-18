import argparse
import inspect
import json
import os
import shlex

from build import build
from crypto.decrypt import decrypt


KEYS_TO_DECRYPT = [
    'STATUS_CALLBACK',
    'GITHUB_TOKEN',
    'AWS_ACCESS_KEY_ID',
    'AWS_SECRET_ACCESS_KEY',
    'BUCKET',
]


def load_vcap():
    vcap_application = json.loads(os.getenv('VCAP_APPLICATION', '{}'))
    vcap_services = json.loads(os.getenv('VCAP_SERVICES', '{}'))

    space = vcap_application['space_name']

    space_prefix = 'pages-staging' if space == 'pages-staging' else f'federalist-{space}'

    uev_ups = next(
        ups for ups in vcap_services['user-provided']
        if ups['name'] == f'{space_prefix}-uev-key'
    )

    uev_env_var = 'USER_ENVIRONMENT_VARIABLE_KEY'
    os.environ[uev_env_var] = uev_ups['credentials']['key']


def decrypt_key_value(k, v, encryption_key):
    if k in KEYS_TO_DECRYPT:
        return decrypt(v, encryption_key)
    return v


def decrypt_params(params):
    vcap_application = json.loads(os.getenv('VCAP_APPLICATION', '{}'))
    vcap_services = json.loads(os.getenv('VCAP_SERVICES', '{}'))

    space = vcap_application['space_name']

    encryption_ups = next(
        ups for ups in vcap_services['user-provided']
        if ups['name'] == f'pages-{space}-encryption'
    )

    encryption_key = encryption_ups['credentials']['key']

    params = {k: decrypt_key_value(k, v, encryption_key) for (k, v) in params.items()}

    return params


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Run a pages build')
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('-p', '--params', dest='params',
                       help='A JSON encoded string',
                       metavar="'{\"foo\": \"bar\"}'")
    group.add_argument('-f', '--file', dest='file',
                       help='A path to a JSON file', type=argparse.FileType('r'),
                       metavar="./foo.json")
    args = parser.parse_args()

    if args.params:
        params = json.loads(args.params)
        params = decrypt_params(params)
    else:
        params = json.load(args.file)

    params = {k.lower(): v for (k, v) in params.items()}

    build_arguments = inspect.getfullargspec(build)[0]
    for k in params:
        if k not in build_arguments:
            # Warn about unused arguments
            print(f'WARNING - Ignoring unused parameter: {k}')

    # Remove unused build arguments
    kwargs = {k: v for (k, v) in params.items() if k in build_arguments}

    if 'user_environment_variables' in kwargs:
        uevs = kwargs['user_environment_variables']
        if uevs and isinstance(uevs, str):
            kwargs['user_environment_variables'] = json.loads(uevs)

    kwargs['branch'] = shlex.quote(kwargs['branch'])
    kwargs['owner'] = shlex.quote(kwargs['owner'])
    kwargs['repository'] = shlex.quote(kwargs['repository'])

    if os.getenv('VCAP_APPLICATION', None):
        load_vcap()

    build(**kwargs)

import json
from os import path
from .repo_config import RepoConfig

__all__ = [
    'RepoConfig', 'from_json_file', 'from_object'
]

FEDERALIST_JSON = 'federalist.json'


def from_json_file(clone_dir, defaults={}):
    obj = {}

    federalist_json_path = path.join(clone_dir, FEDERALIST_JSON)
    if path.isfile(federalist_json_path):
        with open(federalist_json_path) as json_file:
            obj = json.load(json_file)

    return from_object(obj, defaults)


def from_object(obj, defaults={}):
    return RepoConfig(obj, defaults)

import json
from os import path
from .repo_config import RepoConfig

__all__ = [
    'RepoConfig', 'from_json_file', 'from_object'
]

PAGES_JSON = 'pages.json'
FEDERALIST_JSON = 'federalist.json'


def from_json_file(clone_dir, defaults={}):
    obj = {}

    json_files = [PAGES_JSON, FEDERALIST_JSON]
    for json_file_name in json_files:
        json_file_path = path.join(clone_dir, json_file_name)
        if path.isfile(json_file_path):
            with open(json_file_path) as json_file:
                obj = json.load(json_file)
            break

    return from_object(obj, defaults)


def from_object(obj, defaults={}):
    return RepoConfig(obj, defaults)

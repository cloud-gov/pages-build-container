import fnmatch


class RepoConfig:
    '''
    Encapsulate the logic for handling the `federalist.json` configuration

    The file should look something like:
    {
        "fullClone": true,
        "headers": [
            "/*": {
                "cache-control": "no-cache"
            }
        ],
        "excludePaths": [
            "**/Dockerfile",
            "/another_excluded_file.yml"
        ],
        "includePaths": [
            "/included_file",
            "/.well-known/security.txt
        ],
        "cache": true
    }

    Currently, only the following keys are utilized:
        - headers
        - excludePaths
        - includePaths
        - fullClone
        - cache
    '''

    def __init__(self, config={}, defaults={}):
        self.config = config
        self.defaults = defaults

    def get_headers_for_path(self, path_to_match):
        '''
        Determine the headers that apply to particular filepath
        '''

        # A shallow copy should be sufficient
        resolved_headers = self.defaults.get('headers', {}).copy()

        first_matching_cfg = find_first_matching_cfg(
            self.config.get('headers', []),
            path_to_match)

        if first_matching_cfg:
            headers = first_value(first_matching_cfg)

            for key, value in headers.items():
                resolved_headers[key.strip().lower()] = value.strip()

        return resolved_headers

    def is_path_excluded(self, path_to_match):
        return ((contains_dotpath(path_to_match) or self.is_exclude_path_match(path_to_match))
                and not self.is_include_path_match(path_to_match))

    def is_path_included(self, path_to_match):
        return not self.is_path_excluded(path_to_match)

    def is_exclude_path_match(self, path_to_match):
        return is_path_match(self.exclude_paths(), path_to_match)

    def is_include_path_match(self, path_to_match):
        return is_path_match(self.include_paths(), path_to_match)

    def full_clone(self):
        return self.config.get('fullClone', False) is True

    def exclude_paths(self):
        return self.config.get('excludePaths', []) + self.defaults.get('excludePaths', [])

    def include_paths(self):
        return self.config.get('includePaths', []) + self.defaults.get('includePaths', [])

    def should_cache(self):
        return self.config.get('cache', False) is True


def contains_dotpath(filename):
    return any(segment for segment in filename.split('/') if segment.startswith('.'))


def is_path_match(patterns, path_to_match):
    for pattern in patterns:
        if fnmatch.fnmatch(prepend_slash(path_to_match), pattern):
            return True

    return False


def find_first_matching_cfg(configuration_section, path_to_match):
    '''
    Find and return the FIRST configuration rule where the `path_to_match` matches
    the configured pattern.

    Order is important, so the configuration must be specified and handled as a
    list.

    If no path matches, an empty dict is returned.
    '''

    return next(
        (configuration_rule
            for configuration_rule
            in configuration_section
            if match_path(first_key(configuration_rule), path_to_match)),
        {})


def match_path(pattern, path_to_match):
    '''
    Determine if the `path_to_match` matches the path `pattern`

    >>> match_path('/*', '/index.html')
    True

    >>> match_path('/index.html', '/foo.js')
    False

    Patterns can contain the '*' and ':foo' wildcards.

    The '*' wildcard will match anything including '/'
    Ex.

    >>> match_path('/*', '/foo/bar/baz/index.html')
    True

    When combined with an extension, ie '*.html', the wildcard will match
    everything up to the LAST extension in the path to match, which must
    be matched exactly.
    Ex.

    >>> match_path('/*.html', '/foo/bar/baz/index.foo.html')
    True

    >>> match_path('/*.foo', '/foo/bar/baz/index.foo.html')
    False

    The ':foo' wildcard will match anything EXCEPT '/',
    ie it is a single segment wildcard. It can contain any letters after ':'
    Ex.

    >>> match_path('/:foo/bar', '/abc/bar')
    True

    >>> match_path('/:baz', '/abc/foo')
    False
    '''

    # normalize the paths by removing leading slash since that will
    # result in a leading empty string with 'split'ing
    pattern = strip_prefix('/', pattern)
    path_to_match = strip_prefix('/', path_to_match)

    pattern_parts = pattern.split('/')
    path_parts = path_to_match.split('/')

    for idx, pattern_part in enumerate(pattern_parts):
        if pattern_part == '*':
            return True

        if pattern_part.startswith(':'):
            continue

        if len(path_parts) <= idx:
            return False

        if pattern_part.startswith('*.'):
            pattern_part_ext = pattern_part.split('.')[-1]
            last_path_part = path_parts[-1]
            last_path_ext = last_path_part.split('.')[-1]
            return last_path_ext == pattern_part_ext

        path_part = path_parts[idx]

        if path_part != pattern_part:
            return False

    if len(path_parts) > len(pattern_parts):
        return False

    return True


def first_key(dikt):
    return next(key for key in dikt)


def first_value(dikt):
    return next(value for value in dikt.values())


def strip_prefix(prefix, path):
    # Copied from models.py::remove_prefix
    return path[len(prefix):] if path.startswith(prefix) else path


def prepend_slash(path):
    return path if path.startswith('/') else ('/' + path)

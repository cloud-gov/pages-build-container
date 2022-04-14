from repo_config.repo_config import (RepoConfig, match_path,
                                     find_first_matching_cfg)


def test_match_path():

    # (<cfg_path>, <path_to_match>, <expected result>)
    configs = [
        # static paths
        ('/',            '/',            True),
        ('/',            '/hello',       False),
        ('/hello',       '/hello',       True),
        ('/hello',       '/hello/world', False),
        ('/hello/world', '/hello',       False),

        # wildcard paths
        ('/*',       '/',                             True),
        ('/*',       '/hello',                        True),
        ('/*',       '/hello.js',                     True),
        ('/*',       '/hello/world',                  True),
        ('/hello/*', '/hello/world',                  True),
        ('/hello/*', '/world',                        False),
        ('/hello/*', '/hello/sdhgfsjdh/dkjhsfhsdfkj', True),

        # wildcard extension paths
        ('/*.html',     '/',                 False),
        ('/*.html',     '/foo',              False),
        ('/*.html',     '/foo.js',           False),
        ('/*.html',     '/foo.html',         True),
        ('/bar/*.html', '/foo.html',         False),
        ('/bar/*.html', '/bar/foo.html',     True),
        ('/bar/*.html', '/bar/foo.js',       False),
        ('/bar/*.html', '/bar/baz/foo.html', True),
        ('/bar/*.html', '/bar/baz/foo.js',   False),
        ('/bar/*.map',  '/bar/foo.js.map',   True),

        # segment wildcard paths
        ('/:hello',       '/',             True),
        ('/:hello',       '/booyah',       True),
        ('/:hello',       '/booyah/world', False),
        ('/:hello/world', '/booyah/world', True),
        ('/:hello/world', '/booyah/hello', False),
        ('/:hello/world', '/booyah',       False),

        # crazy town
        ('/hello/*/foo',       '/hello/sdhgfsjdh/dkjhsfhsdfkj', True),
        ('/:hello/world/*',    '/booyah/world',                 True),
        ('/:hello/world/*',    '/booyah/world/foo',             True),
        ('/hi/:hello/world/*', '/hi/booyah/nope',               False),
        ('/hi/:hello/world/*', '/hi/booyah/world',              True),
        ('/hi/:hello/world/*', '/hi/booyah/world/crazy',        True),

        # even when missing leading '/'
        (':hello/world/*',  '/booyah/world/foo', True),
        (':hello/world/*',  'booyah/world/foo',  True),
        ('/:hello/world/*', 'booyah/world',      True),
    ]

    for cfg_path, path_to_match, expected_result in configs:
        assert match_path(cfg_path, path_to_match) == expected_result


def test_find_first_matching_cfg():
    headers = [
        {'/index.html':  {'cache-control': 'no-cache'}},
        {'/:foo/*.html': {'cache-control': 'max-age=2000'}},
        {'/*.html':      {'cache-control': 'max-age=4000'}},
        {'/*':           {'cache-control': 'max-age=6000'}}
    ]

    configs = [
      (headers, '/index.html',   headers[0]),
      (headers, '/foo/bar.html', headers[1]),
      (headers, '/foo.html',     headers[2]),
      (headers, '/',             headers[3]),
      (headers, '/bar.js',       headers[3]),
      ({},      '/bar.js',       {})
    ]

    for cfg_headers, path_to_match, expected_result in configs:
        assert find_first_matching_cfg(
                cfg_headers, path_to_match) == expected_result


def test_get_headers_for_path():
    config = {
        'headers': [
            {'/index.html': {'cache-control': 'no-cache'}},
            {'/*.html':     {'cache-control': 'max-age=4000'}},
            {'/*':          {'cache-control': 'max-age=6000'}}
        ]
    }

    defaults = {
        'headers': {
            'cache-control': 'max-age=60',
            'foo-header': 'special-stuff:with-a-colon!'
        }
    }

    repo_config = RepoConfig(config=config, defaults=defaults)

    # When multiple paths match, return the first
    path_to_match = '/index.html'
    value = repo_config.get_headers_for_path(path_to_match)
    assert value == {
        'cache-control': 'no-cache',
        'foo-header': 'special-stuff:with-a-colon!'
    }

    # Match the partial wildcard
    path_to_match = '/foo.html'
    value = repo_config.get_headers_for_path(path_to_match)
    assert value == {
        'cache-control': 'max-age=4000',
        'foo-header': 'special-stuff:with-a-colon!'
    }

    # Match the total wildcard
    path_to_match = '/foo.js'
    value = repo_config.get_headers_for_path(path_to_match)
    assert value == {
        'cache-control': 'max-age=6000',
        'foo-header': 'special-stuff:with-a-colon!'
    }

    # Match default
    config = {
        'headers': [
            {'/index.html': {'cache-control': 'max-age=3000'}}
        ]
    }
    repo_config = RepoConfig(config=config, defaults=defaults)

    path_to_match = '/foo.js'
    value = repo_config.get_headers_for_path(path_to_match)
    assert value == defaults['headers']

    # Match no headers!
    config = {}
    repo_config = RepoConfig(config=config, defaults=defaults)

    path_to_match = '/foo.js'
    value = repo_config.get_headers_for_path(path_to_match)
    assert value == defaults['headers']


def test_is_path_excluded():
    config = {
        'excludePaths': [
            '/excluded-file',
        ]
    }

    defaults = {
        'excludePaths': [
            '/Dockerfile',
            '/docker-compose.yml'
        ]
    }

    repo_config = RepoConfig(config=config, defaults=defaults)

    # Excludes a file explicitly excluded
    value = repo_config.is_path_excluded('/excluded-file')
    assert value is True

    # Doesn't exclude a file not explicitly excluded
    value = repo_config.is_path_excluded('/index.html')
    assert value is not True

    # Excludes Dockerfile by default when that file is in defaults
    value = repo_config.is_path_excluded('/Dockerfile')
    assert value is True

    # Excludes docker-compose.yml by default when that file is in defaults
    value = repo_config.is_path_excluded('/docker-compose.yml')
    assert value is True

    config = {
        'includePaths': [
            '/Dockerfile',
        ]
    }

    repo_config = RepoConfig(config=config, defaults=defaults)

    # Includes Dockerfile when that default is overridden by configuration
    value = repo_config.is_path_excluded('/Dockerfile')
    assert value is not True

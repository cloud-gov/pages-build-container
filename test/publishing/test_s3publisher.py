import boto3
import pytest
import requests_mock
import yaml

from moto import mock_s3

from publishing.s3publisher import list_remote_objects, publish_to_s3
from publishing.models import SiteObject

TEST_BUCKET = 'test-bucket'
TEST_REGION = 'test-region'
TEST_ACCESS_KEY = 'fake-access-key'
TEST_SECRET_KEY = 'fake-secret-key'
OWNER = 'the_owner',
REPOSITORY = 'the_repository'
AUTH_ENDPOINT = 'the_auth_endpoint'
BASE_URL = '/base_url'
AUTH_BASE_URL = 'https://base_url.com'
BUCKET_TYPE = 'dedicated'


@pytest.fixture
def s3_client(monkeypatch):
    monkeypatch.setenv('AWS_ACCESS_KEY_ID', TEST_ACCESS_KEY)
    monkeypatch.setenv('AWS_SECRET_ACCESS_KEY', TEST_SECRET_KEY)

    with mock_s3():
        conn = boto3.resource('s3', region_name=TEST_REGION)

        conn.create_bucket(Bucket=TEST_BUCKET)

        s3_client = boto3.client(
            service_name='s3',
            region_name=TEST_REGION,
            aws_access_key_id=TEST_ACCESS_KEY,
            aws_secret_access_key=TEST_SECRET_KEY,
        )

        yield s3_client


def test_list_remote_objects(monkeypatch, s3_client):
    # Check that nothing is returned if nothing is in the bucket
    results = list_remote_objects(TEST_BUCKET, '/test-site', s3_client)
    assert results == []

    # Add a few objects with different prefixes
    s3_client.put_object(Key='/test-site/a', Body='a', Bucket=TEST_BUCKET)
    s3_client.put_object(Key='/wrong-prefix/b', Body='b', Bucket=TEST_BUCKET)

    # Check that only one object matching the prefix is returned
    results = list_remote_objects(TEST_BUCKET, '/test-site', s3_client)
    assert len(results) == 1
    assert type(results[0]) == SiteObject
    assert results[0].s3_key == '/test-site/a'

    # Add a few more objects
    for i in range(0, 10):
        s3_client.put_object(Key=f'/test-site/sub/{i}.html',
                             Body=f'{i}', Bucket=TEST_BUCKET)

    # Monkeypatch max keys so we can ensure ContinuationTokens are used
    monkeypatch.setattr('publishing.s3publisher.MAX_S3_KEYS_PER_REQUEST', 5)

    # Check that we get all expected objects back
    results = list_remote_objects(TEST_BUCKET, '/test-site', s3_client)
    assert len(results) == 11  # 10 keys from the loop, 1 from previous put


def _make_fake_files(dir, filenames):
    for f_name in filenames:
        file = dir.join(f_name)
        file.write(f'fake content for {f_name}')


def _make_fake_admin_config(dir, f_name='admin/config.yml'):
    config = {
        'backend': {
        }
    }
    file = dir.join(f_name)
    file.write(yaml.dump(config))


def test_publish_to_s3(tmpdir, s3_client):
    # Use tmpdir to create a fake directory
    # full of directories and files to be published/deleted/updated
    test_dir = tmpdir.mkdir('test_dir')

    # make a subdirectory
    test_dir.mkdir('sub_dir')

    site_prefix = 'test_dir'

    filenames = ['index.html',
                 'boop.txt',
                 'sub_dir/index.html']

    _make_fake_files(test_dir, filenames)

    publish_kwargs = {
        'directory': str(test_dir),
        'base_url': BASE_URL,
        'site_prefix': site_prefix,
        'bucket': TEST_BUCKET,
        'cache_control': 'max-age=10',
        's3_client': s3_client,
        'owner': OWNER,
        'repository': REPOSITORY,
        'auth_endpoint': AUTH_ENDPOINT,
        'auth_base_url': AUTH_BASE_URL,
        'bucket_type': BUCKET_TYPE,
    }

    # Create mock for default 404 page request
    with requests_mock.mock() as m:
        m.get(('https://raw.githubusercontent.com'
               '/18F/federalist-404-page/master/'
               '404-federalist-client.html'),
              text='default 404 page')

        publish_to_s3(**publish_kwargs)

        results = s3_client.list_objects_v2(Bucket=TEST_BUCKET)

        keys = [r['Key'] for r in results['Contents']]

        assert results['KeyCount'] == 6  # 4 files, 3 redirects & 404.html

        assert f'{site_prefix}/index.html' in keys
        assert f'{site_prefix}/boop.txt' in keys
        assert f'{site_prefix}/sub_dir' in keys
        assert f'{site_prefix}/sub_dir/index.html' in keys
        assert f'{site_prefix}/404.html' in keys
        assert f'{site_prefix}' in keys  # main redirect object

        # Add another file to the directory
        more_filenames = ['new_index.html']
        _make_fake_files(test_dir, more_filenames)
        publish_to_s3(**publish_kwargs)
        results = s3_client.list_objects_v2(Bucket=TEST_BUCKET)

        assert results['KeyCount'] == 7

        # Delete some files and check that the published files count
        # is correct
        test_dir.join('new_index.html').remove()
        test_dir.join('boop.txt').remove()
        publish_to_s3(**publish_kwargs)
        results = s3_client.list_objects_v2(Bucket=TEST_BUCKET)
        assert results['KeyCount'] == 5

        # Write an existing file with different content so that it
        # needs to get updated
        index_key = f'{site_prefix}/index.html'
        orig_etag = s3_client.get_object(
                        Bucket=TEST_BUCKET,
                        Key=index_key)['ETag']
        test_dir.join('index.html').write('totally new content!!!')
        publish_to_s3(**publish_kwargs)
        results = s3_client.list_objects_v2(Bucket=TEST_BUCKET)

        # number of keys should be the same
        assert results['KeyCount'] == 5

        # make sure content in changed file is updated
        new_etag = s3_client.get_object(
                    Bucket=TEST_BUCKET,
                    Key=index_key)['ETag']
        assert new_etag != orig_etag

        # test hidden files and directories
        test_dir.mkdir('.well-known')
        test_dir.mkdir('.not-well-known')
        more_filenames = ['.well-known/security.txt',
                          '.well-known/not-security.txt',
                          '.well-known/.security',
                          '.not-well-known/security.txt',
                          '.security']
        _make_fake_files(test_dir, more_filenames)
        publish_to_s3(**publish_kwargs)
        results = s3_client.list_objects_v2(Bucket=TEST_BUCKET)
        assert results['KeyCount'] == 6

        # test admin config updated
        test_dir.mkdir('admin')
        admin_config = 'admin/config.yml'
        _make_fake_admin_config(test_dir, admin_config)
        publish_to_s3(**publish_kwargs)
        results = s3_client.list_objects_v2(Bucket=TEST_BUCKET)
        assert results['KeyCount'] == 7
        config = None
        with open(test_dir.join(admin_config)) as f:
            config = yaml.safe_load(f)
        assert config['backend']['repo'] == f'{OWNER}/{REPOSITORY}'
        assert config['backend']['auth_endpoint'] == AUTH_ENDPOINT
        assert config["backend"]["base_url"] == AUTH_BASE_URL

        publish_kwargs['bucket_type'] = 'shared'
        publish_to_s3(**publish_kwargs)
        results = s3_client.list_objects_v2(Bucket=TEST_BUCKET)
        assert results['KeyCount'] == 7
        config = None
        with open(test_dir.join(admin_config)) as f:
            config = yaml.safe_load(f)
        assert config['backend'] == {}

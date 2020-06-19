import boto3
import pytest
import requests_mock

from unittest.mock import Mock

from moto import mock_s3

from steps import publish
from common import SITE_BUILD_DIR_PATH

TEST_BUCKET = 'test-bucket'
TEST_REGION = 'test-region'
TEST_ACCESS_KEY = 'fake-access-key'
TEST_SECRET_KEY = 'fake-secret-key'


@pytest.fixture
def s3_conn(monkeypatch):
    with mock_s3():
        conn = boto3.resource(
            's3',
            aws_access_key_id=TEST_ACCESS_KEY,
            aws_secret_access_key=TEST_SECRET_KEY,
            region_name=TEST_BUCKET
        )
        conn.create_bucket(Bucket=TEST_BUCKET)
        yield conn


class TestPublish():
    def test_it_is_callable(self, s3_conn):
        # Create mock for default 404 page request
        with requests_mock.mock() as m:
            m.get(('https://raw.githubusercontent.com'
                   '/18F/federalist-404-page/master/'
                   '404-federalist-client.html'),
                  text='default 404 page')

            publish(
                base_url='/site/prefix', site_prefix='site/prefix',
                bucket=TEST_BUCKET, cache_control='max-age: boop',
                aws_region=TEST_REGION, aws_access_key_id=TEST_ACCESS_KEY,
                aws_secret_access_key=TEST_SECRET_KEY
            )

    def test_it_calls_publish_to_s3(self, monkeypatch, s3_conn):
        mock_publish_to_s3 = Mock()
        monkeypatch.setattr('publishing.s3publisher.publish_to_s3',
                            mock_publish_to_s3)

        kwargs = dict(
            base_url='/site/prefix',
            site_prefix='site/prefix',
            bucket=TEST_BUCKET,
            cache_control='max-age: boop',
            aws_region=TEST_REGION,
            aws_access_key_id=TEST_ACCESS_KEY,
            aws_secret_access_key=TEST_SECRET_KEY
        )

        publish(**kwargs)

        mock_publish_to_s3.assert_called_once()

        # check that the `directory` kwarg is a string, not a Path
        _, actual_kwargs = mock_publish_to_s3.call_args_list[0]
        assert type(actual_kwargs['directory']) == str
        assert actual_kwargs['directory'] == str(SITE_BUILD_DIR_PATH)

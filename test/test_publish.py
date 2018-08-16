import boto3
import pytest

from unittest.mock import Mock

from moto import mock_s3
from invoke import MockContext

from tasks import publish
from tasks.common import SITE_BUILD_DIR_PATH

TEST_BUCKET = 'test-bucket'
TEST_REGION = 'test-region'


@pytest.fixture
def s3_conn(monkeypatch):
    with mock_s3():
        monkeypatch.setenv('AWS_ACCESS_KEY_ID', 'fake-access-key')
        monkeypatch.setenv('AWS_SECRET_ACCESS_KEY', 'fake-secret-key')
        conn = boto3.resource('s3', region_name=TEST_BUCKET)
        conn.create_bucket(Bucket=TEST_BUCKET)
        yield conn


class TestPublish():
    def test_it_is_callable(self, s3_conn):
        ctx = MockContext()

        publish(ctx, base_url='/site/prefix', site_prefix='site/prefix',
                bucket=TEST_BUCKET, cache_control='max-age: boop',
                aws_region=TEST_REGION)

    def test_it_calls_publish_to_s3(self, monkeypatch, s3_conn):
        mock_publish_to_s3 = Mock()
        monkeypatch.setattr('publishing.s3publisher.publish_to_s3',
                            mock_publish_to_s3)

        ctx = MockContext()

        kwargs = dict(
            base_url='/site/prefix',
            site_prefix='site/prefix',
            bucket=TEST_BUCKET,
            cache_control='max-age: boop',
            aws_region=TEST_REGION,
        )

        publish(ctx, **kwargs)

        mock_publish_to_s3.assert_called_once()

        # check that the `directory` kwarg is a string, not a Path
        _, actual_kwargs = mock_publish_to_s3.call_args_list[0]
        assert type(actual_kwargs['directory']) == str
        assert actual_kwargs['directory'] == str(SITE_BUILD_DIR_PATH)

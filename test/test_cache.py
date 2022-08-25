import os
import boto3
import pytest
import tempfile
import filecmp

from unittest.mock import Mock

from moto import mock_s3

from steps.cache import CacheFolder, get_checksum


@pytest.fixture
def aws_credentials():
    """Mocked AWS Credentials for moto."""
    os.environ["AWS_ACCESS_KEY_ID"] = "testing"
    os.environ["AWS_SECRET_ACCESS_KEY"] = "testing"
    os.environ["AWS_DEFAULT_REGION"] = "testing"


@pytest.fixture
def s3_client(aws_credentials):
    with mock_s3():
        conn = boto3.client("s3")
        yield conn

@pytest.fixture
def bucket(s3_client):
    s3_client.create_bucket(
        Bucket='testing',
        CreateBucketConfiguration={"LocationConstraint": "testing" }
    )
    yield

@pytest.fixture
def cache_folder(s3_client, bucket):
    yield CacheFolder('mykey', 'testing', s3_client)


class TestCache():
    @pytest.fixture(autouse=True)
    def inject_fixtures(self, tmpdir):
        self._tmpdir = tmpdir

    def test_cache_operations(self, cache_folder: CacheFolder):
        # first the cache isn't there
        not_there = cache_folder.exists()
        assert not not_there

        # add some files and cache them
        FILES_TO_CACHE = 5
        for _ in range(FILES_TO_CACHE):
            tempfile.NamedTemporaryFile(dir=self._tmpdir, delete=False)
        cache_folder.zip_upload_folder_to_s3(self._tmpdir)

        # some the cache exists
        there = cache_folder.exists()
        assert there

        # download the cache and compare
        with tempfile.TemporaryDirectory() as download_tmp_dir:
            cache_folder.download_unzip(download_tmp_dir)
            dir_comp = filecmp.dircmp(self._tmpdir, download_tmp_dir)
            assert len(dir_comp.common) == FILES_TO_CACHE
            assert len(dir_comp.diff_files) == 0





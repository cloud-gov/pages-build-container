import os
import boto3
import pytest
import tempfile
import filecmp
import shutil

from moto import mock_aws

from steps.cache import CacheFolder, get_checksum
from log_utils import get_logger


@pytest.fixture
def aws_credentials():
    """Mocked AWS Credentials for moto."""
    os.environ["AWS_ACCESS_KEY_ID"] = "testing"
    os.environ["AWS_SECRET_ACCESS_KEY"] = "testing"
    os.environ["AWS_DEFAULT_REGION"] = "testing"


@pytest.fixture
def s3_client(aws_credentials):
    with mock_aws():
        conn = boto3.client("s3")
        yield conn


@pytest.fixture
def bucket(s3_client):
    s3_client.create_bucket(
        Bucket='testing',
        CreateBucketConfiguration={"LocationConstraint": "testing"}
    )
    yield


@pytest.fixture
def gemfile():
    tmp_file = tempfile.NamedTemporaryFile(delete=False)
    tmp_file.write(b'source "https://rubygems.org"')
    tmp_file.write(b'gem "jekyll", "~> 4.0"')
    yield tmp_file.name


@pytest.fixture(autouse=True)
def cache_folder(s3_client, bucket, gemfile, tmpdir):
    logger = get_logger('testing')
    yield CacheFolder(gemfile, tmpdir, 'testing', s3_client, logger)


class TestCache():
    def test_cache_operations(self, cache_folder: CacheFolder):
        # first the cache isn't there
        assert not cache_folder.exists()

        # add some files and cache them
        FILES_TO_CACHE = 5
        for _ in range(FILES_TO_CACHE):
            tempfile.NamedTemporaryFile(dir=cache_folder.local_folder, delete=False)
        cache_folder.zip_upload_folder_to_s3()

        # now the cache exists
        assert cache_folder.exists()

        # move the old files to a new directory for comparison
        with tempfile.TemporaryDirectory() as download_tmp_dir:
            for f in os.listdir(cache_folder.local_folder):
                shutil.move(
                    os.path.join(cache_folder.local_folder, f),
                    os.path.join(download_tmp_dir, f)
                )

            # download the cache and compare
            cache_folder.download_unzip()
            dir_comp = filecmp.dircmp(cache_folder.local_folder, download_tmp_dir)
            assert len(dir_comp.common) == FILES_TO_CACHE
            assert len(dir_comp.diff_files) == 0

    def test_checksum(self, gemfile):
        c = get_checksum(gemfile)
        assert c == 'd41d8cd98f00b204e9800998ecf8427e'

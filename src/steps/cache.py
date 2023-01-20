from datetime import datetime, timedelta
import os
import hashlib
import shutil
import botocore

# Cache expiration time
NEXT_MONTH = datetime.now() + timedelta(days=30)
ARCHIVE_METHOD = 'tar'


def get_checksum(filename):
    m = hashlib.md5()  # nosec
    with open(filename, 'rb') as f:
        while chunk := f.read(4096):
            m.update(chunk)
    return m.hexdigest()


class CacheFolder():
    '''
    An abstract class for a cache folder in S3
    '''

    def __init__(self, checksum_file, local_folder, bucket, s3_client, logger):
        self.checksum_file = checksum_file
        self.key = get_checksum(checksum_file)
        self.local_folder = local_folder
        self.bucket = bucket
        self.s3_client = s3_client
        self.logger = logger

    def exists(self):
        '''Check if a given cache key exists'''
        try:
            self.s3_client.head_object(
                Bucket=self.bucket,
                Key=f'_cache/{self.key}'
            )
            return True
        except botocore.exceptions.ClientError as error:
            if error.response['Error']['Message'] == 'Not Found':
                return False
            else:
                self.logger.error(error.response['Error'])
                raise error

    def zip_upload_folder_to_s3(self):
        self.logger.info(f'Caching dependencies from {self.local_folder}.')
        tmp_file = f'{self.key}.{ARCHIVE_METHOD}'
        shutil.make_archive(self.key, ARCHIVE_METHOD, self.local_folder)
        self.logger.info(f'Created archive {tmp_file}')
        self.s3_client.upload_file(
            Filename=tmp_file,
            Bucket=self.bucket,
            Key=f'_cache/{self.key}',
            ExtraArgs=dict(Expires=NEXT_MONTH)
        )
        os.unlink(tmp_file)

    def download_unzip(self):
        if self.exists():
            self.logger.info(f'Dependency cache found, downloading to {self.local_folder}.')
            tmp_file = f'{self.key}.{ARCHIVE_METHOD}'
            self.s3_client.download_file(
                Filename=tmp_file,
                Bucket=self.bucket,
                Key=f'_cache/{self.key}'
            )
            shutil.unpack_archive(tmp_file, self.local_folder, ARCHIVE_METHOD)
            os.unlink(tmp_file)
        else:
            self.logger.info('No cache file found.')

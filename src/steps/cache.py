import os
import hashlib
import shutil
import botocore


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

    def __init__(self, key, bucket, s3_client):
        self.key = key
        self.bucket = bucket
        self.s3_client = s3_client

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
                print(error.response['Error'])
                raise error

    def zip_upload_folder_to_s3(self, folder):
        tmp_file = f'{self.key}.zip'
        shutil.make_archive(self.key, 'zip', folder)
        self.s3_client.upload_file(
            Filename=tmp_file,
            Bucket=self.bucket,
            Key=f'_cache/{self.key}',
        )
        os.unlink(tmp_file)

    def download_unzip(self, folder):
        tmp_file = f'{self.key}.zip'
        self.s3_client.download_file(
            Filename=tmp_file,
            Bucket=self.bucket,
            Key=f'_cache/{self.key}'
        )
        shutil.unpack_archive(tmp_file, folder, 'zip')
        os.unlink(tmp_file)

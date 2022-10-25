'''Classes for files published to S3'''

import binascii
import gzip
import hashlib
import mimetypes

from datetime import datetime
from os import path

mimetypes.init()  # must initialize mimetypes


def remove_prefix(text, prefix):
    '''
    Returns a copy of text with the given prefix removed.

    >>> remove_prefix('/ab/cd/ef', '/ab/cd')
    '/ef'

    >>> remove_prefix('abcd', '/ef')
    'abcd'
    '''
    if text.startswith(prefix):
        return text[len(prefix):]
    return text


class SiteObject():
    '''
    An abstract class for an individual object that can be uploaded to S3
    '''

    def __init__(self, filename, md5, site_prefix='', dir_prefix=''):
        self.filename = filename
        self.md5 = md5
        self.dir_prefix = dir_prefix
        self.site_prefix = site_prefix

    @property
    def s3_key(self):
        '''The object's key in the S3 bucket'''
        filename = self.filename
        if self.dir_prefix:
            filename = remove_prefix(filename,
                                     path.join(self.dir_prefix, ''))
        return f'{self.site_prefix}/{filename}'

    def upload_to_s3(self, bucket, s3_client):
        '''Upload this object to S3'''
        raise NotImplementedError  # should be implemented in child classes

    def delete_from_s3(self, bucket, s3_client):
        '''Delete this object from S3'''
        s3_client.delete_object(
            Bucket=bucket,
            Key=self.s3_key,
        )


class SiteFile(SiteObject):
    '''A file produced during a site build'''

    GZIP_EXTENSIONS = ['html', 'css', 'js', 'json', 'svg']

    def __init__(self, filename, dir_prefix, site_prefix, cache_control):
        super().__init__(filename=filename,
                         md5=None,
                         dir_prefix=dir_prefix,
                         site_prefix=site_prefix)
        self._compress()
        self.md5 = self.generate_md5()
        self.cache_control = cache_control

    @property
    def is_compressible(self):
        '''Whether the file should be compressed'''
        _, file_extension = path.splitext(self.filename)
        # file_extension has a preceding '.' character, so use substring
        return file_extension[1:].lower() in self.GZIP_EXTENSIONS

    @property
    def content_encoding(self):
        '''"gzip" if the file is compressible, otherwise None'''
        if self.is_compressible:
            return 'gzip'
        return None

    @property
    def content_type(self):
        '''The best-guess mimetype of the file'''
        content_type, _ = mimetypes.guess_type(self.filename)
        return content_type

    @property
    def is_compressed(self):
        '''Checks to see if the file is already compressed'''
        with open(self.filename, 'rb') as test_f:
            # '1f8b' is the magic flag that gzipped files start with
            return binascii.hexlify(test_f.read(2)) == b'1f8b'

    def generate_md5(self):
        '''Generates an md5 hash of the file contents'''
        hash_md5 = hashlib.md5()  # nosec

        with open(self.filename, 'rb') as file:
            for chunk in iter(lambda: file.read(4096), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()

    def _compress(self):
        '''GZips the file in-situ'''

        if not self.is_compressible:
            # shouldn't be compressed, so return
            return

        if self.is_compressed:
            # already compressed, so return
            return

        # otherwise, gzip the file in place
        with open(self.filename, 'rb') as f_in:
            contents = f_in.read()
            # Spoof the modification time so that MD5 hashes match next time
            spoofed_mtime = datetime(2014, 3, 19).timestamp()  # March 19, 2014
            # Compress the contents and save over the original file
            with gzip.GzipFile(self.filename, mode='wb',
                               mtime=spoofed_mtime) as gz_file:
                gz_file.write(contents)

    def upload_to_s3(self, bucket, s3_client):
        extra_args = {
            "CacheControl": self.cache_control,
            "ServerSideEncryption": "AES256",
        }

        if self.content_encoding:
            extra_args["ContentEncoding"] = self.content_encoding
        if self.content_type:
            extra_args["ContentType"] = self.content_type

        s3_client.upload_file(
            Filename=self.filename,
            Bucket=bucket,
            Key=self.s3_key,
            # For allowed ExtraArgs, see
            # https://boto3.readthedocs.io/en/latest/reference/customizations/s3.html#boto3.s3.transfer.S3Transfer.ALLOWED_UPLOAD_ARGS
            ExtraArgs=extra_args,
        )


class SiteRedirect(SiteObject):
    '''
    A redirect, typically from `/path/to/page => /path/to/page/`
    '''

    def __init__(self, filename, dir_prefix, site_prefix, base_url, cache_control):
        super().__init__(filename=filename,
                         dir_prefix=dir_prefix,
                         md5=None,  # update after super().__init()__
                         site_prefix=site_prefix)

        self.base_url = base_url
        self.cache_control = cache_control

        # The md5 hash is the hash of the destination string, not
        # of the file contents, for our redirect objects
        self.md5 = hashlib.md5(self.destination.encode()).hexdigest()  # nosec

    @property
    def destination(self):
        '''The destination of the redirect object'''
        filename = self.filename

        if self.dir_prefix:
            if filename == self.dir_prefix:
                return f'{self.base_url}/'

            filename = remove_prefix(filename,
                                     path.join(self.dir_prefix, ''))

        return f'{self.base_url}/{filename}/'

    @property
    def s3_key(self):
        filename = self.filename

        if self.dir_prefix:
            if filename == self.dir_prefix:
                # then this is 'root' site redirect object
                # (ie, the main index.html file)
                return self.site_prefix

            filename = remove_prefix(filename,
                                     path.join(self.dir_prefix, ''))

        return f'{self.site_prefix}/{filename}'

    def upload_to_s3(self, bucket, s3_client):
        '''Uploads the redirect object to S3'''
        s3_client.put_object(
            Body=self.destination,
            Bucket=bucket,
            Key=self.s3_key,
            ServerSideEncryption='AES256',
            WebsiteRedirectLocation=self.destination,
            CacheControl=self.cache_control
        )

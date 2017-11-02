'''
Classes and methods for publishing a directory to S3
'''

import glob
import hashlib
import gzip
import mimetypes
import binascii

from os import path
from datetime import datetime

import boto3

from logs import logging

LOGGER = logging.getLogger('S3_PUBLISHER')

mimetypes.init()  # must initialize mimetypes

def remove_prefix(text, prefix):
    '''Returns a copy of text with the given prefix removed'''
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

    def upload_to_s3(self, bucket, s3_client, dry_run=False):
        '''Upload this object to S3'''
        raise NotImplementedError  # should be implemented in child classes

    def delete_from_s3(self, bucket, s3_client, dry_run=False):
        '''Delete this object from S3'''
        start_time = datetime.now()

        if dry_run:
            LOGGER.info(f'Dry run deleting {self.s3_key}')
        else:
            LOGGER.info(f'Deleting {self.s3_key}')
            s3_client.delete_object(
                Bucket=bucket,
                Key=self.s3_key,
            )

        delta = datetime.now() - start_time
        LOGGER.info(f'Deleted {self.s3_key} in {delta.total_seconds():.2f}s')


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
        hash_md5 = hashlib.md5()

        with open(self.filename, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
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

    def upload_to_s3(self, bucket, s3_client, dry_run=False):
        start_time = datetime.now()

        if dry_run:
            LOGGER.info(f'Dry-run uploading {self.s3_key}')
            # don't actually upload anything
        else:
            LOGGER.info(f'Uploading {self.s3_key}')

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

        delta = datetime.now() - start_time
        LOGGER.info(f'Uploaded {self.s3_key} in {delta.total_seconds():.2f}s')


class SiteRedirect(SiteObject):
    '''
    A redirect, typically from `/path/to/page => /path/to/page/`
    '''

    def __init__(self, filename, dir_prefix, site_prefix, base_url):
        super().__init__(filename=filename,
                         dir_prefix=dir_prefix,
                         md5=None,  # update after super().__init()__
                         site_prefix=site_prefix)

        self.base_url = base_url
        self.md5 = hashlib.md5(self.destination.encode()).hexdigest()

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

    def upload_to_s3(self, bucket, s3_client, dry_run=False):
        '''Uploads the redirect object to S3'''

        start_time = datetime.now()

        if dry_run:
            LOGGER.info(f'Dry-run uploading redirect object {self.s3_key}')
            # Don't actually upload anything
        else:
            LOGGER.info(f'Uploading redirect object {self.s3_key}')
            s3_client.put_object(
                Body=self.destination,
                Bucket=bucket,
                Key=self.s3_key,
                ServerSideEncryption='AES256',
                WebsiteRedirectLocation=self.destination,
            )

        delta = datetime.now() - start_time
        LOGGER.info(f'Uploaded redirect object {self.s3_key} in {delta.total_seconds():.2f}s')


def list_remote_objects(bucket, site_prefix, s3_client):
    '''
    Generates a list of remote S3 objects that have keys starting with
    site_preix in the given bucket.
    '''
    results_truncated = True
    continuation_token = None

    remote_objects = []

    while results_truncated:
        request_kwargs = {
            'Bucket': bucket,
            'MaxKeys': 1000,
            'Prefix': site_prefix,
        }

        if continuation_token:
            request_kwargs['ContinuationToken'] = continuation_token

        response = s3_client.list_objects_v2(**request_kwargs)

        contents = response.get('Contents')
        if not contents:
            return remote_objects

        for response_obj in contents:
            # remove the site_prefix from the key
            filename = remove_prefix(response_obj['Key'], site_prefix)

            # remove initial slash if present
            filename = remove_prefix(filename, '/')

            # the etag comes surrounded by double quotes, so remove them
            md5 = response_obj['ETag'].replace('"', '')

            site_obj = SiteObject(filename=filename, md5=md5,
                                  site_prefix=site_prefix)
            remote_objects.append(site_obj)

        results_truncated = response['IsTruncated']
        if results_truncated:
            continuation_token = response['NextContinuationToken']

    return remote_objects


def publish_to_s3(directory, base_url, site_prefix, bucket, cache_control,
                  aws_region, access_key_id, secret_access_key, dry_run=False):
    '''Publishes the given directory to S3'''

    # TODO: BUG: _might_ have an extra redirect obj
    # present: ./tmp/site_repo/_site

    # With glob, dotfiles are ignored by default
    # Note that the filenames will include the `directory` prefix
    # but we won't want that for the eventual S3 keys
    files_and_dirs = glob.glob(path.join(directory, '**', '*'),
                               recursive=True)

    # Collect a list of all files in the specified directory
    local_files = []
    for filename in files_and_dirs:
        if path.isfile(filename):
            site_file = SiteFile(filename=filename,
                                 dir_prefix=directory,
                                 site_prefix=site_prefix,
                                 cache_control=cache_control)
            local_files.append(site_file)

    # Create a list of redirects from the local files
    local_redirects = []
    for site_file in local_files:
        if path.basename(site_file.filename) == 'index.html':
            redirect_filename = path.dirname(site_file.filename)
            site_redirect = SiteRedirect(filename=redirect_filename,
                                         dir_prefix=directory,
                                         site_prefix=site_prefix,
                                         base_url=base_url)
            local_redirects.append(site_redirect)

    # Combined list of local objects
    local_objects = local_files + local_redirects

    # Create an S3 client
    s3_client = boto3.client(
        service_name='s3',
        region_name=aws_region,
        aws_access_key_id=access_key_id,
        aws_secret_access_key=secret_access_key)

    # Get list of remote files
    remote_objects = list_remote_objects(bucket=bucket,
                                         site_prefix=site_prefix,
                                         s3_client=s3_client)

    # Make dicts by filename of local and remote objects for easier searching
    remote_objects_by_filename = {}
    for obj in remote_objects:
        # these will not have the `directory` prefix that our local
        # files do, so add it so we can more easily compare them
        filename = path.join(directory, obj.filename)
        if not obj.filename:
            # Special case where a blank remote filename is the site "root"
            # redirect object, which we don't want to have a trailing slash.
            # Instead, it will just have an S3 key name of `directory`.
            filename = directory
        remote_objects_by_filename[filename] = obj

    local_objects_by_filename = {}
    for obj in local_objects:
        local_objects_by_filename[obj.filename] = obj

    # Create lists of all the new and modified objects
    new_objects = []
    modified_objects = []
    for local_filename, local_obj in local_objects_by_filename.items():
        matching_remote_obj = remote_objects_by_filename.get(local_filename)
        if not matching_remote_obj:
            new_objects.append(local_obj)
        elif matching_remote_obj.md5 != local_obj.md5:
            modified_objects.append(local_obj)

    # Create a list of the remote objects that should be deleted
    deletion_objects = []
    for remote_filename, remote_obj in remote_objects_by_filename.items():
        if not local_objects_by_filename.get(remote_filename):
            deletion_objects.append(remote_obj)

    LOGGER.info('Preparing to upload')
    LOGGER.info(f'New: {len(new_objects)}')
    LOGGER.info(f'Modified: {len(modified_objects)}')
    LOGGER.info(f'Deleted: {len(deletion_objects)}')

    # Upload new files
    for file in new_objects:
        file.upload_to_s3(bucket, s3_client, dry_run)

    # Upload modified files
    for file in modified_objects:
        file.upload_to_s3(bucket, s3_client, dry_run)

    # Delete files not needed any more
    for file in deletion_objects:
        file.delete_from_s3(bucket, s3_client, dry_run)

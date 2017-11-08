'''
Classes and methods for publishing a directory to S3
'''

import glob

from os import path
from datetime import datetime

import boto3

from log_utils import logging

from .SiteObject import (remove_prefix, SiteObject, SiteFile, SiteRedirect)

LOGGER = logging.getLogger('S3_PUBLISHER')



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

    total_start_time = datetime.now() # To report publish time

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
        # These will not have the `directory` prefix that our local
        # files do, so add it so we can more easily compare them.
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

    # Upload new and modified files
    upload_objects = new_objects + modified_objects
    for file in upload_objects:
        if dry_run:
            LOGGER.info(f'Dry-run uploading {file.s3_key}')
        else:
            LOGGER.info(f'Uploading {file.s3_key}')
            start_time = datetime.now()

            file.upload_to_s3(bucket, s3_client)

            delta = datetime.now() - start_time
            LOGGER.info(f'Uploaded {file.s3_key} in {delta.total_seconds():.2f}s')


    # Delete files not needed any more
    for file in deletion_objects:
        if dry_run:
            LOGGER.info(f'Dry run deleting {file.s3_key}')
        else:
            start_time = datetime.now()
            LOGGER.info(f'Deleting {file.s3_key}')

            file.delete_from_s3(bucket, s3_client)

            delta = datetime.now() - start_time
            LOGGER.info(
                f'Deleted {file.s3_key} in {delta.total_seconds():.2f}s')

    total_delta = datetime.now() - total_start_time
    LOGGER.info(f'Total time to publish: {total_delta.total_seconds():.2f}s')

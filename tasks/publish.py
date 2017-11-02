'''
Publish tasks and helpers
'''
from invoke import task

from .common import (CLONE_DIR_PATH, SITE_BUILD_DIR,
                     WORKING_DIR, SITE_BUILD_DIR_PATH,
                     clean)

from logs import logging

from s3publisher import publish_to_s3

LOGGER = logging.getLogger('PUBLISH')

@task
def publish(ctx, base_url, site_prefix, bucket, cache_control,
            aws_region, access_key_id, secret_access_key,
            dry_run=False):
    # TODO: is base_url actually required?
    # TODO: create my own bucket in cloud.gov for testing
    LOGGER.info('Publishing to S3')

    publish_to_s3(
        directory=SITE_BUILD_DIR_PATH,
        base_url=base_url,
        site_prefix=site_prefix,
        bucket=bucket,
        cache_control=cache_control,
        aws_region=aws_region,
        access_key_id=access_key_id,
        secret_access_key=secret_access_key,
        dry_run=dry_run
    )

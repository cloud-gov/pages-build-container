'''
Publish tasks and helpers
'''
import os

from datetime import datetime

import boto3
from invoke import task

from publishing import s3publisher

from log_utils import get_logger
from log_utils.load_dotenv import load_dotenv
from log_utils.delta_to_mins_secs import delta_to_mins_secs
from .common import CLONE_DIR_PATH, SITE_BUILD_DIR_PATH


@task
def publish(ctx, base_url, site_prefix, bucket, cache_control,
            aws_region, dry_run=False):
    '''
    Publish the built site to S3.

    Expects AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY to be
    in the environment.
    '''
    load_dotenv()
    LOGGER = get_logger('PUBLISH')

    LOGGER.info('Publishing to S3')

    access_key_id = os.environ['AWS_ACCESS_KEY_ID']
    secret_access_key = os.environ['AWS_SECRET_ACCESS_KEY']

    start_time = datetime.now()

    s3_client = boto3.client(
        service_name='s3',
        region_name=aws_region,
        aws_access_key_id=access_key_id,
        aws_secret_access_key=secret_access_key)

    s3publisher.publish_to_s3(
        directory=str(SITE_BUILD_DIR_PATH),
        base_url=base_url,
        site_prefix=site_prefix,
        bucket=bucket,
        cache_control=cache_control,
        s3_client=s3_client,
        clone_dir=str(CLONE_DIR_PATH),
        dry_run=dry_run
    )

    delta_string = delta_to_mins_secs(datetime.now() - start_time)
    LOGGER.info(f'Total time to publish: {delta_string}')

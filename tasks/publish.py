'''
Publish tasks and helpers
'''
from datetime import datetime
import boto3
from invoke import task

from publishing import s3publisher

from log_utils import delta_to_mins_secs
from .common import CLONE_DIR_PATH, SITE_BUILD_DIR_PATH


@task
def publish(ctx, base_url, site_prefix, bucket, cache_control,
            aws_region, dry_run=False):
    '''
    Publish the built site to S3.

    Requires environment variables: AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY
    '''

    print('Publishing to S3')

    start_time = datetime.now()

    s3_client = boto3.client(service_name='s3', region_name=aws_region)

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
    print(f'Total time to publish: {delta_string}')

'''
Publish tasks and helpers
'''
from datetime import datetime

from publishing import s3publisher

from log_utils import delta_to_mins_secs, get_logger
from common import SITE_BUILD_DIR_PATH


def publish(base_url, site_prefix, bucket, federalist_config,
            s3_client, dry_run=False):
    '''
    Publish the built site to S3.
    '''
    logger = get_logger('publish')

    logger.info('Publishing to S3')

    start_time = datetime.now()

    s3publisher.publish_to_s3(
        directory=str(SITE_BUILD_DIR_PATH),
        base_url=base_url,
        site_prefix=site_prefix,
        bucket=bucket,
        federalist_config=federalist_config,
        s3_client=s3_client,
        dry_run=dry_run
    )

    delta_string = delta_to_mins_secs(datetime.now() - start_time)
    logger.info(f'Total time to publish: {delta_string}')

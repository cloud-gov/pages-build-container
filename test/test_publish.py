from unittest.mock import Mock

from steps import publish
from common import SITE_BUILD_DIR_PATH


TEST_BUCKET = 'test-bucket'
TEST_REGION = 'test-region'
TEST_ACCESS_KEY = 'fake-access-key'
TEST_SECRET_KEY = 'fake-secret-key'


class TestPublish():
    def test_it_calls_publish_to_s3(self, monkeypatch):
        mock_publish_to_s3 = Mock()
        monkeypatch.setattr('publishing.s3publisher.publish_to_s3',
                            mock_publish_to_s3)

        kwargs = dict(
            base_url='/site/prefix',
            site_prefix='site/prefix',
            bucket=TEST_BUCKET,
            federalist_config={},
            s3_client=None
        )

        publish(**kwargs)

        mock_publish_to_s3.assert_called_once()

        # check that the `directory` kwarg is a string, not a Path
        _, actual_kwargs = mock_publish_to_s3.call_args_list[0]
        assert type(actual_kwargs['directory']) == str
        assert actual_kwargs['directory'] == str(SITE_BUILD_DIR_PATH)

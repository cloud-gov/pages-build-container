import hashlib

from unittest.mock import Mock

import pytest

from publishing.models import SiteObject, SiteFile, SiteRedirect


class TestSiteObject():
    def test_constructor(self):
        model = SiteObject(
            filename='boop',
            md5='md5',
            dir_prefix='dir_prefix',
            site_prefix='site_prefix',
        )
        assert model is not None

        # default params are used
        model = SiteObject(filename='boop2', md5='abc')
        assert model is not None
        assert model.dir_prefix == ''
        assert model.site_prefix == ''

    def test_s3_key(self):
        model = SiteObject('abc', 'md5', site_prefix='site')
        assert model.s3_key == 'site/abc'

        model = SiteObject('/dir/abc', 'md5',
                           dir_prefix='/dir', site_prefix='site')
        assert model.s3_key == 'site/abc'

        model = SiteObject('/not_dir/abc', 'md5',
                           dir_prefix='/dir', site_prefix='site')
        assert model.s3_key == 'site//not_dir/abc'

    def test_upload_to_s3(self):
        model = SiteObject('abc', 'md5')
        # Base SiteObject should not have this method implemented
        # because it is specific to file and redirect objects
        with pytest.raises(NotImplementedError):
            model.upload_to_s3('bucket', None)

    def test_delete_from_s3(self):
        s3_client = Mock()

        model = SiteObject('/dir/abc', 'md5',
                           dir_prefix='/dir', site_prefix='site')
        model.delete_from_s3('test-bucket', s3_client)
        s3_client.delete_object.assert_called_once_with(
            Bucket='test-bucket',
            Key='site/abc')


class TestSiteFile():
    @pytest.mark.parametrize('filename, is_compressible', [
        ('test_file.html', True),
        ('test_file.css', True),
        ('test_file.js', True),
        ('test_file.json', True),
        ('test_file.svg', True),
        ('test_file.txt', False),
        ('test_file.exe', False),
    ])
    def test_is_compressible(self, tmpdir, filename, is_compressible):
        test_dir = tmpdir.mkdir('a_dir')
        test_file = test_dir.join(filename)
        test_file.write('something something')
        model = SiteFile(
            filename=str(test_file),
            dir_prefix=str(test_dir),
            site_prefix='/site',
            cache_control='max-age=60')
        assert model.is_compressible == is_compressible

    def test_non_compressible_file(self, tmpdir):
        test_dir = tmpdir.mkdir('boop')
        test_file = test_dir.join('test_file.txt')
        test_file.write('content')
        model = SiteFile(
            filename=str(test_file),
            dir_prefix=str(test_dir),
            site_prefix='/site',
            cache_control='max-age=60')

        assert model is not None

        # hardcoded md5 hash of 'content'
        assert model.md5 == '9a0364b9e99bb480dd25e1f0284c8555'
        assert model.s3_key == '/site/test_file.txt'
        assert model.dir_prefix == str(test_dir)
        assert model.content_encoding is None
        assert model.content_type == 'text/plain'

        # Make sure uploads is called correctly
        s3_client = Mock()
        model.upload_to_s3('test-bucket', s3_client)
        s3_client.upload_file.assert_called_once_with(
            Filename=str(test_file),
            Bucket='test-bucket',
            Key='/site/test_file.txt',
            ExtraArgs={
                'CacheControl': 'max-age=60',
                'ServerSideEncryption': 'AES256',
                'ContentType': 'text/plain',
            },
        )

    def test_compressible_file(self, tmpdir):
        test_dir = tmpdir.mkdir('boop')

        # .html files are compressible
        test_file = test_dir.join('test_file.html')
        test_file.write('content')
        model = SiteFile(
            filename=str(test_file),
            dir_prefix=str(test_dir),
            site_prefix='/site',
            cache_control='max-age=60')

        assert model is not None
        assert model.is_compressible is True
        assert model.is_compressed is True

        # hardcoded md5 hash of compressed 'content'
        assert model.md5 == 'f3900f9f80fac3c6ee8e077d6b172568'
        assert model.s3_key == '/site/test_file.html'
        assert model.dir_prefix == str(test_dir)
        assert model.content_encoding == 'gzip'
        assert model.content_type == 'text/html'

        # Make sure upload is called correctly
        s3_client = Mock()
        model.upload_to_s3('test-bucket', s3_client)
        s3_client.upload_file.assert_called_once_with(
            Filename=str(test_file),
            Bucket='test-bucket',
            Key='/site/test_file.html',
            ExtraArgs={
                'CacheControl': 'max-age=60',
                'ServerSideEncryption': 'AES256',
                'ContentType': 'text/html',
                'ContentEncoding': 'gzip',
            },
        )


class TestSiteRedirect():
    def test_contructor_and_props(self, tmpdir):
        base_test_dir = tmpdir.mkdir('boop')
        test_dir = base_test_dir.mkdir('sub_dir')

        model = SiteRedirect(
            filename=str(test_dir),
            dir_prefix=str(base_test_dir),
            site_prefix='prefix',
            base_url='/preview'
        )

        assert model is not None

        expected_dest = '/preview/sub_dir/'
        assert model.md5 == hashlib.md5(expected_dest.encode()).hexdigest()
        assert model.destination == expected_dest
        assert model.s3_key == 'prefix/sub_dir'

        # try with empty dir_prefix
        model.dir_prefix = ''
        assert model.destination == f'/preview/{test_dir}/'
        assert model.s3_key == f'prefix/{test_dir}'

        # and when we're dealing with the "root" redirect object
        # ie, filename and dir_prefix are the same
        model.filename = str(base_test_dir)
        model.dir_prefix = str(base_test_dir)
        assert model.destination == '/preview/'
        assert model.s3_key == 'prefix'

    def test_upload_to_s3(self, tmpdir):
        base_test_dir = tmpdir.mkdir('boop')
        test_dir = base_test_dir.mkdir('wherever')

        model = SiteRedirect(
            filename=str(test_dir),
            dir_prefix=str(base_test_dir),
            site_prefix='site-prefix',
            base_url='/site/test'
        )

        s3_client = Mock()
        model.upload_to_s3('test-bucket', s3_client)

        expected_dest = '/site/test/wherever/'

        s3_client.put_object.assert_called_once_with(
            Body=expected_dest,
            Bucket='test-bucket',
            Key='site-prefix/wherever',
            ServerSideEncryption='AES256',
            WebsiteRedirectLocation=expected_dest
        )

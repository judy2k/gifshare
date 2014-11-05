# -*- coding: utf-8 -*-

import unittest
from nose.tools import assert_raises
from mock import MagicMock, patch, call, ANY

from six.moves.configparser import ConfigParser

from .util import *

import gifshare.s3


defaults = {
    'aws_access_id': 'dummy-access-id',
    'aws_secret_access_key': 'dummy-secret-access-key',
    'web_root': 'http://dummy.web.root/',
    'region': 'dummy-region',
    'bucket': 'not.a.bucket',
}


def dummy_get(_, key):
    return defaults[key]


config_stub = MagicMock(spec=ConfigParser)
config_stub.get.side_effect = dummy_get


class DummyKey(object):
    def __init__(self, name):
        self.name = name


class TestBucket(unittest.TestCase):
    def test_bucket(self):
        # Patch S3Connection and its get_bucket method:
        with patch('gifshare.s3.S3Connection',
                   name='S3Connection') as MockS3Connection:
            mock_get_bucket = MagicMock(name='get_bucket')
            MockS3Connection.return_value.get_bucket = mock_get_bucket

            self.bucket = gifshare.s3.Bucket(config_stub)
            _ = self.bucket.bucket

            # Ensure the config is passed correctly to S3Connection
            # and get_bucket:
            MockS3Connection.assert_called_with(
                'dummy-access-id', 'dummy-secret-access-key')
            mock_get_bucket.assert_called_with('not.a.bucket')

    def test_key_for(self):
        with patch('gifshare.s3.S3Connection',
                   name='S3Connection'):
            with patch('gifshare.s3.Key') as key_mock:
                self.bucket = gifshare.s3.Bucket(config_stub)
                k = self.bucket.key_for('abc.gif', 'image/gif')
                key_mock.assert_called_with(self.bucket.bucket, 'abc.gif')
                self.assertEqual(k.content_type, 'image/gif')

    def test_list(self):
        # Patch S3Connection and its get_bucket method:
        with patch('gifshare.s3.S3Connection',
                   name='S3Connection') as MockS3Connection:
            mock_get_bucket = MagicMock(name='get_bucket')
            mock_bucket = MagicMock(name='bucket')
            mock_get_bucket.return_value = mock_bucket
            mock_bucket.list.return_value = [
                DummyKey('image1.jpeg'),
                DummyKey('image2.jpeg')
            ]
            MockS3Connection.return_value.get_bucket = mock_get_bucket

            self.bucket = gifshare.s3.Bucket(config_stub)
            keys = list(self.bucket.list())

            self.assertEqual(keys, [
                'http://dummy.web.root/image1.jpeg',
                'http://dummy.web.root/image2.jpeg',
            ])

            MockS3Connection.assert_called_with(
                'dummy-access-id', 'dummy-secret-access-key')
            mock_get_bucket.assert_called_with('not.a.bucket')
            mock_bucket.list.assert_called_once_with()

    def test_upload_file(self):
        key_stub = MagicMock(name='Key')
        key_stub.exists.return_value = False
        self.bucket = gifshare.s3.Bucket(config_stub)
        self.bucket.key_for = MagicMock(name='key_for', return_value=key_stub)

        url = self.bucket.upload_file('test_image.png', 'image/png', image_path('png'))
        key_stub.set_contents_from_filename.assert_called_once_with(
            os.path.abspath(image_path('png')),
            cb=ANY
        )

    def test_upload_contents(self):
        key_stub = MagicMock(name='Key')
        key_stub.exists.return_value = False
        self.bucket = gifshare.s3.Bucket(config_stub)
        self.bucket.key_for = MagicMock(name='key_for', return_value=key_stub)

        image_data = load_image('png')

        with patch('gifshare.core.download_file', return_value=image_data):
            dest_url = self.bucket.upload_contents(
                'thing.png',
                'image/png',
                image_data
            )
            key_stub.set_contents_from_string.assert_called_once_with(
                image_data,
                cb=ANY
            )
            self.assertEqual(dest_url, 'http://dummy.web.root/thing.png')

    def test_upload_url_existing_file(self):
        key_stub = MagicMock(name='thing.png')
        key_stub.exists.return_value = True
        self.bucket = gifshare.s3.Bucket(config_stub)
        self.bucket.key_for = MagicMock(name='key_for', return_value=key_stub)

        image_data = load_image('png')

        with patch('gifshare.core.download_file', return_value=image_data):
            with self.assertRaises(gifshare.exceptions.FileAlreadyExists):
                self.bucket.upload_contents(
                    'thing.png', 'image/png', image_data)
        self.assertFalse(key_stub.set_contents_from_string.called)

    def test_upload_existing_file(self):
        key_stub = MagicMock(name='Key')
        key_stub.exists.return_value = True
        self.bucket = gifshare.s3.Bucket(config_stub)
        self.bucket.key_for = MagicMock(name='key_for', return_value=key_stub)

        with assert_raises(gifshare.exceptions.FileAlreadyExists):
            self.bucket.upload_file('test_image', 'image/png', image_path('png'))

    def test_get_url(self):
        key_stub = MagicMock(name='Key')
        key_stub.exists.return_value = True
        self.bucket = gifshare.s3.Bucket(config_stub)
        self.bucket.key_for = MagicMock(name='key_for', return_value=key_stub)

        url = self.bucket.get_url('test.png')
        self.bucket.key_for.assert_called_with('test.png')
        self.assertEqual(key_stub.exists.call_count, 1)
        self.assertEqual(url, 'http://dummy.web.root/test.png')

    def test_missing_get_url(self):
        key_stub = MagicMock(name='Key')
        key_stub.exists.return_value = False
        self.bucket = gifshare.s3.Bucket(config_stub)
        self.bucket.key_for = MagicMock(name='key_for', return_value=key_stub)

        with self.assertRaises(gifshare.exceptions.MissingFile):
            self.bucket.get_url('test.png')

    def test_delete_existing(self):
        key_stub = MagicMock(name='Key')
        key_stub.exists.return_value = True
        self.bucket = gifshare.s3.Bucket(config_stub)
        self.bucket.key_for = MagicMock(name='key_for', return_value=key_stub)

        self.bucket.delete_file('/non-existant/image')
        key_stub.delete.assert_called_with()

    @patch('sys.stderr')    # Stops test-output polution.
    def test_delete_missing(self, stderr_stub):
        key_stub = MagicMock(name='Key')
        key_stub.exists.return_value = False
        self.bucket = gifshare.s3.Bucket(config_stub)
        self.bucket.key_for = MagicMock(name='key_for', return_value=key_stub)

        self.bucket.delete_file('/non-existant/image')
        key_stub.delete.assert_not_called()

    def test_grep(self):
        # Patch S3Connection and its get_bucket method:
        with patch('gifshare.s3.S3Connection',
                   name='S3Connection') as MockS3Connection:
            mock_get_bucket = MagicMock(name='get_bucket')
            mock_bucket = MagicMock(name='bucket')
            mock_get_bucket.return_value = mock_bucket
            mock_bucket.list.return_value = [
                DummyKey('bunny-image.jpeg'),
                DummyKey('kitten-image.jpeg'),
                DummyKey('my-kittenz.jpeg')
            ]
            MockS3Connection.return_value.get_bucket = mock_get_bucket

            self.bucket = gifshare.s3.Bucket(config_stub)
            results = list(self.bucket.grep('kitten'))
            self.assertEqual(results, [
                'http://dummy.web.root/kitten-image.jpeg',
                'http://dummy.web.root/my-kittenz.jpeg',
            ])


@patch('gifshare.s3.progressbar.ProgressBar')
class TestUploadCallback(unittest.TestCase):
    def test_upload_callback(self, progress_bar_mock):
        progress_bar_instance_mock = progress_bar_mock.return_value

        callback = gifshare.s3.upload_callback()
        progress_bar_mock.assert_not_called()
        callback(0, 100)
        progress_bar_mock.assert_called_with(widgets=ANY, maxval=100)

        progress_bar_instance_mock.start.assert_called_with()

    def test_callback_update(self, progress_bar_mock):
        progress_bar_instance_mock = progress_bar_mock.return_value

        callback = gifshare.s3.upload_callback()
        callback(0, 100)
        callback(50, 100)
        progress_bar_instance_mock.update.assert_called_with(50)

    def test_callback_finish(self, progress_bar_mock):
        progress_bar_instance_mock = progress_bar_mock.return_value
        callback = gifshare.s3.upload_callback()
        callback(0, 100)
        callback(100, 100)
        progress_bar_instance_mock.finish.assert_called_with()

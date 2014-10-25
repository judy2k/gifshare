# -*- coding: utf-8 -*-

import unittest
from nose.tools import assert_raises
from mock import MagicMock, patch, call, ANY

import os.path
from ConfigParser import ConfigParser

import gifshare


def _image_path(ext):
        here = os.path.dirname(__file__)
        return os.path.join(here, 'fixtures', 'test_image.{}'.format(ext))


defaults = {
    'aws_access_id': 'dummy-access-id',
    'aws_secret_access_key': 'dummy-secret-access-key',
    'web_root': 'http://dummy.web.root/',
    'region': 'dummy-region',
    'bucket': 'not.a.bucket',
}


class DummyKey(object):
    def __init__(self, name):
        self.name = name


def dummy_get(_, key):
    return defaults[key]


config_stub = MagicMock(spec=ConfigParser)
config_stub.get.side_effect = dummy_get


class TestBucket(unittest.TestCase):
    def setUp(self):
        self.bucket = gifshare.Bucket(config_stub)



    def test_bucket(self):
        # Patch S3Connection and its get_bucket method:
        with patch('gifshare.S3Connection',
                   name='S3Connection') as MockS3Connection:
            mock_get_bucket = MagicMock(name='get_bucket')
            MockS3Connection.return_value.get_bucket = mock_get_bucket

            _ = self.bucket.bucket

            # Ensure the config is passed correctly to S3Connection
            # and get_bucket:
            MockS3Connection.assert_called_with(
                'dummy-access-id', 'dummy-secret-access-key')
            mock_get_bucket.assert_called_with('not.a.bucket')

    def test_list(self):
        # Patch S3Connection and its get_bucket method:
        with patch('gifshare.S3Connection',
                   name='S3Connection') as MockS3Connection:
            mock_get_bucket = MagicMock(name='get_bucket')
            mock_bucket = MagicMock(name='bucket')
            mock_get_bucket.return_value = mock_bucket
            mock_bucket.list.return_value = [
                DummyKey('image1.jpeg'),
                DummyKey('image2.jpeg')
            ]
            MockS3Connection.return_value.get_bucket = mock_get_bucket

            keys = list(self.bucket.list())

            self.assertEqual(keys, [
                'http://dummy.web.root/image1.jpeg',
                'http://dummy.web.root/image2.jpeg',
            ])

            MockS3Connection.assert_called_with(
                'dummy-access-id', 'dummy-secret-access-key')
            mock_get_bucket.assert_called_with('not.a.bucket')
            mock_bucket.list.assert_called_once_with()

    @patch('gifshare.S3Connection', name='S3Connection')
    def test_upload_file(self, s3_connection_stub):
        key_stub = MagicMock(name='Key')
        key_stub.exists.return_value = False

        s3_con_instance = s3_connection_stub.return_value
        key_for_stub = MagicMock()
        key_for_stub.return_value = key_stub
        self.bucket.key_for = key_for_stub

        self.bucket.upload_file(_image_path('png'))
        key_stub.set_contents_from_filename.assert_called_once_with(
            os.path.abspath(_image_path('png')),
            cb=ANY
        )

    @patch('gifshare.S3Connection', name='S3Connection')
    def test_upload_missing_file(self, s3_connection_stub):
        with assert_raises(IOError):
            self.bucket.upload_file('/tmp/non-existent')


class TestExtensionDetection(unittest.TestCase):
    def _image_path(self, ext):
        here = os.path.dirname(__file__)
        return os.path.join(here, 'fixtures', 'test_image.{}'.format(ext))

    def _load_image(self, ext):
        return open(self._image_path(ext), 'rb').read()

    def test_jpeg_path(self):
        self.assertEqual(
            gifshare.correct_ext(self._image_path('jpeg')),
            'jpeg')

    def test_gif_path(self):
        self.assertEqual(
            gifshare.correct_ext(self._image_path('gif')),
            'gif')

    def test_png_path(self):
        self.assertEqual(
            gifshare.correct_ext(self._image_path('png')),
            'png')

    def test_jpeg(self):
        self.assertEqual(
            gifshare.correct_ext(self._load_image('jpeg'), True),
            'jpeg')

    def test_gif(self):
        self.assertEqual(
            gifshare.correct_ext(self._load_image('gif'), True),
            'gif')

    def test_png(self):
        self.assertEqual(
            gifshare.correct_ext(self._load_image('png'), True),
            'png')

    def test_unknown_type(self):
        with self.assertRaises(gifshare.UnknownFileType):
            gifshare.correct_ext(self._load_image('ico'), True)


class TestMiscellaneousFunctions(unittest.TestCase):
    @patch('gifshare.progressbar.ProgressBar')
    @patch('gifshare.requests')
    def test_download_file(self, requests_mock, progress_bar_stub):
        pbar_mock = MagicMock()
        progress_bar_stub.return_value.start.return_value = pbar_mock

        response_stub = MagicMock()
        response_stub.headers = {
            'content-length': 197
        }

        def iter_content_stub(_):
            for i in range(3):
                yield ' ' * 64
            yield ' ' * 5
        response_stub.iter_content = iter_content_stub
        requests_mock.get.return_value = response_stub
        gifshare.download_file('http://nonsense.url/')
        requests_mock.get.assert_called_with(
            'http://nonsense.url/', stream=True)
        pbar_mock.update.assert_has_calls([
            call(64), call(128), call(192), call(197)
        ])
        pbar_mock.finish.assert_called_once_with()

    def test_get_name_from_url(self):
        self.assertEqual(
            gifshare.get_name_from_url('http://some.domain/path/myfile.jpeg'),
            'myfile'
        )

        self.assertEqual(
            gifshare.get_name_from_url('http://some.domain/path/myfile.jpeg#.png'),
            'myfile'
        )

# -*- coding: utf-8 -*-

import unittest
from nose.tools import assert_raises
from mock import MagicMock, patch, call

import os.path
from ConfigParser import ConfigParser

import gifshare
import progressbar

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


class TestGifshare(unittest.TestCase):
    def setUp(self):
        pass

    def test_upload(self):
        pass

    def test_upload_missing_file(self):
        with assert_raises(IOError):
            gifshare.upload_file(config_stub, '/tmp/non-existent')


class TestBucket(unittest.TestCase):
    def setUp(self):
        self.bucket = gifshare.Bucket(config_stub)

    def test_bucket(self):
        # Patch S3Connection and its get_bucket method:
        with patch('gifshare.S3Connection',
                   name='S3Connection') as MockS3Connection:
            mock_get_bucket = MagicMock(name='get_bucket')
            MockS3Connection.return_value.get_bucket = mock_get_bucket

            my_bucket = self.bucket.bucket

            # Ensure the config is passed correctly to S3Connection
            # and get_bucket:
            MockS3Connection.assert_called_with(
                'dummy-access-id', 'dummy-secret-access-key')
            mock_get_bucket.assert_called_with('not.a.bucket')


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
    def test_download_file(self, requests_mock, ProgressBar):
        pbar_mock = MagicMock()
        ProgressBar.return_value.start.return_value = pbar_mock

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

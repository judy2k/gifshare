# -*- coding: utf-8 -*-

import unittest
from nose.tools import assert_raises
from mock import MagicMock, patch

import os.path
from ConfigParser import ConfigParser

import gifshare

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
        with patch(
                'gifshare.S3Connection', name='S3Connection') as S3Connection:
            get_bucket = MagicMock(name='get_bucket')
            S3Connection.return_value.get_bucket = get_bucket

            my_bucket = self.bucket.bucket

            # Ensure the config is passed correctly to S3Connection
            # and get_bucket:
            S3Connection.assert_called_with(
                'dummy-access-id', 'dummy-secret-access-key')
            get_bucket.assert_called_with('not.a.bucket')


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


class TestDownload(unittest.TestCase):
    def test_download_file(self):
        with patch('gifshare.requests') as requests_stub:
            gifshare.download_file('http://nonsense.url/')
            requests_stub.get.assert_called_with('http://nonsense.url/', stream=True)

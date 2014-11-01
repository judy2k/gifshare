# -*- coding: utf-8 -*-

from __future__ import absolute_import

import unittest
from nose.tools import assert_raises
from mock import MagicMock, patch, call, ANY

from .util import *

import gifshare


class TestGifShare(unittest.TestCase):
    def _configure_bucket_instance_mock(self):
        bucket_instance_mock = MagicMock(name='bucket_instance', spec=gifshare.s3.Bucket)
        bucket_instance_mock.upload_file.return_value = 'http://dummy.web.root/test_image.png'
        bucket_instance_mock.upload_contents.return_value = 'http://dummy.web.root/test_image.png'

        return bucket_instance_mock

    def test_upload_file(self):
        bucket = self._configure_bucket_instance_mock()
        gs = gifshare.core.GifShare(bucket)
        url = gs.upload_file(image_path('png'))
        bucket.upload_file.assert_called_with(
            u'test_image.png',
            u'image/png',
            image_path('png'),
            False
        )
        self.assertEqual(url, 'http://dummy.web.root/test_image.png')

    def test_upload_missing_file(self):
        bucket = self._configure_bucket_instance_mock()
        gs = gifshare.core.GifShare(bucket)
        with assert_raises(IOError):
            gs.upload_file('/tmp/non-existent')

    @patch('gifshare.core.download_file')
    def test_upload_url(self, download_file_stub):
        download_file_stub.return_value = load_image('png')
        bucket = self._configure_bucket_instance_mock()
        gs = gifshare.core.GifShare(bucket)
        url = gs.upload_url(image_path('png'))
        bucket.upload_contents.assert_called_with(
            u'test_image.png',
            u'image/png',
            load_image('png'),
            False
        )
        self.assertEqual(url, 'http://dummy.web.root/test_image.png')

    def test_delete_existing(self):
        bucket = self._configure_bucket_instance_mock()
        gs = gifshare.core.GifShare(bucket)

        gs.delete_file('/non-existent/image')
        bucket.delete_file.assert_called_with('/non-existent/image')

    def test_get_url(self):
        bucket = self._configure_bucket_instance_mock()
        bucket.get_url.return_value = 'http://dummy.web.root/test.png'
        gs = gifshare.core.GifShare(bucket)

        url = gs.get_url('test.png')
        bucket.get_url.assert_called_with('test.png')
        self.assertEqual(url, 'http://dummy.web.root/test.png')


class TestExtensionDetection(unittest.TestCase):
    def test_jpeg_path(self):
        self.assertEqual(
            gifshare.core.correct_ext(image_path('jpeg')),
            'jpeg')

    def test_gif_path(self):
        self.assertEqual(
            gifshare.core.correct_ext(image_path('gif')),
            'gif')

    def test_png_path(self):
        self.assertEqual(
            gifshare.core.correct_ext(image_path('png')),
            'png')

    def test_jpeg(self):
        self.assertEqual(
            gifshare.core.correct_ext(load_image('jpeg'), True),
            'jpeg')

    def test_gif(self):
        self.assertEqual(
            gifshare.core.correct_ext(load_image('gif'), True),
            'gif')

    def test_png(self):
        self.assertEqual(
            gifshare.core.correct_ext(load_image('png'), True),
            'png')

    def test_unknown_type(self):
        with self.assertRaises(gifshare.core.UnknownFileType):
            gifshare.core.correct_ext(load_image('ico'), True)


class TestMiscellaneousFunctions(unittest.TestCase):
    @patch('gifshare.core.progressbar.ProgressBar')
    @patch('gifshare.core.requests')
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
        gifshare.core.download_file('http://nonsense.url/')
        requests_mock.get.assert_called_with(
            'http://nonsense.url/', stream=True)
        pbar_mock.update.assert_has_calls([
            call(64), call(128), call(192), call(197)
        ])
        pbar_mock.finish.assert_called_once_with()

    def test_get_name_from_url(self):
        self.assertEqual(
            gifshare.core.get_name_from_url('http://some.domain/path/myfile.jpeg'),
            'myfile'
        )

        self.assertEqual(
            gifshare.core.get_name_from_url('http://some.domain/path/myfile.jpeg#.png'),
            'myfile'
        )

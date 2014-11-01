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

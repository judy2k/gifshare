# -*- coding: utf-8 -*-

import unittest
from nose.tools import assert_raises
from mock import MagicMock, patch, call, ANY

from .util import *
import gifshare.cli

config_stub = MagicMock()


class TestMain(unittest.TestCase):
    @patch('gifshare.cli.command_upload')
    def test_main_upload(self, cmd_upload):
        gifshare.cli.main(['upload', 'a-file'])
        self.assertEqual(cmd_upload.call_count, 1)

    @patch('gifshare.cli.command_list')
    def test_main_list(self, cmd_list):
        gifshare.cli.main(['list'])
        self.assertEqual(cmd_list.call_count, 1)

    @patch('gifshare.cli.command_list')
    def test_main_error(self, cmd_list):
        cmd_list.side_effect = gifshare.exceptions.UserException
        result = gifshare.cli.main(['list'])
        self.assertEqual(result, 1)

    @patch('gifshare.cli.load_config', return_value=config_stub)
    @patch('gifshare.cli.Bucket', spec=gifshare.cli.Bucket)
    def test_main_list_arguments(self, bucket_mock, load_config_stub):
        bucket_instance = MagicMock()
        bucket_mock.return_value = bucket_instance
        bucket_instance.list.return_value = [
            'http://dummy.web.root/image1.jpeg',
            'http://dummy.web.root/image2.jpeg',
        ]

        gifshare.cli.main(['list'])
        self.assertEqual(bucket_mock.call_args, call(config_stub))
        self.assertEqual(bucket_instance.list.call_count, 1)

    @patch('random.choice')
    @patch('gifshare.cli.load_config', return_value=config_stub)
    @patch('gifshare.cli.Bucket', spec=gifshare.cli.Bucket)
    def test_main_list_random(self, bucket_mock, load_config_stub, random_choice):
        bucket_instance = MagicMock()
        bucket_mock.return_value = bucket_instance
        bucket_instance.list.return_value = [
            'http://dummy.web.root/image1.jpeg',
            'http://dummy.web.root/image2.jpeg',
        ]

        gifshare.cli.main(['list', '-r'])
        bucket_init = bucket_mock.call_args
        self.assertEqual(bucket_init, call(config_stub))
        self.assertEqual(bucket_instance.list.call_count, 1)

        self.assertEqual(random_choice.call_count, 1)

    @patch('gifshare.cli.load_config', return_value=config_stub)
    @patch('gifshare.cli.Bucket', spec=gifshare.cli.Bucket)
    @patch('gifshare.core.download_file')
    def test_main_upload_url(self, download_file, bucket_mock, load_config_stub):
        download_file.return_value = load_image('png')

        gifshare.cli.main(['upload', 'http://probably.giphy/kittiez.png'])
        self.assertEqual(bucket_mock.call_args, call(config_stub))
        self.assertEqual(download_file.call_count, 1)

    @patch('gifshare.cli.load_config', return_value=config_stub)
    @patch('gifshare.cli.Bucket', spec=gifshare.cli.Bucket)
    def test_main_upload_file(self, bucket_mock, load_config_stub):
        gifshare.cli.main(['upload', image_path('png')])
        self.assertEqual(bucket_mock.call_args, call(config_stub))
        self.assertEqual(bucket_mock.return_value.upload_file.call_count, 1)

    @patch('gifshare.cli.load_config', return_value=config_stub)
    @patch('gifshare.cli.Bucket', spec=gifshare.cli.Bucket)
    def test_main_upload_missing_file(self, bucket_mock, load_config_stub):
        with self.assertRaises(IOError):
            gifshare.cli.main(['upload', '/tmp/non-existent.png'])
            self.assertEqual(bucket_mock.call_count, 0)

    @patch('gifshare.cli.load_config', return_value=config_stub)
    @patch('gifshare.cli.Bucket', spec=gifshare.cli.Bucket)
    def test_main_delete(self, bucket_mock, load_config_stub):
        result = gifshare.cli.main(['delete', 'my/file.png'])
        bucket_mock.return_value.delete_file.assert_called_with('my/file.png')
        self.assertEqual(result, 0)

    @patch('gifshare.cli.load_config', return_value=config_stub)
    @patch('gifshare.cli.Bucket', spec=gifshare.cli.Bucket)
    def test_main_expand(self, bucket_mock, load_config_stub):
        result = gifshare.cli.main(['expand', 'test.png'])
        bucket_mock.return_value.get_url.assert_called_with('test.png')
        self.assertEqual(result, 0)

    @patch('gifshare.cli.load_config', return_value=config_stub)
    @patch('gifshare.cli.Bucket', spec=gifshare.cli.Bucket)
    @patch('webbrowser.open_new')
    def test_main_show(self, open_new_mock, bucket_mock, load_config_stub):
        result = gifshare.cli.main(['show', 'test.png'])
        bucket_mock.return_value.get_url.assert_called_with('test.png')
        self.assertEqual(result, 0)

    @patch('gifshare.cli.load_config', return_value=config_stub)
    @patch('gifshare.cli.Bucket', spec=gifshare.cli.Bucket)
    def test_main_grep(self, bucket_mock, load_config_stub):
        bucket_mock.return_value.grep.return_value = [
            'http://dummy.web.root/image1.jpeg',
            'http://dummy.web.root/image2.jpeg',
        ]
        result = gifshare.cli.main(['grep', 'test'])
        bucket_mock.return_value.grep.assert_called_with('test')
        self.assertEqual(result, 0)

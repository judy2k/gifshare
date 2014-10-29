#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
gifshare - Share Gifs via Amazon S3
"""

from __future__ import print_function, absolute_import, unicode_literals

import argparse
from six.moves import configparser
import logging
from os.path import expanduser, isfile, basename, splitext
import random
import re
from six import StringIO
import sys

from boto.s3.key import Key
from boto.s3.connection import S3Connection

import magic
import progressbar
import requests


FOOTER = """
Copyright (c) 2014 by Mark Smith.
MIT Licensed, see LICENSE.txt for more details.
"""

__version__ = '0.0.3'


class UserException(Exception):
    """
    Indicates that the user should not see a stack-trace - just the
    exception message.
    """
    pass


class UnknownFileType(UserException):
    pass


class FileAlreadyExists(UserException):
    pass


URL_RE = re.compile(r'^http.*')
CONTENT_TYPE_MAP = {
    u'gif': u'image/gif',
    u'jpeg': u'image/jpeg',
    u'png': u'image/png',
}
LOG = logging.getLogger('gifshare')


def correct_ext(data, is_buffer=False):
    magic_output = magic.from_buffer(data) if is_buffer else magic.from_file(
        data)
    match = re.search(r'JPEG|GIF|PNG', magic_output.decode('utf-8'))
    if match:
        return match.group(0).lower()
    else:
        raise UnknownFileType("Unknown file type: {}".format(magic_output))


def load_config():
    config = configparser.SafeConfigParser()
    config.read([expanduser('~/.gifshare'), '.gifshare'])
    return config


def download_file(url):
    LOG.debug("Downloading image ...")
    response = requests.get(url, stream=True)
    length = int(response.headers['content-length'])
    LOG.debug('Content length: %d', length)
    content = StringIO()
    i = 0
    widgets = [
        'Downloading image ', progressbar.Bar(), progressbar.Percentage()]
    pbar = progressbar.ProgressBar(widgets=widgets, maxval=length).start()
    for chunk in response.iter_content(64):
        i += len(chunk)
        LOG.debug('Update: %d', i)
        content.write(chunk)
        pbar.update(i)
    pbar.finish()

    return content.getvalue()


def get_name_from_url(url):
    return re.match(r'.*/([^/\.]+)', url).group(1)


def upload_callback():
    pbar = [None]
    widgets = ['Uploading image ', progressbar.Bar(), progressbar.Percentage()]

    def callback(update, total):
        if pbar[0] is None:
            pbar[0] = progressbar.ProgressBar(widgets=widgets, maxval=total)
            pbar[0].start()
        else:
            pbar[0].update(update)
        if update == total:
            pbar[0].finish()

    return callback


class Bucket(object):
    def __init__(self, config):
        self._bucket = None
        self._key_id = config.get('default', 'aws_access_id')
        self._access_key = config.get('default', 'aws_secret_access_key')
        self._bucket_name = config.get('default', 'bucket')
        self._web_root = config.get('default', 'web_root')

    @property
    def bucket(self):
        if not self._bucket:
            conn = S3Connection(self._key_id, self._access_key)
            self._bucket = conn.get_bucket(self._bucket_name)
        return self._bucket

    def key_for(self, filename, content_type=None):
        k = Key(self.bucket, filename)
        k.content_type = content_type
        return k

    def list(self):
        bucket = self.bucket
        for key in bucket.list():
            url = self._web_root + key.name
            yield url

    def upload_file(self, filename, content_type, path, force=False):
        url = self._web_root + filename

        key = self.key_for(filename, content_type)
        if key.exists() and not force:
            raise FileAlreadyExists("File at {} already exists!".format(url))
        LOG.debug("Uploading image ...")
        key.set_contents_from_filename(path, cb=upload_callback())

        return url

    def upload_contents(self, filename, content_type, data, force=False):
        dest_url = self._web_root + filename
        key = self.key_for(filename, content_type)
        if key.exists() and not force:
            raise FileAlreadyExists(
                "File at {} already exists!".format(dest_url))
        LOG.debug("Uploading image ...")
        key.set_contents_from_string(data, cb=upload_callback())

        return dest_url

    def delete_file(self, remote_path):
        key = self.key_for(remote_path)
        if key.exists():
            key.delete()
        else:
            print("The image '%s' does not exist" % remote_path,
                  file=sys.stderr)


class GifShare(object):
    def __init__(self, bucket):
        self._bucket = bucket

    def upload_url(self, url, name=None, force=False):
        LOG.debug("Uploading URL '%s'", url)
        data = download_file(url)
        ext = correct_ext(data, True)
        content_type = CONTENT_TYPE_MAP[ext]
        filename = (name or get_name_from_url(url)) + '.' + ext

        return self._bucket.upload_contents(
            filename, content_type, data, force)

    def upload_file(self, path, name=None, force=False):
        LOG.debug("Uploading file '%s'", path)
        ext = correct_ext(path)
        filename = (name or splitext(basename(path))[0]) + '.' + ext
        content_type = CONTENT_TYPE_MAP[ext]
        return self._bucket.upload_file(filename, content_type, path, force)

    def delete_file(self, remote_path):
        self._bucket.delete_file(remote_path)


def command_upload(arguments, config):
    path = arguments.path
    if not URL_RE.match(path):
        if isfile(path):
            print(GifShare(Bucket(config)).upload_file(
                path, arguments.key, force=arguments.force))
        else:
            raise IOError(
                '{} does not exist or is not a file!'.format(path))
    else:
        print(GifShare(Bucket(config)).upload_url(
            path, arguments.key, force=arguments.force))


def command_list(arguments, config):
    bucket = Bucket(config)
    if not arguments.random:
        for item in bucket.list():
            print(item)
    else:
        print(random.choice(list(bucket.list())))


def command_delete(arguments, config):
    bucket = Bucket(config)
    bucket.delete_file(arguments.path)


def main(argv=sys.argv[1:]):
    try:
        a_parser = argparse.ArgumentParser(description=__doc__, epilog=FOOTER)
        a_parser.add_argument(
            '--version',
            action='version',
            version='%(prog)s ' + __version__)

        a_parser.add_argument(
            '-v', '--verbose',
            action='store_true',
            help='print out more stuff')

        subparsers = a_parser.add_subparsers()

        upload_parser = subparsers.add_parser(
            "upload",
            help="Upload an image to your bucket."
        )
        upload_parser.set_defaults(target=command_upload)

        upload_parser.add_argument(
            '--force', '-f',
            action='store_true',
            default=False,
            help='Overwrite any existing files if necessary.')

        upload_parser.add_argument(
            'path',
            help='The path to a file to upload')

        upload_parser.add_argument(
            'key',
            nargs='?',
            help='A nice filename for the gif.')

        list_parser = subparsers.add_parser(
            "list",
            help="List images stored in your bucket."
        )
        list_parser.add_argument(
            '-r', '--random',
            action='store_true',
            help='Display a single random image URL.'
        )
        list_parser.set_defaults(target=command_list)

        delete_parser = subparsers.add_parser(
            "delete",
            help="Delete a file in your bucket."
        )
        delete_parser.add_argument(
            "path",
            help="The path to a file to delete"
        )
        delete_parser.set_defaults(target=command_delete)

        arguments = a_parser.parse_args(argv)
        config = load_config()

        logging.basicConfig()
        LOG.setLevel(
            level=logging.DEBUG if arguments.verbose else logging.WARN)

        arguments.target(arguments, config)
        return 0
    except UserException as user_exception:
        print(user_exception, file=sys.stderr)
        return 1


if __name__ == '__main__':
    sys.exit(main())

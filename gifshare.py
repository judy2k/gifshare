#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
gifshare - Share Gifs via Amazon S3
"""

FOOTER = """
Copyright (c) 2014 by Mark Smith.
MIT Licensed, see LICENSE.txt for more details.
"""

__version__ = '0.0.1'

import argparse
from ConfigParser import SafeConfigParser
import logging
from os.path import expanduser, isfile, basename, splitext
import re
from StringIO import StringIO
import sys

from boto.s3.key import Key
from boto.s3.connection import S3Connection

import magic
import progressbar
import requests


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
    'gif': 'image/gif',
    'jpeg': 'image/jpeg',
    'png': 'image/png',
}
LOG = logging.getLogger('gifshare')


def correct_ext(data, is_buffer=False):
    magic_output = magic.from_buffer(data) if is_buffer else magic.from_file(
        data)
    match = re.search(r'JPEG|GIF|PNG', magic_output)
    if match:
        return match.group(0).lower()
    else:
        raise UnknownFileType("Unknown file type: {}".format(magic_output))


def load_config():
    config = SafeConfigParser()
    config.read([expanduser('~/.gifshare'), '.gifshare'])
    return config


def download_file(url):
    LOG.debug("Downloading image ...")
    response = requests.get(url, stream=True)
    length = int(response.headers['content-length'])
    print 'Content length:', length
    content = StringIO()
    i = 0
    widgets = ['Downloading image ', progressbar.Bar(), progressbar.Percentage()]
    pbar = progressbar.ProgressBar(widgets=widgets, maxval=length).start()
    for chunk in response.iter_content(64):
        i += len(chunk)
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


def upload_url(config, url, name=None, force=False):
    data = download_file(url)
    ext = correct_ext(data, True)
    filename = (name or get_name_from_url(url)) + '.' + ext
    dest_url = config.get('default', 'web_root') + filename
    bucket = Bucket(config)
    key = bucket.key_for(filename, CONTENT_TYPE_MAP[ext])
    if key.exists() and force == False:
        raise FileAlreadyExists("File at {} already exists!".format(dest_url))
    LOG.debug("Uploading image ...")

    key.set_contents_from_string(data, cb=upload_callback())

    return dest_url


def upload_file(config, path, name=None, force=False):
    LOG.debug("Uploading file ...")
    ext = correct_ext(path)
    filename = (name or splitext(basename(path))[0]) + '.' + ext
    url = config.get('default', 'web_root') + filename
    bucket = Bucket(config)
    key = bucket.key_for(filename, CONTENT_TYPE_MAP[ext])
    if key.exists() and force == False:
        raise FileAlreadyExists("File at {} already exists!".format(url))
    key.set_contents_from_filename(path, cb=upload_callback())

    return url


class Bucket(object):
    def __init__(self, config):
        self._bucket = None
        self._key_id = config.get('default', 'aws_access_id')
        self._access_key = config.get('default', 'aws_secret_access_key')
        self._bucket_name = config.get('default', 'bucket')

    @property
    def bucket(self):
        if not self._bucket:
            conn = S3Connection(self._key_id, self._access_key)
            self._bucket = conn.get_bucket(self._bucket_name)
        return self._bucket

    def key_for(self, filename, content_type):
        k = Key(self.bucket, filename)
        k.content_type = content_type
        return k

    def list(self):
        bucket = self.bucket
        for key in bucket.list():
            url = config.get('default', 'web_root') + key.name
            print url


def command_upload(arguments, config):
    path = arguments.path
    if not URL_RE.match(path):
        if isfile(path):
            print upload_file(
                config, path, arguments.key, force=arguments.force)
        else:
            raise IOError(
                '{} does not exist or is not a file!'.format(path))
    else:
        print upload_url(
            config, path, arguments.key, force=arguments.force)


def command_list(arguments, config):
    list(config)


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

        upload_parser = subparsers.add_parser("upload")
        upload_parser.set_defaults(target=command_upload)

        upload_parser.add_argument(
            '--force', '-f', action='store_true', default=False,
            help='Overwrite any existing files if necessary.')

        upload_parser.add_argument(
            'path',
            help='The path to a file to upload')

        upload_parser.add_argument(
            'key',
            nargs='?',
            help='A nice filename for the gif.')

        list_parser = subparsers.add_parser("list")
        list_parser.set_defaults(target=command_list)

        arguments = a_parser.parse_args(argv)
        config = load_config()

        logging.basicConfig()
        LOG.setLevel(
            level=logging.DEBUG if arguments.verbose else logging.WARN)

        arguments.target(arguments, config)
    except UserException as ue:
        print >> sys.stderr, ue
        return 1


if __name__ == '__main__':
    sys.exit(main())

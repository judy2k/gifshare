# -*- coding: utf-8 -*-

"""
Functionality specific to Amazon S3 storage.
"""

from __future__ import absolute_import, print_function, unicode_literals

import logging
import sys

from boto.s3.key import Key
from boto.s3.connection import S3Connection

import progressbar

from .exceptions import FileAlreadyExists, MissingFile


LOG = logging.getLogger('gifshare.s3')


def upload_callback():
    """
    Return a callback function that can be called repeatedly with a current
    value and total value to update a progress bar on the screen.

    The progress-bar is initialised on the first call, and disposed of when
    called with update == total.
    """
    pbar = [None]
    widgets = ['Uploading image ', progressbar.Bar(), progressbar.Percentage()]

    def callback(update, total):
        """
        A callback for displaying, updating, and disposing of a terminal
        progress bar.
        """
        if pbar[0] is None:
            pbar[0] = progressbar.ProgressBar(widgets=widgets, maxval=total)
            pbar[0].start()
        else:
            pbar[0].update(update)
        if update == total:
            pbar[0].finish()

    return callback


class Bucket(object):
    """
    Encapsulation of various operations on an S3 bucket.

    Should be initialised with a ConfigParser instance containing the
    following items:

    * aws_access_id
    * aws_secret_access_key
    * bucket
    * web_root
    """

    def __init__(self, config):
        self._bucket = None
        self._key_id = config.get('default', 'aws_access_id')
        self._access_key = config.get('default', 'aws_secret_access_key')
        self._bucket_name = config.get('default', 'bucket')
        self._web_root = config.get('default', 'web_root')

    @property
    def bucket(self):
        """
        A boto Bucket instance.
        """

        if not self._bucket:
            conn = S3Connection(self._key_id, self._access_key)
            self._bucket = conn.get_bucket(self._bucket_name)
        return self._bucket

    def key_for(self, filename, content_type=None):
        """
        Obtain a key in the configured bucket for the provided `filename`.

        If the key will be uploaded-to, the `content_type` param should
        be provided.
        """
        k = Key(self.bucket, filename)
        k.content_type = content_type
        return k

    def list(self):
        """
        Return an iterator over the image URLs stored in this bucket.
        """
        bucket = self.bucket
        for key in bucket.list():
            url = self._web_root + key.name
            yield url

    def upload_file(self, filename, content_type, path, force=False):
        """
        Upload a file from the filesystem to the S3 bucket.

        `filename` is a path to the local file. The uploaded file will be
        stored at `path`, with the provided `content-type`. If `force` is
        `True`, any existing image at the specified path will be overwritten.
        """
        url = self._web_root + filename

        key = self.key_for(filename, content_type)
        if key.exists() and not force:
            raise FileAlreadyExists("File at {} already exists!".format(url))
        LOG.debug("Uploading image ...")
        key.set_contents_from_filename(path, cb=upload_callback())

        return url

    def upload_contents(self, filename, content_type, data, force=False):
        """
        Upload image data to the S3 bucket.

        `filename` contains path under the S3 bucket. `content-type` is the
        content type stored against the image file. `data` contains the
        binary image data.

        If `force` is `True`, any existing image at the specified path will be
        overwritten.
        """
        dest_url = self._web_root + filename
        key = self.key_for(filename, content_type)
        if key.exists() and not force:
            raise FileAlreadyExists(
                "File at {} already exists!".format(dest_url))
        LOG.debug("Uploading image ...")
        key.set_contents_from_string(data, cb=upload_callback())

        return dest_url

    def delete_file(self, remote_path):
        """
        Delete an S3 file at the specified `remote_path`.
        """
        key = self.key_for(remote_path)
        if key.exists():
            key.delete()
        else:
            print("The image '%s' does not exist" % remote_path,
                  file=sys.stderr)

    def get_url(self, name):
        """
        Generate a URL for `name` stored in the bucket.
        """
        key = self.key_for(name)
        if key.exists():
            return self._web_root + name
        else:
            raise MissingFile("The image '%s' does not exist" % name)

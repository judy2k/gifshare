# -*- coding: utf-8 -*-

"""
Core gifshare functionality.
"""

from __future__ import absolute_import, print_function, unicode_literals

import logging
from os.path import expanduser, basename, splitext
import re
import webbrowser

from six.moves import configparser
from six import StringIO
import magic
import progressbar
import requests

from .exceptions import UnknownFileType


LOG = logging.getLogger('gifshare.core')

VERSION = '0.0.4'
CONTENT_TYPE_MAP = {
    u'gif': u'image/gif',
    u'jpeg': u'image/jpeg',
    u'png': u'image/png',
}


def load_config():
    """
    Load configuration from the following locations in order:

    * .gifshare in the user's home directory
    * .gifshare in the current directory
    """
    config = configparser.SafeConfigParser()
    config.read([expanduser('~/.gifshare'), '.gifshare'])
    return config


def download_file(url):
    """
    Download an image from the provided `url` and return the file contents as
    a `str`.
    """
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


def correct_ext(data, is_buffer=False):
    """
    Inspect the contents of an image (data), and determine what image type it
    conforms to. Return the correct file extension for this image-type.

    Raises an UnknownFileType exception if data is not PNG, GIF or JPEG
    image data.
    """
    magic_output = magic.from_buffer(data) if is_buffer else magic.from_file(
        data)
    match = re.search(r'JPEG|GIF|PNG', magic_output.decode('utf-8'))
    if match:
        return match.group(0).lower()
    else:
        raise UnknownFileType("Unknown file type: {}".format(magic_output))


def get_name_from_url(url):
    """
    Extract the filename from the end of a url.
    """
    return re.match(r'.*/([^/\.]+)', url).group(1)


class GifShare(object):
    """
    High level application functionality.
    """

    def __init__(self, bucket):
        self._bucket = bucket

    def upload_url(self, url, name=None, force=False):
        """
        Download the image at `url` and then upload the image data. The name
        is devised from the original URL. This can be overridden by providing
        `name`.

        If `force` is `True`, any existing image at the specified path will be
        overwritten.
        """
        LOG.debug("Uploading URL '%s'", url)
        data = download_file(url)
        ext = correct_ext(data, True)
        content_type = CONTENT_TYPE_MAP[ext]
        filename = (name or get_name_from_url(url)) + '.' + ext

        return self._bucket.upload_contents(
            filename, content_type, data, force)

    def upload_file(self, path, name=None, force=False):
        """
        Upload a file from the filesystem.

        `path` is a path to the local file. The name is devised from the
        original file name. This can be overridden by providing `name`.

        If `force` is `True`, any existing image at the specified path will be
        overwritten.
        """
        LOG.debug("Uploading file '%s'", path)
        ext = correct_ext(path)
        filename = (name or splitext(basename(path))[0]) + '.' + ext
        content_type = CONTENT_TYPE_MAP[ext]
        return self._bucket.upload_file(filename, content_type, path, force)

    def delete_file(self, remote_path):
        """
        Delete a remote file currently stored at `remote_path`.
        """
        self._bucket.delete_file(remote_path)

    def get_url(self, name):
        """
        Obtain a URL for name stored in the bucket.
        """
        return self._bucket.get_url(name)

    def show(self, name):
        """
        Display the image with `name` in the user's browser.
        """
        webbrowser.open_new(self.get_url(name))

    def grep(self, pattern):
        """
        Return a list of all URLs containing `pattern`.
        """
        return list(self._bucket.grep(pattern))

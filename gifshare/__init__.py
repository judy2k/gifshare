# -*- coding: utf-8 -*-
# flake8: noqa
# pylint: disable=unused-import, invalid-name

"""
gifshare - A command-line tool to upload images to S3.
"""

from __future__ import print_function, absolute_import, unicode_literals

from .core import VERSION, GifShare, download_file, load_config
from .s3 import Bucket

__VERSION__ = __version__ = version = VERSION

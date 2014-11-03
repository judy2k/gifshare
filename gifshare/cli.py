# -*- coding: utf-8 -*-

"""
Command-line interface functionality for gifshare.
"""

from __future__ import absolute_import, print_function, unicode_literals

import argparse
import logging
from os.path import isfile
import random
import re
import sys

from .s3 import Bucket
from .core import GifShare, load_config, VERSION
from .exceptions import UserException


LOG = logging.getLogger('gifshare.cli')

URL_RE = re.compile(r'^http.*')
FOOTER = """
Copyright (c) 2014 by Mark Smith.
MIT Licensed, see LICENSE.txt for more details.
"""


def command_upload(arguments, config):
    """
    Extract the provided argparse arguments and upload a file or URL.
    """
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
    """
    Extract the provided argparse arguments and list the files stored remotely.
    """
    bucket = Bucket(config)
    if not arguments.random:
        for item in bucket.list():
            print(item)
    else:
        print(random.choice(list(bucket.list())))


def command_delete(arguments, config):
    """
    Extract the provided argparse arguments and delete a remote file.
    """
    bucket = Bucket(config)
    bucket.delete_file(arguments.path)


def command_expand(arguments, config):
    """
    Extract the provided argparse arguments and expand the name to a URL.
    """
    bucket = Bucket(config)
    print(bucket.get_url(arguments.path))


def command_show(arguments, config):
    """
    Open the user's browser to display the image at the remote path specified
    in arguments.path.
    """
    GifShare(Bucket(config)).show(arguments.path)


def main(argv=sys.argv[1:]):
    """
    The entry-point for command-line execution.

    This function parses the command-line argument and then passes this and the
    loaded configuration off to a sub-command's `command_` function.
    """
    try:
        a_parser = argparse.ArgumentParser(
            description="""
            gifshare - A command-line tool to upload images to S3.
            """,
            epilog=FOOTER)
        a_parser.add_argument(
            '--version',
            action='version',
            version='%(prog)s ' + VERSION)

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

        expand_parser = subparsers.add_parser(
            "expand",
            help="Convert a filename to a URL"
        )
        expand_parser.add_argument(
            'path',
            help="The name of the uploaded file."
        )
        expand_parser.set_defaults(target=command_expand)

        show_parser = subparsers.add_parser(
            "show",
            help="Display a remote image in the browser."
        )
        show_parser.add_argument(
            'path',
            help="The name of the uploaded file."
        )
        show_parser.set_defaults(target=command_show)

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

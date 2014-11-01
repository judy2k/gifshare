# -*- coding: utf-8 -*-

from __future__ import absolute_import, print_function, unicode_literals


class UserException(Exception):
    """
    Indicates that the user should not see a stack-trace - just the
    exception message.
    """
    pass


class UnknownFileType(UserException):
    """
    A UserException that indicates that a file to be uploaded wasn't a PNG, GIF
    or JPEG file.
    """
    pass


class FileAlreadyExists(UserException):
    """
    A UserException that indicates that if a file was uploaded it would
    overwrite a file already in the store.
    """
    pass


class MissingFile(UserException):
    """
    A UserException that indicates a requested file was missing from
    the server.
    """

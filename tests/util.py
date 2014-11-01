# -*- coding: utf-8 -*-

import os.path


def image_path(ext):
        here = os.path.dirname(__file__)
        return os.path.join(here, u'fixtures', u'test_image.{}'.format(ext))


def load_image(ext):
        return open(image_path(ext), 'rb').read()

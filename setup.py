#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
gifshare - A command-line tool to upload images to S3.
"""

from setuptools import setup

import os.path

HERE = os.path.dirname(__file__)

setup(
    name="gifshare",
    version="0.0.4",
    description="Store images in S3",
    long_description=__doc__,
    author='Mark Smith',
    author_email='mark.smith@practicalpoetry.co.uk',
    url='https://github.com/judy2k/gifshare',
    license='MIT License',
    entry_points={
        'console_scripts': [
            'gifshare = gifshare:main',
        ]
    },
    packages=['gifshare'],
    classifiers=[
        'Development Status :: 4 - Beta',
        'Environment :: Console',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
    ],
    install_requires=open(
        os.path.join(HERE, 'requirements/_base.txt')
    ).readlines(),
    zip_safe=False,
)

#!/usr/bin/env python
# -*- coding: utf-8 -*-

from setuptools import setup

setup(
    name="gifshare",
    version="0.0.2",
    description="Store images in S3",
    long_description=__doc__,
    author='Mark Smith',
    author_email='mark.smith@practicalpoetry.co.uk',
    url='https://github.com/judy2k/tzgeo',
    license='MIT License',
    entry_points={
        'console_scripts': [
            'gifshare = gifshare:main',
        ]
    },
    py_modules=['gifshare'],
    classifiers=[
        'Development Status :: 4 - Beta',
        'Environment :: Console',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
    ],
    install_requires=open('requirements.txt').readlines(),
    zip_safe=False,
)

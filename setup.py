#!/usr/bin/python
# coding=UTF-8
#
# BitCurator Access Webtools (Disk Image Access for the Web)
# Copyright (C) 2014 - 2016
# All rights reserved.
#
# This code is distributed under the terms of the GNU General Public
# License, Version 3. See the text file "COPYING" for further details
# about the terms of this license.
#
"""Setup for flask app."""
from setuptools import setup

setup(
    name='wikidp',
    packages=['wikidp'],
    include_package_data=True,
    install_requires=[
        'flask',
        'wikidataintegrator',
        'wtforms',
        'requests==2.13.0',
        'lxml==3.7.3',
        'simplejson==3.10.0',
        'pywikibot'

    ],
)

#TO DO: If using python3.6, I had to run 'install certificates.command' inside the directory in order to load url's 
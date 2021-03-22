#!/usr/bin/python
# coding=UTF-8
#
# WikiDP Wikidata Portal
# Copyright (C) 2020
# All rights reserved.
#
# This code is distributed under the terms of the GNU General Public
# License, Version 3. See the text file "COPYING" for further details
# about the terms of this license.
#
"""Setup for flask app."""
from setuptools import setup, find_packages

INSTALL_REQUIRES = [
    'setuptools',
    'flask>=0.12.3',
    'wikidataintegrator==0.8.4',
    'lxml==4.6.3',
    'jsonpickle==1.4.1',
    'numpy==1.18.2',
    'pandas==1.0.3',
    'python-dateutil==2.8.1',
    'flask-mwoauth>=0.4.81',
    'tqdm==4.45.0',
    'validators==0.14.3'
]
PYTHON_REQUIRES = '>=3.6, <4'

TEST_DEPS = [
    'pre-commit',
    'pytest',
    'pylint',
    'pytest-coverage'
]
EXTRAS = {
    'testing': TEST_DEPS,
}

README = open('README.md', 'r')
README_TEXT = README.read()
README.close()

setup(
    name='wikidp',
    version='0.1.0',
    packages=find_packages(),
    include_package_data=True,
    install_requires=INSTALL_REQUIRES,
    tests_require=TEST_DEPS,
    extras_require=EXTRAS,
    python_requires=PYTHON_REQUIRES,
    platforms=['POSIX'],
    description='Digital preservation portal for Wikidata',
    long_description=README_TEXT,
    long_description_content_type='text/markdown',
    author='Kenny Seals-Nutt',
    author_email='',
    maintainer='Carl Wilson',
    maintainer_email='carl@openpreservation.org',
    url='http://wikidp.org/',
    classifiers=[
        'Environment :: Console',
        'Programming Language :: Python :: 3',
    ]
)

#TO DO: If using python3.6,
#       I had to run 'install certificates.command' inside the directory
#       in order to load url's

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
# This is a python __init__ script to create the app and import the
# main package contents
"""Initialisation module for package, kicks of the flask app."""
import logging

from wikidp.config import APP
from . import (
    routes,
)
if __name__ == "__main__":
    logging.debug("Importing %s", routes.__name__)
    logging.debug("Running Flask App on Port %s", APP.config.get('PORT'))
    APP.run(host='0.0.0.0', port=APP.config.get('PORT'))

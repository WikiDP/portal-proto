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
"""Configuration for WikiDP portal Flask app."""
import os
import tempfile
import logging

from flask import Flask

from .const import ConfKey


# Template these values for flexible install
HOST = 'localhost'
TEMP = tempfile.gettempdir()

# pylint: disable=R0903
class BaseConfig():
    """Base / default config, no debug logging and short log format."""

    HOST = HOST
    DEBUG = False
    LOG_FORMAT = '[%(filename)-15s:%(lineno)-5d] %(message)s'
    LOG_FILE = os.path.join(TEMP, 'wikidp.log')
    CACHE_DIR = os.path.join(TEMP, 'caches')
    SECRET_KEY = '7d441f27d441f27567d441f2b6176a'
    WIKIDATA_USER_NAME = '<username>'
    WIKIDATA_PASSWORD = '<password>'
    WIKIDATA_LANG = 'en'
    WIKIDATA_FB_LANG = 'en'
    ITEM_REGEX = r'(Q|q)\d+'
    PROPERTY_REGEX = r'(P|p)\d+'

# pylint: disable=R0903
class DevConfig(BaseConfig):
    """Developer level config, with debug logging and long log format."""

    DEBUG = True
    LOG_FORMAT = '[%(asctime)s %(levelname)-8s %(filename)-15s:%(lineno)-5d ' +\
                 '%(funcName)-30s] %(message)s'

CONFIGS = {
    "dev": 'wikidp.config.DevConfig',
    "default": 'wikidp.config.BaseConfig'
}

def configure_app(app):
    """Grab the environment variable for app config or defaults to dev."""
    config_name = os.getenv('WIKIDP_CONFIG', 'dev')
    app.config.from_object(CONFIGS[config_name])
    app.config['STATIC_DIR'] = os.path.join(app.root_path, 'static')
    # Bind to PORT if defined, otherwise default to 5000.
    app.config['PORT'] = int(os.environ.get('PORT', 5000))
    app.config['WIKIDATA_USER_NAME'] = os.getenv('WIKIDP_BOT_USER', BaseConfig.WIKIDATA_USER_NAME)
    app.config['WIKIDATA_PASSWORD'] = os.getenv('WIKIDP_BOT_PASSWORD', BaseConfig.WIKIDATA_PASSWORD)
    if os.getenv('WIKIDP_CONFIG_FILE'):
        app.config.from_envvar('WIKIDP_CONFIG_FILE')
    app.config['WIKIDATA_LANG'] = os.getenv('WIKIDP_LANG', BaseConfig.WIKIDATA_LANG)
    app.config['WIKIDATA_FB_LANG'] = os.getenv('WIKIDP_FB_LANG', BaseConfig.WIKIDATA_FB_LANG)
    app.config['WIKIDATA_SIGN_UP_URL'] = \
        "https://www.wikidata.org/w/index.php?title=Special:CreateAccount"
    # Create the list of unique languages to easy SPARQL queries
    if app.config['WIKIDATA_LANG'] != app.config['WIKIDATA_FB_LANG']:
        app.config['WIKIBASE_LANGUAGE'] = ",".join([app.config['WIKIDATA_LANG'],
                                                    app.config['WIKIDATA_FB_LANG']])
    else:
        app.config['WIKIBASE_LANGUAGE'] = app.config['WIKIDATA_LANG']

APP = Flask(__name__)
# Get the appropriate config
configure_app(APP)
# Configure logging across all modules
logging.basicConfig(filename=APP.config[ConfKey.LOG_FILE], level=logging.DEBUG,
                    format=APP.config[ConfKey.LOG_FORMAT])
logging.info("Started Wiki-DP Portal app.")
logging.debug("Configured logging.")
logging.debug("Logging in directory %s", APP.config[ConfKey.LOG_FILE])
logging.debug("Application configured with languages=%s", APP.config[ConfKey.WIKIBASE_LANGUAGE])

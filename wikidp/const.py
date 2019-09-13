#!/usr/bin/python
# coding=UTF-8
#
# WikiDP Wikidata Portal
# Copyright (C) 2017
# All rights reserved.
#
# This code is distributed under the terms of the GNU General Public
# License, Version 3. See the text file "COPYING" for further details
# about the terms of this license.
#
"""Constants used across BitCurator modules.
These need to map to the names used in the default config file, but better
than multiple hardcoded strings in code.
"""
ENTITY_URL_PATTERN = 'http://www.wikidata.org/entity/$1'
ITEM_REGEX = r'(Q|q)\d+'
PROPERTY_REGEX = r'(P|p)\d+'
LANG = 'en'
FALLBACK_LANG = 'en'
DEFAULT_UI_LANGUAGES = [
    (LANG, "English"),
    ("fr", "français (French)"),
    ("es", "Spanish"),
    ("de", "German"),
    ("da", "Danish"),
    ("nl", "Dutch"),
    ("zh", "Chinese"),
    ("ar", "Arabic"),
    ("it", "Italian"),
    ("lv", "Latvian"),
    ("et", "Estonian"),
    ("fi", "Finnish"),
    ("pt", "Portuguese"),
    ("sv", "Swedish"),
    ("no", "Norwegian"),
    ("ja", "Japanese")
]


class ConfKey():
    """Config key string constants"""
    LOG_FORMAT = 'LOG_FORMAT'
    LOG_FILE = 'LOG_FILE'
    WIKIDATA_LANG = 'WIKIDATA_LANG'
    WIKIDATA_FB_LANG = 'WIKIDATA_FB_LANG'
    WIKIBASE_LANGUAGE = 'WIKIBASE_LANGUAGE'
    ITEM_REGEX = 'ITEM_REGEX'
    PROPERTY_REGEX = 'PROPERTY_REGEX'

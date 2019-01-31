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
"""Flask application api routes for Wikidata portal."""
from flask import jsonify

from wikidp.config import APP
from wikidp.controllers.api import (
    get_property_checklist_from_schema,
    write_claims_to_item,
)
from wikidp.controllers.search import search_result_list
from wikidp.utils import (
    item_detail_parse,
    get_property,
)


@APP.route("/api/")
def route_api_welcome():
    """Landing Page API index"""
    return 'Welcome to the WikiDP API'


@APP.route("/api/<item:qid>", methods=['GET', 'POST'])
def route_api_get_item(qid):
    """User posts a item-id and returns json of (id, label, desc, aliases) ."""
    item = item_detail_parse(qid, with_claims=False)
    return jsonify(item)


@APP.route("/api/<item:qid>/claims/write", methods=['POST'])
def route_api_write_claims_to_item(qid):
    """ User posts a JSON object of claims to contribute to an item"""
    return write_claims_to_item(qid)


@APP.route("/api/<prop:pid>", methods=['GET', 'POST'])
def route_api_get_property(pid):
    prop = get_property(pid)
    return jsonify(prop)


@APP.route("/api/search/<search_string>", methods=['GET', 'POST'])
def route_api_search_item_by_string(search_string):
    """Post string, returns list of json of (id, label, desc, aliases) ."""
    _string = search_string.strip()
    output = search_result_list(_string)
    return jsonify(output)


@APP.route("/api/schema/<path:schema_name>/properties")
def route_api_get_properties_by_schema(schema_name):
    prop_list = get_property_checklist_from_schema(schema_name)
    return jsonify(prop_list)

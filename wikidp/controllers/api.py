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
""" Flask application routes for Wikidata portal. """
import logging

from flask import request, json, jsonify
import pywikibot

from wikidp.utils import remove_duplicates_from_list, get_pid_from_string
from wikidp.controllers import (
    sparql as sparql_controller,
    search as search_controller
)
import wikidp.DisplayFunctions as DF

SANDBOX_API_URL = 'https://test.wikidata.org/w/'
SANDBOX_SPARQL_URL = 'https://test.wikidata.org/proxy/wdqs/bigdata/namespace/wdq/'
SITE = pywikibot.Site("test", "wikidata")
REPO = SITE.data_repository()
SCHEMA_DIRECTORY_PATH = 'wikidp/schemas/'


def search_item_by_string(search_string):
    """Post string, returns list of json of (id, label, desc, aliases) ."""
    logging.debug("Processing user POST request.")
    string = search_string.strip()
    output = search_controller.search_result_list(string)
    return jsonify(output)


def get_item_label(qid):
    """User posts a item-id and returns json of (id, label, description, aliases)"""
    logging.debug("Processing user POST request.")
    output = DF.qid_to_basic_details(qid)
    return jsonify(output)


def load_schema(schema_name):
    try:
        with open(SCHEMA_DIRECTORY_PATH+schema_name) as data_file:
            return json.load(data_file)
    except Exception as e:
        return False


def get_schema_properties(schema_name):
    data = load_schema(schema_name)
    if data is False:
        return False
    exps = []
    for shape in data['shapes']:
        if 'expression' in shape:
            shape_expression = shape['expression']
            if 'expressions' in shape_expression:
                shape_expression_expressions = shape_expression['expressions']
                exps += [expression['predicate'] for expression in shape_expression_expressions if 'predicate' in expression and expression['predicate'] not in exps]
            if 'predicate' in shape_expression and shape_expression['predicate'] not in exps:
                exps.append(shape_expression['predicate'])
    # Extract pids from list
    exps = [get_pid_from_string(predicate) for predicate in exps if get_pid_from_string(predicate) is not False ]
    output = remove_duplicates_from_list(exps)
    return output


def get_property(pid, source='client'):
    property_details = sparql_controller.get_property_details_by_pid_list([pid])
    output = property_details['results']['bindings'][0]
    return jsonify(output) if source is 'client' else output


def get_property_checklist_from_schema(schema_name, source='client'):
    pid_list = get_schema_properties(schema_name)
    if pid_list:
        property_details = sparql_controller.get_property_details_by_pid_list(pid_list)
        output = property_details['results']['bindings']
    else:
        output = []
    return jsonify(output) if source is 'client' else output


def write_claims_to_item(qid):
    logging.debug("Processing user POST request.")
    user_claims = request.get_json()
    successful_claims, failure_claims = [], []
    item = pywikibot.ItemPage(REPO, u"Q175461")  # WIKIDATA TESTING ITEM
    # item = pywikibot.ItemPage(REPO, qid)
    for user_claim in user_claims:
        write_status = write_claim(item, user_claim['pid'], user_claim['value'], user_claim['type'])
        if write_status is True:
            successful_claims.append(user_claim)
        else:
            failure_claims.append(user_claim)
    output = {'status': 'success', 'successful_claims': successful_claims, 'failure_claims':failure_claims}
    return jsonify(output)


def write_claim(item, property, value, type, meta=False):
    """Write a claim to WikiData.

    Args:
        item (pywikibot.ItemPage): Wikidata Item Model
        property (str): Wikidata Property Identifier [ex. 'P1234']
        value (str): Value matching accepted property type (could be other
        datatypes) meta (dict, optional): Contains information about
        qualifiers/references/summaries
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        # TODO: Account for all dataTypes
        claim = pywikibot.Claim(REPO, property)
        if type == 'WikibaseItem':
            target = pywikibot.ItemPage(REPO, value)
        # elif type == 'Coordinate'
        # elif type == 'String'
        else:
            target = value
        claim.setTarget(target)
        item.addClaim(claim, summary=u'Adding claim')
        return True
    except Exception:
        return False

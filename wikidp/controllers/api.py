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
"""Flask application routes for Wikidata portal."""
from collections import defaultdict
from flask import (
    json,
    jsonify,
)
from wikidataintegrator.wdi_core import (
    WDItemEngine,
    WDItemID,
    WDString,
)
from wikidataintegrator.wdi_login import WDLogin

from wikidp.config import APP
from wikidp.const import ConfKey
from wikidp.models import FileFormat
from wikidp.utils import (
    get_pid_from_string,
    get_property_details_by_pid_list,
)

# pylint: disable=W0511
# TODO: Account for all dataTypes
STRING_TO_WD_DATATYPE = {
    "WikibaseItem": WDItemID,
    "String": WDString,
}
MEDIAWIKI_API_URL = APP.config[ConfKey.MEDIAWIKI_API_URL]
WIKIDATA_PASSWORD = APP.config[ConfKey.WIKIDATA_PASSWORD]
WIKIDATA_USER_NAME = APP.config[ConfKey.WIKIDATA_USER_NAME]
SCHEMA_DIRECTORY_PATH = 'wikidp/schemas/'


def build_login():
    """
    Build a WDI Login.

    Notes:
        TODO: Add params to use OAuth token once configured
        This is a temporary function to stub where we can thread
        OAuth through this entry-point when it is configured.
        Currently, it uses system-wide user/pwd credentials to login just
        to demonstrate writing behavior.

    Returns (WDLogin):

    """
    return WDLogin(mediawiki_api_url=MEDIAWIKI_API_URL,
                   user=WIKIDATA_USER_NAME,
                   pwd=WIKIDATA_PASSWORD)


def load_schema(schema_name):
    """Load a schema file by name."""
    try:
        with open(SCHEMA_DIRECTORY_PATH+schema_name) as data_file:
            return json.load(data_file)
    except FileNotFoundError:
        return None


def parse_predicate(expression):
    """
    Get the Property Id from an expression's predicate.
    Args:
        expression (Dict):

    Returns (Tuple[Optional[str], bool]):

    """
    predicate = expression.get("predicate", "")
    pid = get_pid_from_string(predicate)
    if pid:
        return pid, "qualifier" in predicate
    return None, False


def parse_expressions(schema):
    """
    Parse Shape Expressions of a Schema.

    Args:
        schema (Dict):

    Returns (defaultdict[str, set]):

    """
    prop_map = defaultdict(set)
    for shape in schema.get('shapes', []):
        outer_expression = shape.get('expression', {})
        props = set()
        qualifiers = set()
        for expression in outer_expression.get('expressions', []):
            pid, is_qualifier = parse_predicate(expression)
            if pid and is_qualifier:
                qualifiers.add(pid)
            elif pid:
                props.add(pid)
            for inner_expression in expression.get('expressions', []):
                pid, _ = parse_predicate(inner_expression)
                if pid:
                    prop_map[pid] = prop_map[pid]
        for prop in props:
            prop_map[prop] = qualifiers
    return prop_map


def get_schema_properties(schema_name):
    """
    Get property constraints of a particular schema.

    Args:
        schema_name (str): Relative file name of schema.

    Examples:
        >>> get_schema_properties('file_format_id_pattern')
        { "P31": {"P123"}, "P279": {}, ... }

    Returns (Optional[defaultdict[str, set]]):

    """
    data = load_schema(schema_name)
    if not data:
        return None
    return parse_expressions(data)


def flatten_prop_map(prop_map):
    """
    Extract all Ids from a property map.

    Args:
        prop_map (defaultdict[str, set]):

    Returns:

    """
    prop_ids = set()
    for prop, qualifiers in prop_map.items():
        prop_ids.add(prop)
        prop_ids.update(qualifiers)
    return prop_ids


def get_property_checklist_from_schema(schema_name):
    """
    Create a property checklist from a schema.

    Args:
        schema_name (str):

    Returns (List[Dict]):

    """
    prop_map = get_schema_properties(schema_name)
    if not prop_map:
        return []
    all_prop_ids = flatten_prop_map(prop_map)
    all_prop_data = {
        prop.get("id"): prop
        for prop in get_property_details_by_pid_list(all_prop_ids)
    }
    checklist = []
    for pid, qualifiers in prop_map.items():
        data = all_prop_data[pid]
        data["qualifiers"] = [
            all_prop_data[qualifier]
            for qualifier in qualifiers
        ]
        checklist.append(data)
    return checklist


def write_claims_to_item(qid, json_data):
    """
    Write new claims to an item.

    Args:
        qid (str): Wikidata Identifier
        json_data (List[Dict]): Data from request
    """
    # Build statements
    data = [
        build_statement(claim_data.get('pid'), claim_data.get('value'),
                        claim_data.get('type'), claim_data.get('qualifiers'),
                        claim_data.get('references'))
        for claim_data in json_data
    ]
    # Get wikidata item
    item = WDItemEngine(wd_item_id=qid, mediawiki_api_url=MEDIAWIKI_API_URL,
                        data=data)
    # Build login and Write to wikidata
    # TODO: Add params to use request OAuth token from request once configured
    wd_login = build_login()
    qid = item.write(wd_login)

    return jsonify({
        "message": f"Successfully Contributed {len(data)} "
                   f"Statements to Wikidata Item '{item.get_label()}' ({qid}).",
        "status": "success"
    })


def build_statement(prop, value, data_type, qualifier_data, reference_data):
    """
    Build Statement to Write to Wikidata.

    Args:
        prop (str): Wikidata Property Identifier [ex. 'P1234']
        value (str): Value matching accepted property
        data_type (str):
        qualifier_data (List[Dict]): list of data about qualifiers
        reference_data (List[Dict]): list of data about references

    Returns (WDBaseDataType):
    """
    qualifiers = [
        wd_datatype(qualifier.get('type'), value=qualifier.get('value'),
                    prop_nr=qualifier.get("pid"), is_qualifier=True)
        for qualifier in qualifier_data
    ]
    # The double list here is intentional based on the way Wikidataintegrator
    # expects the data type
    references = [[
        wd_datatype(reference.get('type'), value=reference.get('value'),
                    prop_nr=reference.get("pid"), is_reference=True)
        for reference in reference_data
    ]]

    return wd_datatype(data_type, prop_nr=prop, value=value,
                       qualifiers=qualifiers, references=references)


def wd_datatype(data_type_string, *args, **kwargs):
    """
    Create a WikidataIntegrator WDBaseDataType instance by a string name.

    Args:
        data_type_string (str):

    Returns (WDBaseDataType):

    """
    wd_datatype_class = STRING_TO_WD_DATATYPE[data_type_string]
    assert wd_datatype_class, f"Invalid Datatype '{wd_datatype_class}'"
    return wd_datatype_class(*args, **kwargs)


def get_all_file_formats():
    """
    Get all File Formats.

    Returns (List[FileFormat]):

    """
    formats = FileFormat.list_formats()
    return formats

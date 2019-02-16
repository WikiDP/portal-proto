from datetime import datetime
import json
import logging
from os import listdir
from os.path import (
    isfile,
    join,
    splitext,
)
import re
from string import Template

from urllib import request as urllib_request
from wikidataintegrator.wdi_core import WDItemEngine
import validators

from wikidp.const import (
    ITEM_REGEX,
    PROPERTY_REGEX,
    LANG,
    FALLBACK_LANG,
)
from wikidp.sparql import (
    ALL_QUALIFIER_PROPERTIES,
    PROPERTY_ALLOWED_QUALIFIERS,
    PROPERTY_QUERY,
)


def flatten_string(_string):
    return " ".join(_string.split())


def file_to_label(filename):
    output = remove_extension_from_filename(filename)
    return output.replace('_', ' ').title()


def get_pid_from_string(input_string):
    regex_search = re.search(PROPERTY_REGEX, input_string)
    return regex_search.group() if regex_search else False


def get_qid_from_string(input_string):
    regex_search = re.search(ITEM_REGEX, input_string)
    return regex_search.group() if regex_search else False


def entity_id_to_int(entity):
    return int(entity[1:])


def get_property(pid):
    prop_response = get_property_details_by_pid_list([pid])
    return prop_response[0] if prop_response else None


def convert_list_to_value_string(lst):
    """
        Arg: lst, ex: ['P31', 'P5', 'P123']
        Returns: "(wd:P31)(wd:P5)(wd:P123)"
    """
    return '(wd:{0})'.format(')(wd:'.join(map(str, lst)))


def format_wikidata_bindings(bindings):
    return [{k: v.get('value') for k, v in res.items()} for res in bindings]


def process_query_string(query):
    result = WDItemEngine.execute_sparql_query(query)
    bindings = result['results'].get('bindings')
    return format_wikidata_bindings(bindings)


def get_all_qualifier_properties():
    query = flatten_string(ALL_QUALIFIER_PROPERTIES)
    return process_query_string(query)


def get_allowed_qualifiers_by_pid(pid):
    value = convert_list_to_value_string([pid])
    query = PROPERTY_ALLOWED_QUALIFIERS_TEMPLATE.substitute(values=value)
    return process_query_string(query)


def get_property_details_by_pid_list(pid_list):
    values = convert_list_to_value_string(pid_list)
    query = PROPERTY_QUERY_TEMPLATE.substitute(values=values)
    return process_query_string(query)


def get_directory_filenames_with_subdirectories(directory_path):
    output = []
    for item in listdir(directory_path):
        i = {'name': item, 'label': file_to_label(item)}
        this_path = join(directory_path, item)
        if isfile(this_path):
            i['type'] = 'file'
        else:
            i['type'] = 'directory'
            i['files'] = get_directory_filenames_with_subdirectories(this_path)
        output.append(i)
    return output


def remove_extension_from_filename(filename_string):
    return splitext(filename_string)[0]


def time_formatter(time):
    """Converts wikidata's time json to a human readable string"""
    try:
        formatted_time = datetime.strptime(time, '+%Y-%m-%dT%H:%M:%SZ')
        return formatted_time.strftime("%A, %B %-d, %Y")
    except (ValueError, TypeError):
        return time


def get_wikimedia_image_url_from_title(title):
    """Convert image title to the url location of that file it describes."""
    # TO DO: Url's do not work with non-ascii characters
    #    For example, the title of the image for Q267193 [Sublime Text]
    #    is "Скриншот sublime text 2.png"
    title = title.replace(" ", "_")
    url = "https://commons.wikimedia.org/w/api.php?action=query&prop=imageinfo&iiprop=url&titles=File:{}&format=json"\
        .format(title)
    try:
        url = urllib_request.urlopen(url)
        base = json.loads(url.read().decode())["query"]["pages"]
        # Return just the first item
        for item in base:
            return base[item]["imageinfo"][0]["url"]
        return "https://commons.wikimedia.org/wiki/File:"+title
    except (UnicodeEncodeError, KeyError, Exception):
        return "https://commons.wikimedia.org/wiki/File:"+title


def parse_wd_response_by_key(item, key, default=None):
    """
    Parse WikiData Response dictionary into a python list of values
    Args:
        item (dict): Returned output of using wikidataintegrator's wd_json_representation
        key (str): Desired key to extract values of from item
        default (optional): Expected return if value does not exist for fallback language

    Returns ([str]): list of values
    """
    value_dict = item.get(key)
    if value_dict:
        values = get_lang(value_dict, default=default)
        if type(values) is list:
            return [x.get('value') for x in values]
        if type(values) is dict:
            return values.get('value', values)
        return values
    return default


def get_lang(_dict, default=None):
    """
    Get language value of a dictionary, fallback language if not available
    Args:
        _dict (dict): Dictionary for getting value
        default (optional): Expected return if value does not exist for fallback language

    Returns: value of dictionary's language key or default

    """
    if _dict is {}:
        pass
    value = _dict.get(LANG)
    if value:
        return value
    return _dict.get(FALLBACK_LANG, default)


def item_detail_parse(qid, with_claims=True):
    """Uses the JSON representation of wikidataintegrator to parse the item ID specified (qid)
    and returns a new dictionary of previewing information and a dictionary of property counts"""
    item = get_item_json(qid)
    if item:
        label = parse_wd_response_by_key(item, 'labels', default="Item {}".format(qid))
        aliases = parse_wd_response_by_key(item, 'aliases', default=[])
        description = parse_wd_response_by_key(item, 'descriptions', default='')
        output_dict = {'qid': qid, 'label': label, 'aliases': aliases, 'description': description}
        if with_claims:
            claim_list = []
            ex_list = []
            categories = []
            claims = get_claims_from_json(item)
            properties = get_property_details_by_pid_list(claims.keys())
            cached_property_labels = {prop['id']: prop['propertyLabel'] for prop in properties}
            for pid, claim_dict in sorted(claims.items(), key=lambda x: entity_id_to_int(x[0])):
                property_label = cached_property_labels.get(pid)
                value_list = []
                add_to_ex_list = False
                for json_details in claim_dict:
                    val = parse_snak(pid, json_details.get('mainsnak'), cached_property_labels)
                    if val:
                        val['references'] = parse_references(json_details, cached_property_labels)
                        val['qualifiers'] = parse_qualifiers(json_details, cached_property_labels)
                        value_list.append(val)
                        if val.get('parse_type') == 'external-id':
                            add_to_ex_list = True
                        #  Determining the 'category' of the item from the 'instance of' and 'subclass of' properties
                        elif pid in ['P31', 'P279']:
                            categories.append(val)
                parsed_claim = {'pid': pid, 'label': property_label, 'values': value_list}
                ex_list.append(parsed_claim) if add_to_ex_list else claim_list.append(parsed_claim)
            output_dict['external_links'] = ex_list
            output_dict['claims'] = claim_list
            output_dict['categories'] = categories
            output_dict['properties'] = properties
        return output_dict
    return False


def parse_qualifiers(json_details, cached_property_labels):
    qualifier_set = json_details.get('qualifiers')
    return parse_snak_set(qualifier_set, cached_property_labels)


def parse_references(json_details, cached_property_labels):
    reference_list = json_details.get('references')
    if reference_list:
        reference_set = reference_list[0].get('snaks')
        return parse_snak_set(reference_set, cached_property_labels)
    return []


def parse_snak_set(snak_set, cached_property_labels):
    parsed_snaks = []
    if snak_set:
        for pid, snak_list in snak_set.items():
            label = pid_label(pid, cached_property_labels)
            values = []
            for snak in snak_list:
                val = parse_snak(pid, snak, cached_property_labels)
                if val:
                    values.append(val)
            if values:
                parsed_snaks.append({'pid': pid, 'label': label, 'values': values})
    return parsed_snaks


def get_item_json(qid):
    """
    Get item json dictionary from qid
    Args:
        qid (str): Wikidata Identifier, ex: "Q1234"

    Returns:
        Dict: Returned value of WDItemEngine().wd_json_representation
    """
    try:
        item = WDItemEngine(wd_item_id=qid)
        return item.wd_json_representation
    except (ValueError, ConnectionAbortedError, Exception):
        logging.exception("Exception reading QID: %s", qid)
        return None


def get_item_property_counts(qid):
    """
    Count the number of values in a claim by property
    Args:
        qid (str): Wikidata Identifier, ex: "Q1234"

    Returns:
        Dict: {k(str): v(int)} where k is Wikidata Property identifier string and v is count
    """
    selected_item = get_item_json(qid)
    claims = get_claims_from_json(selected_item)
    counts = {}
    for pid, values in claims.items():
        counts[pid] = len(values)
    return counts


def get_claims_from_json(item_json):
    """
    Get claim dictionary from WD Item Json Representation
    Args:
        item_json (dict): Returned value of WDItemEngine().wd_json_representation

    Returns:
        Dictionary of {k:v} where k is property id and v is list of value dictionaries
    """
    return item_json.get('claims', {})


def parse_snak(pid, snak, cached_property_labels):
    """ Uses the json_details dictionary of a single claim and outputs
    the parsed data into the output_dict. """
    try:
        if snak['snaktype'] == 'novalue' or 'datavalue' not in snak:
            return None
        #  Parsing the statements & values by data type
        parse_type = snak.get('datatype')
        data_type = snak['datavalue'].get('type')
        data_value = snak['datavalue'].get('value')

        #  In the event the value is an image file name, convert the title to the image's url
        if pid in ["P18", "P154"]:
            val = get_wikimedia_image_url_from_title(data_value)
            parse_type = 'image'
        elif parse_type == 'external-id':
            val = {'url': format_url_from_property(pid, data_value), 'label': data_value}
        elif data_type == 'string':
            val = data_value
            if validators.url(val):
                parse_type = 'url'
        elif data_type == 'wikibase-entityid':
            parse_type = data_value.get('entity-type')
            if parse_type == 'property':
                pid = 'P{}'.format(data_value.get('numeric-id'))
                label = pid_label(pid, cached_property_labels)
                val = {'pid': pid, 'label': label}
            else:
                val = data_value.get('id')
        elif data_type == 'time':
            val = time_formatter(data_value.get('time'))
            parse_type = 'time'
        elif data_type == 'quantity' and 'amount' in data_value:
            num = data_value.get('amount')
            try:
                val = int(num)
            except ValueError:
                val = float(num)
        elif data_type == 'monolingualtext':
            val = '"{}" (language: {})'.format(data_value.get('text', ''), data_value.get('language', 'unknown'))
        else:
            val = "Unable To Parse Value {}".format(data_type)
        return {'value': val, 'parse_type': parse_type, 'type': data_type}
    except (KeyError, Exception):
        logging.exception("Unexpected exception parsing claims.")
        return None


def parse_by_data_type(data, cached_property_labels=None):
    """ Checks the data type of the current data value to determine how
    to return as a string or ID-label tuple. """
    data_type = type(data)
    if data_type is dict:
        if 'text' in data:
            return data['text']
        elif 'time' in data:
            return time_formatter(data.get('time'))
        elif 'entity-type' in data and 'id' in data:
            return id_to_label_list(data.get('id'), cached_property_labels)
    return data


def id_to_label_list(wikidata_id, cached_property_labels):
    """Takes in an id (P## or Q##) and returns a list of that entity's label and id"""
    if wikidata_id[0].lower() == 'p':
        return [wikidata_id, pid_label(wikidata_id, cached_property_labels)]
    return [wikidata_id]


def pid_label(pid, cached_values):
    """Convert property identifier (P###) to a label and updates the cache."""
    if pid not in cached_values:
        prop = get_property(pid)
        default_label = "property {}".format(pid)
        property_label = prop.get('propertyLabel', default_label) if prop else default_label
        cached_values[pid] = property_label
        return property_label
    return cached_values.get(pid)


def format_url_from_property(pid, value):
    """Inputs property identifier (P###) for a given url type, looks up that
    wikidata property id's url format (P1630) and creates a url with the value using the format"""
    value = value.strip()
    prop = get_property(pid)
    if 'formatter_url' in prop:
        return prop.get("formatter_url").replace("$1", value)
    return None


def create_query_template(_string):
    flat_str = flatten_string(_string)
    return Template(flat_str)


# Register Template Queries Here
PROPERTY_QUERY_TEMPLATE = create_query_template(PROPERTY_QUERY)
PROPERTY_ALLOWED_QUALIFIERS_TEMPLATE = create_query_template(PROPERTY_ALLOWED_QUALIFIERS)

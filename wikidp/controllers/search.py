"""Search Controller Functions and Helpers for WikiDP."""

import logging
import re

from wikidataintegrator.wdi_core import WDItemEngine

from wikidp.models import PuidSearchResult
from wikidp.utils import (
    LANG,
    item_detail_parse,
)


def get_search_result_context(search_string):
    context = []
    # Check if searching with PUID
    if re.search("[x-]?fmt/\d+", search_string) is not None:
        result = PuidSearchResult.search_puid(search_string, lang=LANG)
        for res in result:
            context.append({
                'qid': res.format,
                'label': res.label,
                'description': res.description
            })
    context.extend(search_result_list(search_string))
    return context


def search_result_list(string):
    """
    Use wikidataintegrator to generate a list of similar items based on a
    text search and returns a list of (qid, Label, description, aliases)
    dictionaries
    """
    result_qid_list = WDItemEngine.get_wd_search_results(string, language=LANG)
    output = []
    for qid in result_qid_list[:10]:
        item = item_detail_parse(qid, with_claims=False)
        if item:
            output.append(item)
    return output


def get_search_by_puid_context(puid):
    new_puid = puid.replace('_', '/')
    logging.debug("Searching for PUID: %s", new_puid)
    results = PuidSearchResult.search_puid(new_puid, lang=LANG)
    return new_puid, results

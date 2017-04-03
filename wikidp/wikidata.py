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
""" Some basic Wikidata examples to go with our PywikiBot """
import os.path
import pywikibot
from pywikibot import pagegenerators as pg

SITE = pywikibot.Site("wikidata", "wikidata")
REPO = SITE.data_repository()
THIS_DIR = os.path.dirname(os.path.abspath(__file__))

def wikidata_test():
    """ Simple Proof of Concept test that prints an item. """
    item = pywikibot.ItemPage(REPO, "Q26085352")
    item_dict = item.get() #Get the item dictionary
    clm_dict = item_dict["claims"] # Get the claim dictionary
    return str(clm_dict)

def get_formats_generator():
    """ Convenience method to return the list of file formats using the SPARQL
    query file. """
    query_file_path = get_query_path('list-formats.rq')
    return get_sparql_generator(query_file_path, SITE)

def get_sparql_generator(query_file_path, site):
    """ Opens the SPARQL file at query_file_path, reads the contents and queries
    SITE for the data and returns the generator. """
    with open(query_file_path, 'r') as query_file:
        query = query_file.read().replace('\n', '')
    generator = pg.WikidataQueryPageGenerator(query, site=site)
    return generator

def get_query_path(query_file_name):
    """ Munges the path to a query file together """
    return os.path.join(THIS_DIR, 'queries/' + query_file_name)

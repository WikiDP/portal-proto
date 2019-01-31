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
"""Model classes to glue queries to return types."""
import logging

from wikidataintegrator import wdi_core


class FileFormat(object):
    """Encapsulates a file format plus wikidata query magic for formats."""
    def __init__(self, qid, name, media_types=None):
        self._qid = qid
        self._name = name
        self._media_types = media_types if media_types is not None else []

    @property
    def qid(self):
        """The wikidata item id."""
        return self._qid

    @property
    def name(self):
        """The name of the format, equivalent to the WikiData label."""
        return self._name

    @property
    def media_types(self):
        """A list of MediaTypes associated with the format."""
        return self._media_types

    def __str__(self):
        _media_types = '|'.join(self.media_types)
        return "FileFormat : [qid={}, name={}, media_types=[{}]]".format(self.qid, self.name, _media_types)

    @classmethod
    def list_formats(cls, lang="en"):
        """Queries Wikidata for formats and returns a list of FileFormat instances."""
        query = [
            "SELECT ?idFileFormat ?idFileFormatLabel",
            "(GROUP_CONCAT(DISTINCT ?mediaType; SEPARATOR='|') AS ?mediaTypes)",
            "WHERE {",
            "?idFileFormat wdt:P31 wd:Q235557.",
            "OPTIONAL { ?idFileFormat wdt:P1163 ?mediaType }",
            "SERVICE wikibase:label {{ bd:serviceParam wikibase:language  '{}' }}".format(lang),
            "}",
            "GROUP BY ?idFileFormat ?idFileFormatLabel",
            "ORDER BY ?idFileFormatLabel"
            ]
        results_json = wdi_core.WDItemEngine.execute_sparql_query(" ".join(query))
        results = [cls(x['idFileFormat']['value'].replace('http://www.wikidata.org/entity/', ''),
                       x['idFileFormatLabel']['value'],
                       x['mediaTypes']['value'].split('|'))
                   for x in results_json['results']['bindings']]
        return results


class PuidSearchResult(object):
    """Encapsulates a file format plus wikidata query magic for formats."""
    def __init__(self, wd_format, label, description, mime, puid):
        self._format = wd_format
        self._label = label
        self._description = description
        self._mime = mime
        self._puid = puid

    @property
    def format(self):
        """The wikidata item the format field."""
        return self._format

    @property
    def label(self):
        """The formats WikiData label."""
        return self._label

    @property
    def description(self):
        """The description type of the format."""
        return self._description

    @property
    def mime(self):
        """The MIME type of the format."""
        return self._mime

    @property
    def puid(self):
        """The PUID of the format."""
        return self._puid

    def __str__(self):
        return "PuidSearchResult : [format={}, label={}, MIME={}, puid={}]"\
            .format(self.format, self.label, self.mime, self.puid)

    @classmethod
    def search_puid(cls, puid, lang="en"):
        """Queries Wikidata for formats and returns a list of FileFormat instances."""
        query = cls._concat_query("VALUES ?puid {{ '{}' }}".format(puid), lang)
        results_json = wdi_core.WDItemEngine.execute_sparql_query(query)
        logging.debug(str(results_json))
        return cls._assemble_results(results_json)

    @classmethod
    def search_mime(cls, mime, lang="en"):
        """Queries Wikidata for formats and returns a list of FileFormat instances."""
        query = cls._concat_query("VALUES ?mime {{ '{}' }}".format(mime), lang)
        results_json = wdi_core.WDItemEngine.execute_sparql_query(query)
        logging.debug(str(results_json))
        return cls._assemble_results(results_json)

    @staticmethod
    def _concat_query(values_clause="", lang="en"):
        query = [
            "SELECT DISTINCT ?format ?formatLabel ?formatDescription ?mime ?puid",
            "WHERE {",
            "?format wdt:P2748 ?puid.",
            "OPTIONAL{?format wdt:P1163 ?mime.}",
            "SERVICE wikibase:label {{ bd:serviceParam wikibase:language '{}' }}".format(lang),
            values_clause,
            "}"
            ]
        return " ".join(query)

    @staticmethod
    def _assemble_results(results_json):
        results = [PuidSearchResult(
            x['format']['value'].replace('http://www.wikidata.org/entity/', ''),
            x['formatLabel']['value'],
            x['formatDescription']['value'],
            x['mime']['value'] if 'mime' in x else 'unknown',
            x['puid']['value'])
                   for x in results_json['results']['bindings']]
        return results

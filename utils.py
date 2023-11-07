import copy
import json
import os
import requests
import requests_cache
import sqlite3
import urllib.parse
import rdflib
import sys

import regex as re

from local import MARKLOGIC, REQUESTS_CACHE_DB

# OVERRIDE AS PER JL, UNTIL MORE ITEMS IN THE DB ARE SET TO PUBLIC DOMAIN.
# All of these items are from Spoken Yucatec Maya, by Robert W.  Blair and
# Refugio Vermont-Salas Yucatán Maya
# (https://mlc.lib.uchicago.edu/series/b2tw6wt2bf1h/)

ADJUST_PERMISSIONS_FOR = (
    'https://ark.lib.uchicago.edu/ark:61001/b27z7tq17f2p/',
    'https://ark.lib.uchicago.edu/ark:61001/b2ns2j788j88/',
    'https://ark.lib.uchicago.edu/ark:61001/b2x35rw20w44/',
    'https://ark.lib.uchicago.edu/ark:61001/b2b32bm0cc6s/',
    'https://ark.lib.uchicago.edu/ark:61001/b2xp6p144m5j/',
    'https://ark.lib.uchicago.edu/ark:61001/b2sv9z53wj4g/',
    'https://ark.lib.uchicago.edu/ark:61001/b2zb56k8272g/',
    'https://ark.lib.uchicago.edu/ark:61001/b2kk51x0nf0z/',
    'https://ark.lib.uchicago.edu/ark:61001/b2xj8mp1mf2w/',
    'https://ark.lib.uchicago.edu/ark:61001/b2fm4c69rx5z/',
    'https://ark.lib.uchicago.edu/ark:61001/b26226s5q30f/',
    'https://ark.lib.uchicago.edu/ark:61001/b2bd0kb22h4s/',
    'https://ark.lib.uchicago.edu/ark:61001/b2pz25j6vr6r/',
    'https://ark.lib.uchicago.edu/ark:61001/b2jc45r1gt15/',
    'https://ark.lib.uchicago.edu/ark:61001/b2wz2h56sf1w/',
    'https://ark.lib.uchicago.edu/ark:61001/b2s60jp86929/',
    'https://ark.lib.uchicago.edu/ark:61001/b2dd7np9c11x/',
    'https://ark.lib.uchicago.edu/ark:61001/b2nn4hh3gv92/',
    'https://ark.lib.uchicago.edu/ark:61001/b2xg1804tx87/',
    'https://ark.lib.uchicago.edu/ark:61001/b2hj0w19mk93/',
    'https://ark.lib.uchicago.edu/ark:61001/b2rz0nt08s1x/',
    'https://ark.lib.uchicago.edu/ark:61001/b2fd1h93d30h/',
    'https://ark.lib.uchicago.edu/ark:61001/b2nx6ht9gs29/',
    'https://ark.lib.uchicago.edu/ark:61001/b2r11rg54r8n/',
    'https://ark.lib.uchicago.edu/ark:61001/b2092cs0g415/',
    'https://ark.lib.uchicago.edu/ark:61001/b2v113n2dd5c/',
    'https://ark.lib.uchicago.edu/ark:61001/b2c26267q062/',
    'https://ark.lib.uchicago.edu/ark:61001/b2m95x63mk4b/',
    'https://ark.lib.uchicago.edu/ark:61001/b2db9dx96x10/',
    'https://ark.lib.uchicago.edu/ark:61001/b2t13k17j52d/',
    'https://ark.lib.uchicago.edu/ark:61001/b2d92d45md76/',
    'https://ark.lib.uchicago.edu/ark:61001/b24p59z2z190/',
    'https://ark.lib.uchicago.edu/ark:61001/b2g22mq7mg0g/',
    'https://ark.lib.uchicago.edu/ark:61001/b2wh7z086r8p/',
    'https://ark.lib.uchicago.edu/ark:61001/b2zb1zh1237h/',
    'https://ark.lib.uchicago.edu/ark:61001/b2q21gp5gd01/',
    'https://ark.lib.uchicago.edu/ark:61001/b2dt1p02tj1v/',
    'https://ark.lib.uchicago.edu/ark:61001/b2p72hc6f05g/',
    'https://ark.lib.uchicago.edu/ark:61001/b24w9th7137b/',
    'https://ark.lib.uchicago.edu/ark:61001/b22k5pj7kj30/',
    'https://ark.lib.uchicago.edu/ark:61001/b2v93v03sf4m/',
    'https://ark.lib.uchicago.edu/ark:61001/b2gx09697j4m/',
    'https://ark.lib.uchicago.edu/ark:61001/b2g45jm25615/',
    'https://ark.lib.uchicago.edu/ark:61001/b2qz60h81g2v/',
    'https://ark.lib.uchicago.edu/ark:61001/b20w2mk13s96/',
    'https://ark.lib.uchicago.edu/ark:61001/b2986kg1zg6r/',
    'https://ark.lib.uchicago.edu/ark:61001/b2kf6wg1156r/',
    'https://ark.lib.uchicago.edu/ark:61001/b2cv6zt8fx9t/',
    'https://ark.lib.uchicago.edu/ark:61001/b2g334r72v2t/',
    'https://ark.lib.uchicago.edu/ark:61001/b2cj6d02g311/',
    'https://ark.lib.uchicago.edu/ark:61001/b2w08504c143/',
    'https://ark.lib.uchicago.edu/ark:61001/b26n7mt8c979/',
    'https://ark.lib.uchicago.edu/ark:61001/b2n86h25sc45/',
    'https://ark.lib.uchicago.edu/ark:61001/b2dv15c7rc3q/',
    'https://ark.lib.uchicago.edu/ark:61001/b2sm18k8n75j/',
    'https://ark.lib.uchicago.edu/ark:61001/b2r58933xn1j/',
    'https://ark.lib.uchicago.edu/ark:61001/b28n1dc7n541/',
    'https://ark.lib.uchicago.edu/ark:61001/b2kn8b21zc7f/',
    'https://ark.lib.uchicago.edu/ark:61001/b2917kg25x0z/',
    'https://ark.lib.uchicago.edu/ark:61001/b2s24fg9mp1p/',
    'https://ark.lib.uchicago.edu/ark:61001/b26h3895d33z/',
    'https://ark.lib.uchicago.edu/ark:61001/b2dk20t1r33s/',
    'https://ark.lib.uchicago.edu/ark:61001/b2bb80n1rc11/',
    'https://ark.lib.uchicago.edu/ark:61001/b2kf56f95m07/',
    'https://ark.lib.uchicago.edu/ark:61001/b2nc1f30z72q/',
    'https://ark.lib.uchicago.edu/ark:61001/b2np6mb2q02d/',
    'https://ark.lib.uchicago.edu/ark:61001/b2n21p14kh4f/',
    'https://ark.lib.uchicago.edu/ark:61001/b2t371j4534n/',
    'https://ark.lib.uchicago.edu/ark:61001/b2pm0wz05f70/',
    'https://ark.lib.uchicago.edu/ark:61001/b2hf8pr53h5w/',
    'https://ark.lib.uchicago.edu/ark:61001/b2ss7bf2532g/',
    'https://ark.lib.uchicago.edu/ark:61001/b20h13d34p6n/',
    'https://ark.lib.uchicago.edu/ark:61001/b2z57qw38x6t/',
    'https://ark.lib.uchicago.edu/ark:61001/b2jf2703db41/',
    'https://ark.lib.uchicago.edu/ark:61001/b23k4xz12b2n/',
    'https://ark.lib.uchicago.edu/ark:61001/b2hh19v36x5x/',
    'https://ark.lib.uchicago.edu/ark:61001/b2m03t162w1c/',
    'https://ark.lib.uchicago.edu/ark:61001/b2xv7nc0z617/',
    'https://ark.lib.uchicago.edu/ark:61001/b26q3115h46d/',
    'https://ark.lib.uchicago.edu/ark:61001/b21h6xv05h0d/',
    'https://ark.lib.uchicago.edu/ark:61001/b21f9k88bw4z/',
    'https://ark.lib.uchicago.edu/ark:61001/b24d8c45wv6b/',
    'https://ark.lib.uchicago.edu/ark:61001/b29t2ss6jn8d/',
    'https://ark.lib.uchicago.edu/ark:61001/b2571kt69j1h/',
    'https://ark.lib.uchicago.edu/ark:61001/b2bq1dt93091/',
    'https://ark.lib.uchicago.edu/ark:61001/b2t70m723552/',
    'https://ark.lib.uchicago.edu/ark:61001/b2x384510n19/',
    'https://ark.lib.uchicago.edu/ark:61001/b2vb7pd0j09g/',
    'https://ark.lib.uchicago.edu/ark:61001/b2hz2wh6dn39/',
    'https://ark.lib.uchicago.edu/ark:61001/b2d11m85h35n/',
    'https://ark.lib.uchicago.edu/ark:61001/b2hs9nz31p93/',
    'https://ark.lib.uchicago.edu/ark:61001/b2ts58t0kc0m/',
    'https://ark.lib.uchicago.edu/ark:61001/b26m2tw4c100/',
    'https://ark.lib.uchicago.edu/ark:61001/b2n73qx48v7m/',
    'https://ark.lib.uchicago.edu/ark:61001/b2622vh1j128/',
    'https://ark.lib.uchicago.edu/ark:61001/b28f6dj1sj98/',
    'https://ark.lib.uchicago.edu/ark:61001/b2j650d7rc39/',
    'https://ark.lib.uchicago.edu/ark:61001/b2sp8sr1qr6v/',
    'https://ark.lib.uchicago.edu/ark:61001/b2vw8jr6gc6c/',
    'https://ark.lib.uchicago.edu/ark:61001/b2kv54j69w96/',
    'https://ark.lib.uchicago.edu/ark:61001/b2mx0xk0fv4z/',
    'https://ark.lib.uchicago.edu/ark:61001/b2ws36c8zt87/',
    'https://ark.lib.uchicago.edu/ark:61001/b26v6113dn3x/',
    'https://ark.lib.uchicago.edu/ark:61001/b2hf2v20jt50/',
    'https://ark.lib.uchicago.edu/ark:61001/b2939qr4b080/',
    'https://ark.lib.uchicago.edu/ark:61001/b2z18q42tb1f/',
    'https://ark.lib.uchicago.edu/ark:61001/b2h22px34s6m/',
    'https://ark.lib.uchicago.edu/ark:61001/b2sk01z2qk4x/',
    'https://ark.lib.uchicago.edu/ark:61001/b2qs96638g5p/',
    'https://ark.lib.uchicago.edu/ark:61001/b2391vf47w3n/'
)

def regularize_string(_):
    """Regularize a string for browses by trimming excess whitespace,
       converting all whitespace to a single space, etc.

       Parameters: _(str) - a string to regularize.

       Returns:
           str:
    """
    return ' '.join(_.split())


class MLCGraph:
    def __init__(self, config):
        """
        Parameters:
            g (rdflib.Graph): a graph containing triples for the project.
        """
        self.backend = 'http://marklogic.lib.uchicago.edu:8031'
        self.config = config
        self.named_graph = 'http://lib.uchicago.edu/mlc'
        self.requests = requests_cache.CachedSession(REQUESTS_CACHE_DB)

    def get_browse_terms(self, browse_type):
        """
        Get a dictionary of browse terms, along with the series identifiers for
        each term.

        Paramters:
            browse_type (str): e.g., 'contributor', 'creator', 'date',
                'decade', 'language', 'location'

        Returns:
            dict: a Python dictionary, where the key is the browse term and the
            value is a list of series identifiers.

        Notes:
            The date browse converts all dates into decades and is range-aware-
            so an item with the date "1933/1955" will appear in "1930s",
            "1940s", and "1950s".

            I would like to get TGN data as triples.
        """
        browse_types = {
            'contributor': 'http://purl.org/dc/terms/contributor',
            'creator': 'http://purl.org/dc/terms/creator',
            'date': 'http://purl.org/dc/terms/date',
            'decade': 'http://purl.org/dc/terms/date',
            'language': 'http://purl.org/dc/elements/1.1/language',
            'location': 'http://purl.org/dc/terms/spatial'
        }
        assert browse_type in browse_types

        browse_dict = {}
        if browse_type == 'decade':
            qres = self.query(
                '''
                    PREFIX dcterms: <http://purl.org/dc/terms/>

                    SELECT ?date_str ?identifier
                    FROM <{}>
                    WHERE {{
                        ?identifier ?browse_type ?date_str .
                        ?identifier dcterms:hasPart ?_
                    }}
                '''.format(self.named_graph),
                {
                    'browse_type': rdflib.URIRef(browse_types[browse_type])
                }
            )
            for date_str, identifier in qres:
                if str(date_str) == '(:unav)':
                    continue
                dates = []
                for year in date_str.split('/'):
                    match = re.search('([0-9]{4})', year)
                    if match:
                        dates.append(int(match.group(0)))
                if len(dates) == 1:
                    dates.append(dates[0])
                if len(dates) > 2:
                    dates = dates[:2]
                try:
                    year = dates[0]
                except IndexError:
                    print(date_str)
                    sys.exit()
                while year <= dates[1]:
                    decade = str(year)[:3] + '0s'
                    if decade not in browse_dict:
                        browse_dict[decade] = set()
                    browse_dict[decade].add(str(identifier))
                    year += 1
        elif browse_type == 'language':
            qres = self.query(
                '''
                    PREFIX dcterms: <http://purl.org/dc/terms/>
                    PREFIX lexvo: <https://www.iso.org/standard/39534.html>
                    PREFIX skos: <http://www.w3.org/2004/02/skos/core#>

                    SELECT ?browse_term ?identifier
                    FROM <{}>
                    FROM <http://lib.uchicago.edu/glottolog>
                    WHERE {{
                        ?identifier ?browse_type ?code .
                        ?identifier dcterms:hasPart ?_ .
                        ?glottolog_identifier lexvo:iso639P3PCode ?code .
                        ?glottolog_identifier skos:prefLabel ?browse_term
                    }}
                    ORDER BY ?browse_term
                '''.format(self.named_graph),
                {
                    'browse_type': rdflib.URIRef(browse_types[browse_type])
                }
            )
            for browse_term, identifier in qres:
                browse_term = regularize_string(str(browse_term))
                if not browse_term:
                    continue
                if browse_term not in browse_dict:
                    browse_dict[browse_term] = set()
                browse_dict[browse_term].add(regularize_string(str(identifier)))
        elif browse_type == 'location':
            qres = self.query(
                '''
                    PREFIX dcterms: <http://purl.org/dc/terms/>
                    PREFIX skos: <http://www.w3.org/2004/02/skos/core#>

                    SELECT ?browse_term ?identifier
                    FROM <{}>
                    FROM <http://vocab.getty.edu/tgn/>
                    WHERE {{
                        ?identifier ?browse_type ?tgn_number .
                        ?identifier dcterms:hasPart ?_ .
                        BIND(IRI(CONCAT('http://vocab.getty.edu/tgn/', ?tgn_number)) AS ?tgn_iri)
                        ?tgn_iri skos:prefLabel ?browse_term .
                        FILTER langMatches(lang(?browse_term), 'EN')
                    }}
                '''.format(self.named_graph),
                {
                    'browse_type': rdflib.URIRef(browse_types[browse_type])
                }
            )
            for browse_terms, identifier in qres:
                for browse_term in browse_terms.split():
                    browse_term = regularize_string(browse_term)
                    if not browse_term:
                        continue
                    if browse_term not in browse_dict:
                        browse_dict[browse_term] = set()
                    browse_dict[browse_term].add(
                        regularize_string(str(identifier))
                    )
        else:
            qres = self.query(
                '''
                    SELECT ?browse_term ?identifier
                    FROM <{}>
                    WHERE {{
                        ?identifier ?browse_type ?browse_term .
                        ?identifier <http://purl.org/dc/terms/hasPart> ?_
                    }}
                '''.format(self.named_graph),
                {
                    'browse_type': rdflib.URIRef(browse_types[browse_type])
                }
            )
            for labels, identifier in qres:
                for label in labels.split('\n'):
                    label = regularize_string(label)
                    if not label:
                        continue
                    if label not in browse_dict:
                        browse_dict[label] = set()
                    browse_dict[label].add(regularize_string(str(identifier)))

        # convert identifiers set to a list.
        for k in browse_dict.keys():
            browse_dict[k] = sorted(list(browse_dict[k]))

        return browse_dict

    def get_item_dbid(self, item_id):
        """
        Get the database identifier for a given item.

        Parameters:
            item_id (str): a series identifier.

        Returns:
            str: item identifier.
        """

        dbid = ''
        for row in self.query(
            '''
                PREFIX dc: <http://purl.org/dc/elements/1.1/>

                SELECT ?dbid
                FROM <{}>
                WHERE {{
                    ?item_id dc:identifier ?dbid
                }}
            '''.format(self.named_graph),
            {
                'item_id': rdflib.URIRef(item_id)
            }
        ):
            dbid = row[0]
        return dbid

    def get_item_has_panopto_link(self, item_id):
        """
        Return whether an item has a Panopto link or not.

        Parameters:
            item_id (str): a series identifier.

        Returns:
            bool
        """
        has_panopto_link = '0'
        for row in self.query(
            '''
                PREFIX edm: <http://www.europeana.eu/schemas/edm/>

                SELECT ?url
                FROM <{}>
                WHERE {{
                    ?aggregation edm:aggregatedCHO ?item_id .
                    ?aggregation edm:isShownBy ?url
                }}
            '''.format(self.named_graph),
            {
                'item_id': rdflib.URIRef(item_id)
            }
        ):
            has_panopto_link = '1'
        return has_panopto_link

    def get_item_info(self, item_id, get_format_relationships=False):
        """
        Get info for search snippets and page views of a given item.

        Parameters:
            item_id (str): a series identifier.
            get_format_relationships (bool): get format relationships.

        Returns:
            dict: item information.
        """
        data = {}

        for label, p in {
            'content_type': 'http://id.loc.gov/ontologies/bibframe/content',
            'linguistic_data_type':
                'http://lib.uchicago.edu/dma/olacLinguisticDataType',
            'creator': 'http://purl.org/dc/terms/creator',
            'description': 'http://purl.org/dc/elements/1.1/description',
            'identifier': 'http://purl.org/dc/elements/1.1/identifier',
            'medium': 'http://purl.org/dc/terms/medium',
            'titles': 'http://purl.org/dc/elements/1.1/title',
            'alternative_title': 'http://purl.org/dc/terms/alternative',
            'contributor': 'http://purl.org/dc/terms/contributor',
            'date': 'http://purl.org/dc/terms/date',
            'is_part_of': 'http://purl.org/dc/terms/isPartOf',
            'discourse_type':
                'http://www.language−archives.org/OLAC/metadata.html' +
                'discourseType'
        }.items():
            values = set()
            for row in self.query(
                '''
                    SELECT ?value
                    FROM <{}>
                    WHERE {{
                        ?item_id ?p ?value
                    }}
                '''.format(self.named_graph),
                {
                    'p': rdflib.URIRef(p),
                    'item_id': rdflib.URIRef(item_id)
                }
            ):
                values.add(' '.join(row[0].split()))
            data[label] = sorted(list(values))

        # locations
        locations = set()
        for row in self.query(
            '''
                PREFIX dcterms: <http://purl.org/dc/terms/>
                PREFIX skos: <http://www.w3.org/2004/02/skos/core#>

                SELECT ?value
                FROM <{}>
                FROM <http://vocab.getty.edu/tgn/>
                WHERE {{
                    ?item_id dcterms:isPartOf ?_ .
                    ?item_id dcterms:spatial ?tgn_number .
                    BIND(IRI(CONCAT('http://vocab.getty.edu/tgn/', ?tgn_number)) AS ?tgn_iri)
                    ?tgn_iri skos:prefLabel ?value .
                    FILTER (lang(?value) = 'en')
                }}
            '''.format(self.named_graph),
            {
                'item_id': rdflib.URIRef(item_id)
            }
        ):
            locations.add(str(row[0]))
        data['location'] = list(locations)

        # primary_language
        primary_languages = set()
        for row in self.query(
            '''
                PREFIX dcterms: <http://purl.org/dc/terms/>
                PREFIX icu: <http://lib.uchicago.edu/icu/>
                PREFIX lexvo: <https://www.iso.org/standard/39534.html>
                PREFIX skos: <http://www.w3.org/2004/02/skos/core#>
                PREFIX uchicago: <http://lib.uchicago.edu/>

                SELECT DISTINCT ?label
                FROM <{}>
                FROM <http://lib.uchicago.edu/glottolog>
                WHERE {{
                    ?item_id dcterms:isPartOf ?_ .
                    ?item_id uchicago:language ?l .
                    ?l icu:languageRole ?role .
                    FILTER (?role IN ('Both', 'Primary'))
                    ?l lexvo:iso639P3PCode ?code .
                    ?glottolog_identifier lexvo:iso639P3PCode ?code .
                    ?glottolog_identifier skos:prefLabel ?label .
                    FILTER langMatches(lang(?label), 'en')
                }}
            '''.format(self.named_graph),
            {
                'item_id': rdflib.URIRef(item_id)
            }
        ):
            primary_languages.add(str(row[0]))

        data['primary_language'] = list(primary_languages)

        # subject_language
        subject_languages = set()
        for row in self.query(
            '''
                PREFIX dcterms: <http://purl.org/dc/terms/>
                PREFIX icu: <http://lib.uchicago.edu/icu/>
                PREFIX lexvo: <https://www.iso.org/standard/39534.html>
                PREFIX skos: <http://www.w3.org/2004/02/skos/core#>
                PREFIX uchicago: <http://lib.uchicago.edu/>

                SELECT DISTINCT ?label
                FROM <{}>
                FROM <http://lib.uchicago.edu/glottolog>
                WHERE {{
                    ?item_id dcterms:isPartOf ?_ .
                    ?item_id uchicago:language ?l .
                    ?l icu:languageRole ?role .
                    FILTER (?role IN ('Both', 'Subject'))
                    ?l lexvo:iso639P3PCode ?code .
                    ?glottolog_identifier lexvo:iso639P3PCode ?code .
                    ?glottolog_identifier skos:prefLabel ?label .
                    FILTER langMatches(lang(?label), 'en')
                }}
            '''.format(self.named_graph),
            {
                'item_id': rdflib.URIRef(item_id)
            }
        ):
            subject_languages.add(str(row[0]))

        data['subject_language'] = list(subject_languages)

        # has_format
        data['has_format'] = {}

        for row in self.query(
            '''
                PREFIX dc: <http://purl.org/dc/elements/1.1/>
                PREFIX dcterms: <http://purl.org/dc/terms/>
                PREFIX edm: <http://www.europeana.eu/schemas/edm/>

                SELECT ?format_item_id ?format_medium
                FROM <{}>
                WHERE {{
                    ?item_id dcterms:hasFormat ?format_item_id .
                    ?format_item_id dcterms:medium ?format_medium .
                    ?format_item_id dc:identifier ?format_dbid .
                    ?format_agg edm:aggregatedCHO ?format_item_id .
                    BIND( EXISTS {{
                        ?format_agg edm:isShownBy ?_ .
                    }}
                    AS ?has_panopto
                    )
                }}
                ORDER BY DESC(?has_panopto) ?format_dbid
            '''.format(self.named_graph),
            {
                'item_id': rdflib.URIRef(item_id)
            }
        ):
            format_id = str(row[0])
            medium = str(row[1])
            if medium not in data['has_format']:
                data['has_format'][medium] = []
            data['has_format'][medium].append(row[0])

        # is_format_of
        data['is_format_of'] = {}

        for row in self.query(
            '''
                PREFIX dc: <http://purl.org/dc/elements/1.1/>
                PREFIX dcterms: <http://purl.org/dc/terms/>
                PREFIX edm: <http://www.europeana.eu/schemas/edm/>

                SELECT ?format_item_id ?format_medium
                FROM <{}>
                WHERE {{
                    ?item_id dcterms:isFormatOf ?format_item_id .
                    ?format_item_id dcterms:medium ?format_medium .
                    ?format_item_id dc:identifier ?format_dbid .
                    ?format_agg edm:aggregatedCHO ?format_item_id .
                    BIND( EXISTS {{
                        ?format_agg edm:isShownBy ?_ .
                    }}
                    AS
                    ?has_panopto
                    )
                }}
                ORDER BY DESC(?has_panopto) ?format_dbid
            '''.format(self.named_graph),
            {
                'item_id': rdflib.URIRef(item_id)
            }
        ):
            format_id = str(row[0])
            medium = str(row[1])
            if medium not in data['is_format_of']:
                data['is_format_of'][medium] = []
            data['is_format_of'][medium].append(row[0])

        # JEJ
        # load item hasFormat / isFormatOf relationships
        if get_format_relationships:
            for format_relationship in ('has_format', 'is_format_of'):
                if format_relationship in data:
                    for medium in data[format_relationship].keys():
                        for i in range(len(data[format_relationship][medium])):
                            url = data[format_relationship][medium][i]
                            data[format_relationship][medium][i] = self.get_item_info(url)

        # panopto links
        panopto_links = set()
        for row in self.query(
            '''
                PREFIX edm: <http://www.europeana.eu/schemas/edm/>

                SELECT ?panopto_link
                FROM <{}>
                WHERE {{
                    ?aggregation edm:aggregatedCHO ?item_id .
                    ?aggregation edm:isShownBy ?panopto_link
                }}
            '''.format(self.named_graph),
            {
                'item_id': rdflib.URIRef(item_id)
            }
        ):
            panopto_links.add(str(row[0]))
        data['panopto_links'] = list(panopto_links)

        # panopto identifiers
        panopto_identifiers = set()
        panopto_prefix = 'https://uchicago.hosted.panopto.com/Panopto/Pages/Embed.aspx?id='
        for row in self.query(
            '''
                PREFIX dcterms: <http://purl.org/dc/terms/>

                SELECT ?identifier
                FROM <{}>
                WHERE {{
                    ?web_resource dcterms:identifier ?identifier
                }}
            '''.format(self.named_graph),
            {
                'web_resource': rdflib.URIRef(item_id + '/file.wav')
            }
        ):
            if str(row[0]).startswith(panopto_prefix):
                panopto_identifiers.add(str(row[0]).replace(panopto_prefix, ''))
        data['panopto_identifiers'] = list(panopto_identifiers)

        # access rights
        access_rights = set()
        for row in self.query(
            '''
                PREFIX dcterms: <http://purl.org/dc/terms/>

                SELECT ?access_rights
                FROM <{}>
                WHERE {{
                    ?item_id dcterms:isPartOf ?series_id .
                    ?series_id dcterms:accessRights ?access_rights
                }}
            '''.format(self.named_graph),
            {
                'item_id': rdflib.URIRef(item_id)
            }
        ):
            access_rights.add(str(row[0]))
        data['access_rights'] = list(access_rights)

        # OVERRIDE AS PER JL, UNTIL MORE ITEMS IN THE DB ARE SET TO PUBLIC DOMAIN.
        if item_id in ADJUST_PERMISSIONS_FOR:
            data['access_rights'] = ['Public domain']

        data['ark'] = item_id

        return data

    def get_item_identifiers(self):
        """
        Get all item identifiers from the graph.

        Parameters:
            None

        Returns:
            list: item identifiers.
        """
        qres = self.query(
            '''
                PREFIX dcterms: <http://purl.org/dc/terms/>

                SELECT ?item_id
                FROM <{}>
                WHERE {{
                    ?_ dcterms:hasPart ?item_id
                }}
            '''.format(self.named_graph)
        )

        results = set()
        for row in qres:
            results.add(str(row[0]))
        return sorted(list(results))

    def get_item_identifiers_for_series(self, i):
        """
        Get the item identifiers for a given series.

        Parameters:
            i (str): a series identifier.

        Returns:
            list: a list of item identifiers.
        """
        r = self.query(
            '''
                PREFIX dcterms: <http://purl.org/dc/terms/>

                SELECT ?item_id
                FROM <{}>
                WHERE {{
                    ?series_id dcterms:hasPart ?item_id
               }}
            '''.format(self.named_graph),
            {
                'series_id': rdflib.URIRef(i)
            }
        )

        results = set()
        for row in r:
            results.add(str(row[0]))
        return sorted(list(results))

    def get_item_medium(self, item_id):
        """
        Get the medium for a given item.

        Parameters:
            item_id (str): a series identifier.

        Returns:
            str: medium
        """
        medium = ''
        for row in self.query(
            '''
                PREFIX dcterms: <http://purl.org/dc/terms/>

                SELECT ?medium
                FROM <{}>
                WHERE {{
                    ?item_id dcterms:medium ?medium
                }}
            '''.format(self.named_graph),
            {
                'item_id': rdflib.URIRef(item_id)
            }
        ):
            medium = str(row[0])
        return medium

    def get_search_tokens_for_identifier(self, i):
        """
        Get the search tokens for a given series or item identifier from the
        graph.

        Parameters:
            i (str): a series identifier

        Returns:
            str: a string that can be searched via SQLite.
        """

        search_tokens = []

        # non-blank triples with no special processing
        for p in (
            'http://purl.org/dc/elements/1.1/description',
            'http://purl.org/dc/elements/1.1/title',
            'http://purl.org/dc/terms/alternative',
            'http://purl.org/dc/terms/creator',
            'http://purl.org/dc/terms/contributor',
            'http://www.language−archives.org/OLAC/metadata.htmldiscourseType',
            'http://lib.uchicago.edu/dma/contentType'
        ):
            r = self.query(
                '''
                    SELECT ?o
                    FROM <{}>
                    WHERE {{
                        ?series_id ?p ?o
                    }}
                '''.format(self.named_graph),
                {
                    'p': rdflib.URIRef(p),
                    'series_id': rdflib.URIRef(i)
                }
            )
            for row in r:
                search_tokens.append(str(row[0]))

        # fn:collection
        r = self.query(
            '''
                PREFIX fn: <http://www.w3.org/2005/xpath-functions>

                SELECT ?o
                FROM <{}>
                WHERE {{
                    ?series_aggregation_id fn:collection ?o .
                }}
            '''.format(self.named_graph),
            {
                'p': rdflib.URIRef(p),
                'series_aggregation_id': rdflib.URIRef(i + '/aggregation')
            }
        )
        lookup = {
            'dma': 'Digital Media Archive'
        }
        for row in r:
            if str(row[0]) in lookup:
                search_tokens.append(lookup[str(row[0])])

        # dc:language
        r = self.query(
            '''
                PREFIX dc: <http://purl.org/dc/elements/1.1/>

                SELECT ?o
                FROM <{}>
                WHERE {{
                    ?series_id dc:language ?o
                }}
            '''.format(self.named_graph),
            {
                'series_id': rdflib.URIRef(i)
            }
        )
        for row in r:
            for label in self.glottolog_lookup.get_glottolog_language_names(str(row[0])):
                search_tokens.append(label)

        # dcterms:spatial
        r = self.query(
            '''
                PREFIX dcterms: <http://purl.org/dc/terms/>

                SELECT ?o
                FROM <{}>
           
                WHERE {{
                    ?series_id dcterms:spatial ?o
                }}
            '''.format(self.named_graph),
            {
                'series_id': rdflib.URIRef(i)
            }
        )
        for row in r:
            for tgn_identifier in str(row[0]).split():
                for label in self.get_tgn_place_names(tgn_identifier):
                    search_tokens.append(label)

        # series-level dc:date
        years = set()
        r = self.query(
            '''
                PREFIX dcterms: <http://purl.org/dc/terms/>

                SELECT ?o
                WHERE {{
                    ?series_id dcterms:date ?o
                }}
            '''.format(self.named_graph),
            {
                'series_id': rdflib.URIRef(i)
            }
        )
        for row in r:
            date_str = str(row[0])
            year_strs = []
            for year_str in date_str.split('/'):
                if year_str.isnumeric() and len(year_str) == 4:
                    year_strs.append(int(year_str))
            if len(year_strs) == 1:
                years.add(str(year_strs[0]))
            elif len(year_strs) > 1:
                year_strs.sort()
                y = year_strs[0]
                while y <= year_strs[-1]:
                    years.add(str(y))
                    y += 1
        for y in sorted(list(years)):
            search_tokens.append(y)

        # replace all whitespace with single spaces and return all search
        # tokens in a single string.
        return ' '.join([' '.join(s.split()) for s in search_tokens])

    def get_series_date(self, i):
        """
        Get a single date for a given series identifier from the graph.

        Parameters:
            i (str): a series identifier

        Returns:
            str: a four-digit year (YYYY) or a year range (YYYY/YYYY)
        """
        years = []
        for row in self.query(
            '''
                PREFIX dcterms: <http://purl.org/dc/terms/>

                SELECT ?date
                FROM <{}>
                WHERE {{
                    ?identifier dcterms:date ?date
                }}
            '''.format(self.named_graph),
            {
                'identifier': rdflib.URIRef(i)
            }
        ):
            for year in row[0].split('/'):
                years.append(year)

        if len(years) == 0:
            return ''

        if len(years) == 1:
            return years[0]

        years = sorted(years)
        return '/'.join([years[0], years[-1]])

    def get_series_dbid(self, i):
        """
        Get a single database identifier for a given series identifier.

        Parameters:
            i (str): a series identifier

        Returns:
            str: a database identifier.
        """
        dbids = []
        for row in self.query(
            '''
                PREFIX dc: <http://purl.org/dc/elements/1.1/>

                SELECT ?dbid
                FROM <{}>
                WHERE {{
                    ?identifier dc:identifier ?dbid
                }}
            '''.format(self.named_graph),
            {
                'identifier': rdflib.URIRef(i)
            }
        ):
            dbids.append(str(row[0]))

        if len(dbids) == 0:
            return ''
        return dbids[0]

    def get_series_identifiers(self):
        """
        Get all series identifiers from the graph.

        Parameters:
            None

        Returns:
            list: series identifiers.
        """
        return sorted(self.get_series_item_lookup().keys())

    def get_series_identifiers_for_item(self, i):
        """
        Get the series identifiers for a given item.

        Parameters:
            i (str): an item identifier.

        Returns:
            list: a list of series identifiers.
        """
        series_ids = []
        for series_id, item_ids in self.get_series_item_lookup().items():
            if i in item_ids:
                series_ids.append(series_id)
        return series_ids

    def get_series_info(self, series_id):
        """
        Get info for search snippets and page views for a given series.

        Parameters:
            series_id (str): a series identifier.

        Returns:
            str: series title.
        """
        data = {}

        for label, p in {
            'content_type': 'http://id.loc.gov/ontologies/bibframe/content',
            'creator': 'http://purl.org/dc/terms/creator',
            'description': 'http://purl.org/dc/elements/1.1/description',
            'identifier': 'http://purl.org/dc/elements/1.1/identifier',
            'titles': 'http://purl.org/dc/elements/1.1/title',
            'access_rights': 'http://purl.org/dc/terms/accessRights',
            'alternative_title': 'http://purl.org/dc/terms/alternative',
            'contributor': 'http://purl.org/dc/terms/contributor',
            'date': 'http://purl.org/dc/terms/date'
        }.items():
            values = set()
            for row in self.query(
                '''
                    SELECT ?value
                    FROM <{}>
                    WHERE {{
                        ?series_id ?p ?value
                    }}
                '''.format(self.named_graph),
                {
                    'p': rdflib.URIRef(p),
                    'series_id': rdflib.URIRef(series_id)
                }
            ):
                values.add(' '.join(row[0].split()))
            data[label] = sorted(list(values))

        # locations
        locations = set()
        for row in self.query(
            '''
                PREFIX dcterms: <http://purl.org/dc/terms/>
                PREFIX skos: <http://www.w3.org/2004/02/skos/core#>

                SELECT ?value
                FROM <{}>
                FROM <http://vocab.getty.edu/tgn/>
                WHERE {{
                    ?series_id dcterms:hasPart ?_ .
                    ?series_id dcterms:spatial ?tgn_number .
                    BIND(IRI(CONCAT('http://vocab.getty.edu/tgn/', ?tgn_number)) AS ?tgn_iri)
                    ?tgn_iri skos:prefLabel ?value .
                    FILTER (lang(?value) = 'en')
                }}
            '''.format(self.named_graph),
            {
                'series_id': rdflib.URIRef(series_id)
            }
        ):
            locations.add(str(row[0]))
        data['location'] = list(locations)

        # primary_language
        primary_languages = set()
        for row in self.query(
            '''
                PREFIX dcterms: <http://purl.org/dc/terms/>
                PREFIX icu: <http://lib.uchicago.edu/icu/>
                PREFIX lexvo: <https://www.iso.org/standard/39534.html>
                PREFIX skos: <http://www.w3.org/2004/02/skos/core#>
                PREFIX uchicago: <http://lib.uchicago.edu/>

                SELECT DISTINCT ?label
                FROM <{}>
                FROM <http://lib.uchicago.edu/glottolog>
                WHERE {{
                    ?series_id dcterms:hasPart ?_ .
                    ?series_id uchicago:language ?l .
                    ?l icu:languageRole ?role .
                    FILTER (?role IN ('Both', 'Primary'))
                    ?l lexvo:iso639P3PCode ?code .
                    ?glottolog_identifier lexvo:iso639P3PCode ?code .
                    ?glottolog_identifier skos:prefLabel ?label .
                    FILTER langMatches(lang(?label), 'en')
                }}
            '''.format(self.named_graph),
            {
                'series_id': rdflib.URIRef(series_id)
            }
        ):
            primary_languages.add(str(row[0]))

        data['primary_language'] = list(primary_languages)

        # subject_language
        subject_languages = set()
        for row in self.query(
            '''
                PREFIX dcterms: <http://purl.org/dc/terms/>
                PREFIX icu: <http://lib.uchicago.edu/icu/>
                PREFIX lexvo: <https://www.iso.org/standard/39534.html>
                PREFIX skos: <http://www.w3.org/2004/02/skos/core#>
                PREFIX uchicago: <http://lib.uchicago.edu/>

                SELECT DISTINCT ?label
                FROM <{}>
                FROM <http://lib.uchicago.edu/glottolog>
                WHERE {{
                    ?series_id dcterms:hasPart ?_ .
                    ?series_id uchicago:language ?l .
                    ?l icu:languageRole ?role .
                    FILTER (?role IN ('Both', 'Subject'))
                    ?l lexvo:iso639P3PCode ?code .
                    ?glottolog_identifier lexvo:iso639P3PCode ?code .
                    ?glottolog_identifier skos:prefLabel ?label .
                    FILTER langMatches(lang(?label), 'en')
                }}
            '''.format(self.named_graph),
            {
                'series_id': rdflib.URIRef(series_id)
            }
        ):
            subject_languages.add(str(row[0]))

        data['subject_language'] = list(subject_languages)

        data['ark'] = series_id

        return data

    def get_series_item_lookup(self):
        """Get a series/item lookup.

        Parameters:
            (None)

        Returns:
            dict: a dictionary, where keys are series identifiers and values
                  are lists of item identifiers.
        """
        lookup = {}

        for row in self.query(
            '''
                PREFIX dcterms: <http://purl.org/dc/terms/>

                SELECT ?series_id ?item_id
                FROM <{}>
                WHERE {{
                    ?series_id dcterms:hasPart ?item_id
                }}
            '''.format(self.named_graph)
        ):
            series_id = row[0]
            item_id = row[1]

            if series_id not in lookup:
                lookup[series_id] = set()
            lookup[series_id].add(item_id)

        for series_id in lookup.keys():
            lookup[series_id] = sorted(list(lookup[series_id]))
        return lookup

    def search_items(self, search_term, sort_type = 'rank'):
        """
        Get items matching a search. 

        Parameters:
            search_term (str): a search string.
            sort_type (str): e.g., 'rank', 'date'

        Returns:
            list: a list of item identifiers.
        """
        q = '''PREFIX cts: <http://marklogic.com/cts#>
               PREFIX dc: <http://purl.org/dc/elements/1.1/>
               PREFIX dcterms: <http://purl.org/dc/terms/>
               PREFIX dma: <http://lib.uchicago.edu/dma/>
               PREFIX edm: <http://www.europeana.eu/schemas/edm/>
               PREFIX fn: <http://www.w3.org/2005/xpath-functions>
               PREFIX lexvo: <https://www.iso.org/standard/39534.html>
               PREFIX olac: <http://www.language−archives.org/OLAC/metadata.html>
               PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
               
               SELECT DISTINCT ?item
               FROM <{}>
               FROM <http://lib.uchicago.edu/glottolog>
               WHERE {{
                 ?item dcterms:isPartOf ?_ .
                 {{
                   {{
                     ?item dc:description ?description .
                     FILTER cts:contains (?description, cts:word-query(?search_term))
                   }} UNION {{
                     ?item dc:title ?title .
                     FILTER cts:contains (?title, cts:word-query(?search_term))
                   }} UNION {{
                     ?item dcterms:alternative ?alternative .
                     FILTER cts:contains (?alternative, cts:word-query(?search_term))
                   }} UNION {{
                     ?item dcterms:creator ?creator .
                     FILTER cts:contains (?creator, cts:word-query(?search_term))
                   }} UNION {{
                     ?item dcterms:contributor ?contributor .
                     FILTER cts:contains (?contributor, cts:word-query(?search_term))
                   }} UNION {{
                     ?item dc:language ?language_code . 
                     ?glottolog lexvo:iso639P3PCode ?language_code .
                     ?glottolog rdfs:label ?language_string . 
                     FILTER cts:contains(?language_string, cts:word-query(?search_term))
                   }} UNION {{
                     ?item olac:discourseType ?discourse_type .
                     FILTER cts:contains (?discourse_type, cts:word-query(?search_term))
                   }} UNION {{
                     ?item dma:contentType ?content_type .
                     FILTER cts:contains (?content_type, cts:word-query(?search_term))
                   }}
                 }}
               }}'''.format(self.named_graph)
    
        # replace whitespace with single space.
        q = ' '.join(q.split())

        params = [
            ('query', q),
            ('bind:search_term', search_term)
        ]

        u = '{}/v1/graphs/sparql?{}'.format(
            MARKLOGIC,
            urllib.parse.urlencode(params)
        )
        results = requests.get(u).json()

        identifiers = []
        for binding in results['results']['bindings']:
            identifiers.append(binding['item']['value'])
        return identifiers

    def search_series(self, search_term, sort_type = 'rank'):
        """
        Get series matching a search. 

        Parameters:
            search_term (str): a search string.
            sort_type (str): e.g., 'rank', 'date'

        Returns:
            list: a list of series identifiers.
        """
        q = '''PREFIX cts: <http://marklogic.com/cts#>
               PREFIX dc: <http://purl.org/dc/elements/1.1/>
               PREFIX dcterms: <http://purl.org/dc/terms/>
               PREFIX dma: <http://lib.uchicago.edu/dma/>
               PREFIX edm: <http://www.europeana.eu/schemas/edm/>
               PREFIX fn: <http://www.w3.org/2005/xpath-functions>
               PREFIX lexvo: <https://www.iso.org/standard/39534.html>
               PREFIX olac: <http://www.language−archives.org/OLAC/metadata.html>
               PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
               
               SELECT DISTINCT ?series
               FROM <{}>
               FROM <http://lib.uchicago.edu/glottolog>
               WHERE {{
                 {{
                   ?series dcterms:hasPart ?item .
                   {{
                     ?item dc:description ?description .
                     FILTER cts:contains (?description, cts:word-query(?search_term))
                   }} UNION {{
                     ?item dc:title ?title .
                     FILTER cts:contains (?title, cts:word-query(?search_term))
                   }} UNION {{
                     ?item dcterms:alternative ?alternative .
                     FILTER cts:contains (?alternative, cts:word-query(?search_term))
                   }} UNION {{
                     ?item dcterms:creator ?creator .
                     FILTER cts:contains (?creator, cts:word-query(?search_term))
                   }} UNION {{
                     ?item dcterms:contributor ?contributor .
                     FILTER cts:contains (?contributor, cts:word-query(?search_term))
                   }} UNION {{
                     ?item dc:language ?language_code . 
                     ?glottolog lexvo:iso639P3PCode ?language_code .
                     ?glottolog rdfs:label ?language_string . 
                     FILTER cts:contains(?language_string, cts:word-query(?search_term))
                   }} UNION {{
                     ?item olac:discourseType ?discourse_type .
                     FILTER cts:contains (?discourse_type, cts:word-query(?search_term))
                   }} UNION {{
                     ?item dma:contentType ?content_type .
                     FILTER cts:contains (?content_type, cts:word-query(?search_term))
                   }}
                 }} UNION {{
                   ?series dc:title ?title .
                   FILTER cts:contains (?title, cts:word-query(?search_term))
                 }} UNION {{
                   ?series dcterms:alternative ?alternative .
                   FILTER cts:contains (?alternative, cts:word-query(?search_term))
                 }} UNION {{
                   ?series dc:description ?description .
                   FILTER cts:contains (?description, cts:word-query(?search_term))
                 }} UNION {{
                   ?aggregation edm:aggregatedCHO ?series .
                   ?aggregation fn:collection ?collection .
                   FILTER cts:contains(?collection, cts:word-query(?search_term))
                 }} UNION {{
                   ?series dc:language ?language_code .
                   ?glottolog lexvo:iso639P3PCode ?language_code .
                   ?glottolog rdfs:label ?language_string . 
                   FILTER cts:contains(?language_string, cts:word-query(?search_term))
                 }} UNION {{
                   ?series dcterms:spatial ?spatial .
                   FILTER cts:contains(?spatial, cts:word-query(?search_term))
                 }} UNION {{
                   ?series dcterms:date ?date .
                   FILTER cts:contains(?date, cts:word-query(?search_term))
                 }} UNION {{
                   ?series dma:contentType ?content_type .
                   FILTER cts:contains (?content_type, cts:word-query(?search_term))
                 }}
               }}'''.format(self.named_graph)
    
        # replace whitespace with single space.
        q = ' '.join(q.split())

        params = [
            ('query', q),
            ('bind:search_term', search_term)
        ]

        u = '{}/v1/graphs/sparql?{}'.format(
            MARKLOGIC,
            urllib.parse.urlencode(params)
        )
        results = requests.get(u).json()

        identifiers = []
        for binding in results['results']['bindings']:
            identifiers.append(binding['series']['value'])
        return identifiers

    def search(self, search_term, facets=[], sort_type = 'rank'):
        """
        Get series matching a search. 

        Parameters:
            search_term (str): a search string.
            facets (list):     a list of strings, where each string begins with a
                               browse/facet type, followed by a colon, followed
                               by the term.
            sort_type (str): e.g., 'rank', 'date'

        Returns:
            list: a list, where each element contains a three-tuple with a
                  series identifier, a list of item identifiers with hits in
                  that series, and a rank.
        """
        '''
        # we may want to do this differently, by getting identifiers from the browses ahead of time.
        for i, facet in enumerate(facets):
            match = re.match('^([^:]*):(.*)$', facet)
            params.append(('bind:browsetype' + str(i), match.group(1)))
            params.append(('bind:browseterm' + str(i), match.group(2)))
        '''

        # by default, all identifiers are searchable.
        facet_identifiers = set(self.get_series_identifiers())

        # get the set of identifiers that is present in all active facets.
        for facet in facets:
            match = re.match('^([^:]*):(.*)$', facet)
            browse_type = match_group(1)
            browse_term = match.group(2)
            assert browse_term in ('contributor', 'creator', 'date', 'decade',
                'language', 'location')
            browse_terms = self.get_browse_terms(browse_term)
            if browse_term in browse_terms:
                facet_identifiers |= set(browse_terms[browse_term])

        # retrieve search results, filtering for active facets.
        results = []
        for s in self.search_series(search_term, sort_type):
            if s in facet_identifiers:
                results.append([s, [], 0.0])

        # retrieve item results.
        item_results = self.search_items(search_term)

        # get the series/item lookup.
        lookup = self.get_series_item_lookup()

        # add items to results. 
        for i in range(len(results)):
            s = results[i][0]
            for item in item_results:
                if item in lookup[s]:
                    results[i][1].append(item)

        return results

    def query(self, s, b = {}):
        """Query the triplestore. 

        Parameters:
            s (str): a SPARQL query.
            b (dict): variable bindings for the query.

        Returns:
            a list of tuples, like those returned by rdflib's graph.query().
        """
        # convert all whitespace to a single space, trim string.
        s = ' '.join(s.split())
        
        # build a list of tuples to submit as GET request URL params.
        params = [('query', s)]
        for k, v in b.items():
            params.append(('bind:' + k, str(v)))

        r = self.requests.get('{}/v1/graphs/sparql?{}'.format(
            self.backend,
            urllib.parse.urlencode(params)
        ))
        data = r.json()

        # handle errors.
        if 'errorResponse' in data:
            sys.stderr.write(r.text)
            sys.exit()

        # collect output into a list of lists, like rdflib's graph.query().
        output = []
        for result in data['results']['bindings']:
            row = []
            for var in data['head']['vars']:
                if result[var]['type'] in ('literal', 'uri'):
                    v = result[var]['value']
                else:
                    raise NotImplementedError
                row.append(v)
            output.append(row)

        return output

import json, os, rdflib, requests, requests_cache, sqlite3, sys, timeit, urllib.parse
from docopt import docopt
from rdflib.plugins.sparql import prepareQuery

import regex as re

requests_cache.install_cache('requests_cache')

def regularize_string(s):
    """Regularize a string for browses by trimming excess whitespace, 
       converting all whitespace to a single space, etc.
  
       Parameters: s(str) - a string to regularize.
 
       Returns:
           str: 
    """
    return ' '.join(s.split())

class MLCGraph:
    def __init__(self, g):
        """
        Parameters:
            g (rdflib.Graph): a graph containing triples for the project.
        """
        self.g = g

    def get_browse_terms(self, browse_type, sort_key='label'):
        """
        Get a dictionary of browse terms, along with the items for each term. It's
        currently not documented whether a browse should return series nodes, item
        nodes, or both - so this includes both. 
    
        Paramters:
            browse_type (str): e.g., 'contributor', 'creator', 'date',
                'decade', 'language', 'location'
            sort_key (str): e.g., 'count', 'label'
    
        Returns:
            dict: a Python dictionary, where the key is the browse term and the
            value is a list of identifiers. 
    
        Notes:
            The date browse converts all dates into decades and is range-aware-
            so an item with the date "1933/1955" will appear in "1930s", "1940s",
            and "1950s".
    
            When I try to match our dc:language to Glottolog's lexvo:iso639P3PCode,
            I run into trouble in Python's rdflib because Glottolog's data has an
            explicit datatype of xsd:string() and ours doesn't have an explicit
            datatype. Making both match manually solves the problem. We may be able
            to solve this in MarkLogic by casting the variable. 
    
            Here I solved the problem by manually editing the glottolog triples 
            so they match ours. 
    
            I would like to get TGN data as triples. 
    
            Go to http://vocab.getty.edu/sparql.
        """
        browse_types = {
            'contributor': 'http://purl.org/dc/terms/contributor',
            'creator':     'http://purl.org/dc/terms/creator',
            'date':        'http://purl.org/dc/terms/date',
            'decade':      'http://purl.org/dc/terms/date',
            'language':    'http://purl.org/dc/elements/1.1/language',
            'location':    'http://purl.org/dc/terms/spatial'
        }
        assert browse_type in browse_types
    
        browse_dict = {}
        if browse_type == 'decade':
            qres = self.g.query(
                prepareQuery('''
                    SELECT ?date_str ?identifier 
                    WHERE {{
                        ?identifier ?browse_type ?date_str .
                        ?identifier <http://purl.org/dc/terms/hasPart> ?_
                    }}
                '''),
                initBindings={
                    'browse_type': rdflib.URIRef(browse_types[browse_type])
                }
            )
            for date_str, identifier in qres:
                dates = []
                for s in date_str.split('/'):
                    m = re.search('([0-9]{4})', s)
                    if m:
                        dates.append(int(m.group(0)))
                if len(dates) == 1:
                    dates.append(dates[0])
                if len(dates) > 2:
                    dates = dates[:2] 
                d = dates[0]
                while d <= dates[1]:
                    decade = str(d)[:3] + '0s'
                    if not decade in browse_dict:
                        browse_dict[decade] = set()
                    browse_dict[decade].add(str(identifier))
                    d += 1
        elif browse_type == 'language':
            qres = self.g.query(
                prepareQuery('''
                    SELECT ?browse_term ?identifier 
                    WHERE {
                        ?identifier ?browse_type ?browse_term .
                        ?identifier <http://purl.org/dc/terms/hasPart> ?_
                    }
                '''),
                initBindings={
                    'browse_type': rdflib.URIRef(browse_types[browse_type])
                }
            )
            for browse_term, identifier in qres:
                browse_term = regularize_string(str(browse_term))
                for label in self.get_glottolog_language_names_preferred(
                    browse_term
                ):
                    label = regularize_string(label)
                    if not label:
                        continue
                    if not label in browse_dict:
                        browse_dict[label] = set()
                    browse_dict[label].add(regularize_string(str(identifier)))
        elif browse_type == 'location':
            qres = self.g.query(
                prepareQuery('''
                    SELECT ?browse_term ?identifier 
                    WHERE {
                        ?identifier ?browse_type ?browse_term .
                        ?identifier <http://purl.org/dc/terms/hasPart> ?_
                    }
                '''),
                initBindings={
                    'browse_type': rdflib.URIRef(browse_types[browse_type])
                }
            )
            for browse_terms, identifier in qres:
                for browse_term in browse_terms.split():
                    browse_term = regularize_string(browse_term)
                    for label in self.get_tgn_place_names_preferred(
                        browse_term
                    ):
                        label = regularize_string(label)
                        if not label:
                            continue
                        if not label in browse_dict:
                            browse_dict[label] = set()
                        browse_dict[label].add(regularize_string(str(identifier)))
        else:
            qres = self.g.query(
                prepareQuery('''
                    SELECT ?browse_term ?identifier 
                    WHERE {
                        ?identifier ?browse_type ?browse_term .
                        ?identifier <http://purl.org/dc/terms/hasPart> ?_
                    }
                '''),
                initBindings={
                    'browse_type': rdflib.URIRef(browse_types[browse_type])
                }
            )
            for labels, identifier in qres:
                for label in labels.split('\n'):
                    label = regularize_string(label)
                    if not label:
                        continue
                    if not label in browse_dict:
                        browse_dict[label] = set()
                    browse_dict[label].add(regularize_string(str(identifier)))
    
        # convert identifiers set to a list.
        for k in browse_dict.keys():
            browse_dict[k] = sorted(list(browse_dict[k]))
    
        return browse_dict

    def get_glottolog_codes(self):
        """Get all ISO639P3P Codes from the Glottolog graph.
    
        Parameters:
            (none)
    
        Returns:
            list: all identifiers. 
        """
        results = set()
        for row in self.g.query('''
            SELECT ?code
            WHERE {
                ?_ <https://www.iso.org/standard/39534.htmliso639P3PCode> ?code
            }
        '''):
            results.add(str(row[0]))
        return results
    
    def get_glottolog_language_names(self, c):
        """Get all language names from Glottolog for a given identifier. 
     
        Parameters:
            c (str): ISO 639P3P code, e.g., "eng"
    
        Returns:
            list: a list of language names as unicode strings.
        """
        results = set()
        for row in self.g.query(
            prepareQuery('''
                SELECT ?label
                WHERE {
                    ?identifier <https://www.iso.org/standard/39534.htmliso639P3PCode> ?code .
                    {
                        ?identifier <http://www.w3.org/2004/02/skos/core#altLabel> ?label
                    } UNION {
                        ?identifier <http://www.w3.org/2004/02/skos/core#prefLabel> ?label
                    }
                    
                }
            '''),
            initBindings={
                'code': rdflib.Literal(c, datatype=rdflib.XSD.string)
            }
        ):
            results.add(str(row[0]).strip())
        return list(results)
      
    def get_glottolog_language_names_preferred(self, c):
        """Get preferred language names from Glottolog.
    
        Parameters:
            c (str): ISO 639P3P code, e.g., "eng"
    
        Returns:
            list: a list of language names, e.g., "English"
        """
        results = set()
        for row in self.g.query(
            prepareQuery('''
                SELECT ?label
                WHERE {
                    ?identifier <https://www.iso.org/standard/39534.htmliso639P3PCode> ?code .
                    ?identifier <http://www.w3.org/2004/02/skos/core#prefLabel> ?label
                }
            '''),
            initBindings={
                'code': rdflib.Literal(c, datatype=rdflib.XSD.string)
            }
        ):
            results.add(str(row[0]).strip())
        return list(results)

    def get_item_dbid(self, item_id):
        """
        Get the database identifier for a given item.

        Parameters:
            item_id (str): a series identifier.

        Returns:
            str: item identifier.
        """
        dbid = ''
        for row in self.g.query(
            prepareQuery('''
                SELECT ?dbid
                WHERE {
                    ?item_id <http://purl.org/dc/elements/1.1/identifier> ?dbid
                }
            '''),
            initBindings={
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
        for row in self.g.query(
            prepareQuery('''
                SELECT ?url
                WHERE {
                    ?aggregation <http://www.europeana.eu/schemas/edm/aggregatedCHO> ?item_id .
                    ?aggregation <http://www.europeana.eu/schemas/edm/isShownBy> ?url
                }
            '''),
            initBindings={
                'item_id': rdflib.URIRef(item_id)
            }
        ):
            has_panopto_link = '1'
        return has_panopto_link

    def get_item_info(self, item_id):
        """
        Get info for search snippets and page views of a given item.
    
        Parameters:
            item_id (str): a series identifier.
    
        Returns:
            dict: item information.
        """
        data = {}
    
        for label, p in {
            'content_type':         'http://id.loc.gov/ontologies/bibframe/content',
            'linguistic_data_type': 'http://lib.uchicago.edu/dma/olacLinguisticDataType',
            'creator':              'http://purl.org/dc/terms/creator',
            'description':          'http://purl.org/dc/elements/1.1/description',
            'identifier':           'http://purl.org/dc/elements/1.1/identifier',
            'medium':               'http://purl.org/dc/terms/medium',
            'titles':               'http://purl.org/dc/elements/1.1/title',
            'alternative_title':    'http://purl.org/dc/terms/alternative',
            'contributor':          'http://purl.org/dc/terms/contributor',
            'date':                 'http://purl.org/dc/terms/date',
            'is_part_of':           'http://purl.org/dc/terms/isPartOf',
            'location':             'http://purl.org/dc/terms/spatial',
            'discourse_type':       'http://www.language−archives.org/OLAC/metadata.htmldiscourseType'
        }.items():
            values = set()
            for row in self.g.query(
                prepareQuery('''
                    SELECT ?value
                    WHERE {
                        ?item_id ?p ?value
                    }
                '''),
                initBindings={
                    'p': rdflib.URIRef(p),
                    'item_id': rdflib.URIRef(item_id)
                }
            ):
                values.add(' '.join(row[0].split()))
            data[label] = sorted(list(values))

        # convert TGN identifiers to preferred names.
        tgn_identifiers = set()
        for i in data['location']:
            for j in i.split():
                tgn_identifiers.add(j)

        data['location'] = []
        for i in tgn_identifiers:
            for preferred_name in self.get_tgn_place_names_preferred(
                i
            ):
                data['location'].append(preferred_name)
   
        # primary_language
        codes = set()
        for row in self.g.query(
            prepareQuery('''
                SELECT ?code
                WHERE {
                    ?item_id <http://lib.uchicago.edu/language> ?l .
                    ?l <http://lib.uchicago.edu/icu/languageRole> ?role .
                    ?l <https://www.iso.org/standard/39534.htmliso639P3PCode> ?code .
                    FILTER (?role IN ('Both', 'Primary'))
                }
            '''),
            initBindings={
                'item_id': rdflib.URIRef(item_id)
            }
        ):
            codes.add(row[0])

        preferred_names = set()
        for c in codes:
            for preferred_name in self.get_glottolog_language_names_preferred(
                c
            ):
                preferred_names.add(preferred_name)

        data['primary_language'] = []
        for preferred_name in preferred_names:
            data['primary_language'].append(preferred_name)

        # subject_language
        codes = set()
        for row in self.g.query(
            prepareQuery('''
                SELECT ?code
                WHERE {
                    ?item_id <http://lib.uchicago.edu/language> ?l .
                    ?l <http://lib.uchicago.edu/icu/languageRole> ?role .
                    ?l <https://www.iso.org/standard/39534.htmliso639P3PCode> ?code .
                    FILTER (?role IN ('Both', 'Subject'))
                }
            '''),
            initBindings={
                'item_id': rdflib.URIRef(item_id)
            }
        ):
            codes.add(row[0])

        preferred_names = set()
        for c in codes:
            for preferred_name in self.get_glottolog_language_names_preferred(
                c
            ):
                preferred_names.add(preferred_name)

        data['subject_language'] = []
        for preferred_name in preferred_names:
            data['subject_language'].append(preferred_name)

        # has_format
        data['has_format'] = []

        for row in self.g.query(
            prepareQuery('''
                SELECT ?has_format_item_id
                WHERE {
                    ?item_id <http://purl.org/dc/terms/hasFormat> ?has_format_item_id .
                    ?has_format_item_id <http://purl.org/dc/elements/1.1/identifier> ?has_format_item_dbid .
                    ?has_format_agg <http://www.europeana.eu/schemas/edm/aggregatedCHO> ?has_format_item_id .
                    BIND( EXISTS { ?has_format_agg <http://www.europeana.eu/schemas/edm/isShownBy> ?_ . } AS ?has_panopto )
                }
                ORDER BY DESC(?has_panopto) ?has_format_item_dbid
            '''),
            initBindings={
                'item_id': rdflib.URIRef(item_id)
            }
        ):
            data['has_format'].append(row[0])

        # is_format_of
        data['is_format_of'] = []

        for row in self.g.query(
            prepareQuery('''
                SELECT ?is_format_of_item_id
                WHERE {
                    ?item_id <http://purl.org/dc/terms/isFormatOf> ?is_format_of_item_id .
                    ?is_format_of_item_id <http://purl.org/dc/elements/1.1/identifier> ?is_format_of_item_dbid .
                    ?is_format_of_agg <http://www.europeana.eu/schemas/edm/aggregatedCHO> ?is_format_of_item_id .
                    BIND( EXISTS { ?is_format_of_agg <http://www.europeana.eu/schemas/edm/isShownBy> ?_ . } AS ?has_panopto )
                }
                ORDER BY DESC(?has_panopto) ?is_format_of_item_dbid
            '''),
            initBindings={
                'item_id': rdflib.URIRef(item_id)
            }
        ):
            data['is_format_of'].append(row[0])

        # panopto links
        panopto_links = set()
        for row in self.g.query(
            prepareQuery('''
                SELECT ?panopto_link
                WHERE {
                    ?aggregation <http://www.europeana.eu/schemas/edm/aggregatedCHO> ?item_id .
                    ?aggregation <http://www.europeana.eu/schemas/edm/isShownBy> ?panopto_link
                }
            '''),
            initBindings={
                'item_id': rdflib.URIRef(item_id)
            }
        ):
            panopto_links.add(str(row[0]))
        data['panopto_links'] = list(panopto_links)

        # panopto identifiers
        panopto_identifiers = set()
        for panopto_link in panopto_links:
            try:
                r = requests.head(panopto_link, allow_redirects=True)
                identifier = urllib.parse.parse_qs(
                    urllib.parse.urlparse(
                        urllib.parse.parse_qs(
                            urllib.parse.urlparse(r.url).query
                        )['ReturnUrl'][0]
                    ).query
                )["id"][0]
                panopto_identifiers.add(identifier)
            except requests.exceptions.ConnectionError:
                data['panopto_links'].remove(panopto_link)
                print('unable to retrieve panopto identifier from ' + panopto_link)
        data['panopto_identifiers'] = list(panopto_identifiers)

        # access rights
        access_rights = set()
        for row in self.g.query(
            prepareQuery('''
                SELECT ?access_rights
                WHERE {
                    ?item_id <http://purl.org/dc/terms/isPartOf> ?series_id .
                    ?series_id <http://purl.org/dc/terms/accessRights> ?access_rights
                }
            '''),
            initBindings={
                'item_id': rdflib.URIRef(item_id)
            }
        ):
            access_rights.add(str(row[0]))
        data['access_rights'] = list(access_rights)

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
        qres = self.g.query('''
            SELECT ?item_id
            WHERE {
                ?_ <http://purl.org/dc/terms/hasPart> ?item_id
            }
        ''')
    
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
        r = self.g.query(
            prepareQuery('''
                SELECT ?item_id
                    WHERE {
                        ?series_id <http://purl.org/dc/terms/hasPart> ?item_id
                   }
            '''),
            initBindings={
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
        for row in self.g.query(
            prepareQuery('''
                SELECT ?medium
                WHERE {
                    ?item_id <http://purl.org/dc/terms/medium> ?medium
                }
            '''),
            initBindings={
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
            r = self.g.query(
                prepareQuery('''
                    SELECT ?o
                        WHERE {
                            ?series_id ?p ?o
                       }
                '''),
                initBindings={
                    'p': rdflib.URIRef(p),
                    'series_id': rdflib.URIRef(i)
                }
            )
            for row in r:
                search_tokens.append(str(row[0]))
    
        # edm:datasetName
        r = self.g.query(
            prepareQuery('''
                SELECT ?o
                    WHERE {
                        ?series_aggregation_id <http://www.europeana.eu/schemas/edm/datasetName> ?o .
                   }
            '''),
            initBindings={
                'p': rdflib.URIRef(p),
                'series_aggregation_id': rdflib.URIRef(i + '/aggregation')
            }
        )
        lookup = {
            'DMA': 'Digital Media Archive'
        }
        for row in r:
            search_tokens.append(lookup[str(row[0])])
    
        # dc:language 
        r = self.g.query(
            prepareQuery('''
                SELECT ?o
                    WHERE {
                        ?series_id <http://purl.org/dc/elements/1.1/language> ?o
                   }
            '''),
            initBindings={
                'series_id': rdflib.URIRef(i)
            }
        )
        for row in r:
            for label in self.get_glottolog_language_names(str(row[0])):
                search_tokens.append(label)
       
        # dcterms:spatial 
        r = self.g.query(
            prepareQuery('''
                SELECT ?o
                    WHERE {
                        ?series_id <http://purl.org/dc/terms/spatial> ?o
                    }
            '''),
            initBindings={
                'series_id': rdflib.URIRef(i)
            }
        )
        for row in r:
            for tgn_identifier in str(row[0]).split():
                for label in self.get_tgn_place_names(tgn_identifier):
                    search_tokens.append(label)
    
        # series-level dc:date
        years = set()
        r = self.g.query(
            prepareQuery('''
                SELECT ?o
                    WHERE {
                        ?series_id <http://purl.org/dc/terms/date> ?o
                    }
            '''),
            initBindings={
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
    
        # replace all whitespace with single spaces and return all search tokens in
        # a single string.
        return ' '.join([' '.join(s.split()) for s in search_tokens])

    def get_search_tokens_for_series_identifier(self, i):
        """
        Get the search tokens for a given series identifier from the graph.
    
        Parameters:
            i (str): a series identifier
    
        Returns:
            str: a string that can be searched via SQLite.
        """
        search_tokens = []
        
        # item-level description
        for iid in self.get_item_identifiers_for_series(i):
            r = self.g.query(
                prepareQuery('''
                    SELECT ?o
                        WHERE {
                            ?item_id <http://purl.org/dc/elements/1.1/description> ?o
                       }
                '''),
                initBindings={
                    'item_id': rdflib.URIRef(iid)
                }
            )
            for row in r:
                search_tokens.append(row[0])

        token_str = self.get_search_tokens_for_identifier(i)

        if token_str and search_tokens:
            token_str = token_str + \
            ' ' + \
            ' '.join([' '.join(s.split()) for s in search_tokens])

        return token_str

    def get_search_tokens_for_item_identifier(self, i):
        """
        Get the search tokens for a given item identifier from the graph.
    
        Parameters:
            i (str): a series identifier
    
        Returns:
            str: a string that can be searched via SQLite.
        """
        search_tokens = []
        
        # item-level description
        r = self.g.query(
            prepareQuery('''
                SELECT ?o
                    WHERE {
                        ?item_id <http://purl.org/dc/elements/1.1/description> ?o
                   }
            '''),
            initBindings={
                'item_id': rdflib.URIRef(i)
            }
        )
        for row in r:
            search_tokens.append(row[0])

        token_str = self.get_search_tokens_for_identifier(i)

        if token_str and search_tokens:
            token_str = token_str + \
            ' ' + \
            ' '.join([' '.join(s.split()) for s in search_tokens])

        return token_str

    def get_series_date(self, i):
        """
        Get a single date for a given series identifier from the graph.
    
        Parameters:
            i (str): a series identifier
    
        Returns:
            str: a four-digit year (YYYY) or a year range (YYYY/YYYY)
        """
        years = []
        for row in self.g.query(
            prepareQuery('''
                SELECT ?date
                WHERE {
                    ?identifier <http://purl.org/dc/terms/date> ?date
                }
                '''
            ),
            initBindings={
                'identifier': rdflib.URIRef(i)
            }
        ):
            for year in row[0].split('/'):
                years.append(year)

        if len(years) == 0:
            return ''
        elif len(years) == 1:
            return years[0]
        elif len(years) > 1:
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
        for row in self.g.query(
            prepareQuery('''
                SELECT ?dbid
                WHERE {
                    ?identifier <http://purl.org/dc/elements/1.1/identifier> ?dbid
                }
                '''
            ),
            initBindings={
                'identifier': rdflib.URIRef(i)
            }
        ):
            dbids.append(str(row[0]))

        if len(dbids) == 0:
            return ''
        else:
            return dbids[0]

    def get_series_identifiers(self):
        """
        Get all series identifiers from the graph.
    
        Parameters:
            None
    
        Returns:
            list: series identifiers. 
        """
        qres = self.g.query('''
            SELECT ?series_id
            WHERE {
                ?series_id <http://purl.org/dc/terms/hasPart> ?_
            }
        ''')
    
        results = set()
        for row in qres:
            results.add(str(row[0]))
        return sorted(list(results))

    def get_series_identifiers_for_item(self, i):
        """
        Get the series identifiers for a given item.
      
        Parameters:
            i (str): an item identifier.
    
        Returns:
            list: a list of series identifiers.
        """
        r = self.g.query(
            prepareQuery('''
                SELECT ?series_id
                    WHERE {
                        ?series_id <http://purl.org/dc/terms/hasPart> ?item_id
                   }
            '''),
            initBindings={
                'item_id': rdflib.URIRef(i)
            }
        )
    
        results = set()
        for row in r:
            results.add(str(row[0]))
        return sorted(list(results))

    def get_series_info(self, series_id):
        """
        Get info for search snippets and page views for a given series.
    
        Parameters:
            series_id (str): a series identifier.
    
        Returns:
            str: series title.
        """
        data = {}
    
        # edm:datasetName translate "DMA" to "Digital Media Archive"
        # language (indigenous and interview)
    
        for label, p in {
            'content_type':      'http://id.loc.gov/ontologies/bibframe/content',
            'creator':           'http://purl.org/dc/terms/creator',
            'description':       'http://purl.org/dc/elements/1.1/description',
            'identifier':        'http://purl.org/dc/elements/1.1/identifier',
            'titles':            'http://purl.org/dc/elements/1.1/title',
            'access_rights':     'http://purl.org/dc/terms/accessRights',
            'alternative_title': 'http://purl.org/dc/terms/alternative',
            'contributor':       'http://purl.org/dc/terms/contributor',
            'date':              'http://purl.org/dc/terms/date',
            'location':          'http://purl.org/dc/terms/spatial'
        }.items():
            values = set()
            for row in self.g.query(
                prepareQuery('''
                    SELECT ?value
                    WHERE {
                        ?series_id ?p ?value
                    }
                '''),
                initBindings={
                    'p': rdflib.URIRef(p),
                    'series_id': rdflib.URIRef(series_id)
                }
            ):
                values.add(' '.join(row[0].split()))
            data[label] = sorted(list(values))

        # convert TGN identifiers to preferred names.
        tgn_identifiers = set()
        for i in data['location']:
            for j in i.split():
                tgn_identifiers.add(j)

        data['location'] = []
        for i in tgn_identifiers:
            for preferred_name in self.get_tgn_place_name_preferred(
                i
            ):
                data['location'].append(preferred_name)

        # primary_language
        codes = set()
        for row in self.g.query(
            prepareQuery('''
                SELECT ?code
                WHERE {
                    ?series_id <http://lib.uchicago.edu/language> ?l .
                    ?l <http://lib.uchicago.edu/icu/languageRole> ?role .
                    ?l <https://www.iso.org/standard/39534.htmliso639P3PCode> ?code .
                    FILTER (?role IN ('Both', 'Primary'))
                }
            '''),
            initBindings={
                'series_id': rdflib.URIRef(series_id)
            }
        ):
            codes.add(row[0])

        preferred_names = set()
        for c in codes:
            for preferred_name in self.get_glottolog_language_names_preferred(
                c
            ):
                preferred_names.add(preferred_name)

        data['primary_language'] = []
        for preferred_name in preferred_names:
            data['primary_language'].append(preferred_name)

        # subject_language
        codes = set()
        for row in self.g.query(
            prepareQuery('''
                SELECT ?code
                WHERE {
                    ?series_id <http://lib.uchicago.edu/language> ?l .
                    ?l <http://lib.uchicago.edu/icu/languageRole> ?role .
                    ?l <https://www.iso.org/standard/39534.htmliso639P3PCode> ?code .
                    FILTER (?role IN ('Both', 'Subject'))
                }
            '''),
            initBindings={
                'series_id': rdflib.URIRef(series_id)
            }
        ):
            codes.add(row[0])

        preferred_names = set()
        for c in codes:
            for preferred_name in self.get_glottolog_language_names_preferred(
                c
            ):
                preferred_names.add(preferred_name)

        data['subject_language'] = []
        for preferred_name in preferred_names:
            data['subject_language'].append(preferred_name)

        data['ark'] = series_id

        return data

    def get_series_search_tokens(self, i):
        """
        Get the search tokens for a given series identifier from the graph.
    
        Parameters:
            i (str): a series identifier
    
        Returns:
            str: a string that can be searched via SQLite.
        """
        search_tokens = []
        
    def get_series_identifiers(self):
        """
        Get all series identifiers from the graph.
    
        Parameters:
            None
    
        Returns:
            list: series identifiers. 
        """
        qres = self.g.query('''
            SELECT ?series_id
            WHERE {
                ?series_id <http://purl.org/dc/terms/hasPart> ?_
            }
        ''')
    
        results = set()
        for row in qres:
            results.add(str(row[0]))
        return sorted(list(results))

    def get_series_identifiers_for_item(self, i):
        """
        Get the series identifiers for a given item.
      
        Parameters:
            i (str): an item identifier.
    
        Returns:
            list: a list of series identifiers.
        """
        r = self.g.query(
            prepareQuery('''
                SELECT ?series_id
                    WHERE {
                        ?series_id <http://purl.org/dc/terms/hasPart> ?item_id
                   }
            '''),
            initBindings={
                'item_id': rdflib.URIRef(i)
            }
        )
    
        results = set()
        for row in r:
            results.add(str(row[0]))
        return sorted(list(results))

    def get_series_info(self, series_id):
        """
        Get info for search snippets and page views for a given series.
    
        Parameters:
            series_id (str): a series identifier.
    
        Returns:
            str: series title.
        """
        data = {}
    
        # edm:datasetName translate "DMA" to "Digital Media Archive"
        # language (indigenous and interview)
    
        for label, p in {
            'content_type':      'http://id.loc.gov/ontologies/bibframe/content',
            'creator':           'http://purl.org/dc/terms/creator',
            'description':       'http://purl.org/dc/elements/1.1/description',
            'identifier':        'http://purl.org/dc/elements/1.1/identifier',
            'titles':            'http://purl.org/dc/elements/1.1/title',
            'access_rights':     'http://purl.org/dc/terms/accessRights',
            'alternative_title': 'http://purl.org/dc/terms/alternative',
            'contributor':       'http://purl.org/dc/terms/contributor',
            'date':              'http://purl.org/dc/terms/date',
            'location':          'http://purl.org/dc/terms/spatial'
        }.items():
            values = set()
            for row in self.g.query(
                prepareQuery('''
                    SELECT ?value
                    WHERE {
                        ?series_id ?p ?value
                    }
                '''),
                initBindings={
                    'p': rdflib.URIRef(p),
                    'series_id': rdflib.URIRef(series_id)
                }
            ):
                values.add(' '.join(row[0].split()))
            data[label] = sorted(list(values))

        # convert TGN identifiers to preferred names.
        tgn_identifiers = set()
        for i in data['location']:
            for j in i.split():
                tgn_identifiers.add(j)

        data['location'] = []
        for i in tgn_identifiers:
            for preferred_name in self.get_tgn_place_names_preferred(
                i
            ):
                data['location'].append(preferred_name)

        # primary_language
        codes = set()
        for row in self.g.query(
            prepareQuery('''
                SELECT ?code
                WHERE {
                    ?series_id <http://lib.uchicago.edu/language> ?l .
                    ?l <http://lib.uchicago.edu/icu/languageRole> ?role .
                    ?l <https://www.iso.org/standard/39534.htmliso639P3PCode> ?code .
                    FILTER (?role IN ('Both', 'Primary'))
                }
            '''),
            initBindings={
                'series_id': rdflib.URIRef(series_id)
            }
        ):
            codes.add(row[0])

        preferred_names = set()
        for c in codes:
            for preferred_name in self.get_glottolog_language_names_preferred(
                c
            ):
                preferred_names.add(preferred_name)

        data['primary_language'] = []
        for preferred_name in preferred_names:
            data['primary_language'].append(preferred_name)

        # subject_language
        codes = set()
        for row in self.g.query(
            prepareQuery('''
                SELECT ?code
                WHERE {
                    ?series_id <http://lib.uchicago.edu/language> ?l .
                    ?l <http://lib.uchicago.edu/icu/languageRole> ?role .
                    ?l <https://www.iso.org/standard/39534.htmliso639P3PCode> ?code .
                    FILTER (?role IN ('Both', 'Subject'))
                }
            '''),
            initBindings={
                'series_id': rdflib.URIRef(series_id)
            }
        ):
            codes.add(row[0])

        preferred_names = set()
        for c in codes:
            for preferred_name in self.get_glottolog_language_names_preferred(
                c
            ):
                preferred_names.add(preferred_name)

        data['subject_language'] = []
        for preferred_name in preferred_names:
            data['subject_language'].append(preferred_name)

        data['ark'] = series_id

        return data

    def get_tgn_identifiers(self):
        """Get all TGN identifiers from the TGN graph.
    
        Parameters:
            (None)
    
        Returns:
            list: all identifiers. 
    
        Notes:
            There are only 157 identifiers in the data as of August, 2023. 
        """
        results = set()
        for row in self.g.query('''
            SELECT ?identifier
            WHERE {
                ?identifier <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> ?type .
                FILTER (?type IN (
                    <http://vocab.getty.edu/ontology#Subject>,
                    <http://vocab.getty.edu/ontology#PhysPlaceConcept>,
                    <http://www.w3.org/2004/02/skos/core#Concept>,
                    <http://vocab.getty.edu/ontology#AdminPlaceConcept>
                ))
            }
        '''):
            results.add(str(row[0]).replace('http://vocab.getty.edu/tgn/', ''))
        return list(results)
    
    def get_tgn_place_names(self, i):
        """Get all place names from TGN for a given identifier. 
     
        Parameters:
            i (str): TGN identifier, e.g., '7005493'
    
        Returns:
            list: a list of place names as unicode strings.
        """
        results = set()
        for row in self.g.query(
            prepareQuery(''' 
                SELECT ?label
                WHERE {
                    {
                        ?tgn <http://www.w3.org/2000/01/rdf-schema#label> ?label .
                    } UNION {
                        ?tgn <http://www.w3.org/2004/02/skos/core#altLabel> ?label .
                    } UNION {
                        ?tgn <http://www.w3.org/2004/02/skos/core#prefLabel> ?label .
                    }
                }
            '''),
            initBindings={
                'tgn': rdflib.URIRef('http://vocab.getty.edu/tgn/' + str(i))
            }
        ):
            results.add(str(row[0]))
        return list(results)
    
    def get_tgn_place_names_en(self, i):
        """Get a list of English-language place names from TGN.
    
        Parameters:
            i (str): TGN identifier, e.g., '7005493'
    
        Returns:
            list: a list of strings, e.g., "Guatemala"
    
        Notes:
            This data is spotty- English-language names are not always available.
        """
        results = set()
        for row in self.g.query(
            prepareQuery(''' 
                SELECT ?label
                WHERE {
                    {
                        ?tgn <http://www.w3.org/2000/01/rdf-schema#label> ?label .
                    } UNION {
                        ?tgn <http://www.w3.org/2004/02/skos/core#altLabel> ?label .
                    } UNION {
                        ?tgn <http://www.w3.org/2004/02/skos/core#prefLabel> ?label .
                    }
                    FILTER langMatches(lang(?label), "EN")
                }
            '''),
            initBindings={
                'tgn': rdflib.URIRef('http://vocab.getty.edu/tgn/' + str(i))
            }
        ):
            results.add(str(row[0]).strip())
        return list(results)
    
    def get_tgn_place_names_preferred(self, i):
        """Get English-language place names if we can, otherwise get a list of all
           place names.
    
        Parameters:
            i (str): TGN identifier, e.g., '7005493'
    
        Returns:
            list: a list of strings, e.g., "Guatemala"
        """
        results = set()
        for row in self.g.query(
            prepareQuery(''' 
                SELECT ?label
                WHERE {
                    ?tgn <http://www.w3.org/2004/02/skos/core#prefLabel> ?label .
                    FILTER langMatches(lang(?label), "EN")
                }
            '''),
            initBindings={
                'tgn': rdflib.URIRef('http://vocab.getty.edu/tgn/' + str(i))
            }
        ):
            results.add(str(row[0]).strip())

        place_names = list(results)
        if len(place_names) > 0:
            return [place_names[0]]
        else:
            place_names = self.get_tgn_place_names_en(i)
            if len(place_names) > 0:
                return [place_names[0]]
            else:
                place_names = self.get_tgn_place_names(i)
                if len(place_names) > 0:
                    return [self.get_tgn_place_names(i)[0]]
        return []
    

class MLCDB:
    def __init__(self, config):
        """
        Parameters:
            config (dict): a configuration dict, e.g., .config from Flask.
        """
        self.config = config

        self.con = None
        self.cur = None

        self._item_info = {}
        self._series_info = {}

    def build_db(self):
        """
        Build SQLite database.
    
        Parameters:
            None
        """
        if os.path.exists(self.config['DB']):
            os.remove(self.config['DB'])
     
        con = sqlite3.connect(self.config['DB'])
        cur = con.cursor()
    
        g = rdflib.Graph()
        g.parse(self.config['MESO_TRIPLES'], format='turtle')
        g.parse(self.config['GLOTTO_TRIPLES'], format='turtle')
        g.parse(self.config['TGN_TRIPLES'])
    
        mlc_graph = MLCGraph(g)

        # build an item to series lookup
        item_series_lookup = {}
        for item_id in mlc_graph.get_item_identifiers():
            if not item_id in item_series_lookup:
                item_series_lookup[item_id] = []
            for series_id in mlc_graph.get_series_identifiers_for_item(item_id): 
                item_series_lookup[item_id].append(series_id)

        # build tables
        cur.execute('begin')
    
        cur.execute('''
            create table browse(
                type text,
                term text,
                id text
            );
        ''')
        cur.execute('''
            create virtual table item using fts5(
                id,
                dbid,
                has_panopto_link,
                info,
                medium,
                text,
                series_ids
            );
        ''')
        cur.execute('''
            create virtual table series using fts5(
                id,
                dbid,
                date,
                info,
                text
            );
        ''')
        cur.execute('commit')
    
        # load data
        cur.execute('begin')
    
        # load browses
        for browse_type, sort_key in {
            'contributor': 'count',
            'creator':     'count',
            'date':        'label',
            'decade':      'label',
            'language':    'count',
            'location':    'count'
        }.items():
            for browse_term, identifiers in mlc_graph.get_browse_terms(
                browse_type,
                sort_key
            ).items():
                for identifier in identifiers:
                    cur.execute('''
                        insert into browse (type, term, id)
                        values (?, ?, ?);
                        ''',
                        (
                            browse_type,
                            browse_term,
                            identifier
                        )
                    )
    
        # load item
        for i in mlc_graph.get_item_identifiers(): 
            cur.execute('''
                insert into item (id, dbid, has_panopto_link, info, medium, text, series_ids) 
                values (?, ?, ?, ?, ?, ?, ?);
                ''',
                (
                    i,
                    mlc_graph.get_item_dbid(i),
                    mlc_graph.get_item_has_panopto_link(i),
                    json.dumps(mlc_graph.get_item_info(i)),
                    json.dumps(mlc_graph.get_item_medium(i)),
                    mlc_graph.get_search_tokens_for_item_identifier(i),
                    '|'.join(item_series_lookup[i])
                )
            )
    
        # load series 
        for i in mlc_graph.get_series_identifiers(): 
            cur.execute('''
                insert into series (
                    id, 
                    dbid,
                    date,
                    info,
                    text) values (?, ?, ?, ?, ?);
                ''',
                (
                    i,
                    mlc_graph.get_series_dbid(i),
                    mlc_graph.get_series_date(i),
                    json.dumps(mlc_graph.get_series_info(i)),
                    mlc_graph.get_search_tokens_for_series_identifier(i)
                )
            )
    
        cur.execute('commit')

    def connect(self):
        """
        Connect to database.

        Parameters:
            None

        Returns:
            None
        """
        self.con = sqlite3.connect(self.config['DB'], check_same_thread=False)
        self.cur = self.con.cursor()

        for row in self.cur.execute('select id, info from item;').fetchall():
            self._item_info[row[0]] = json.loads(row[1])

        for row in self.cur.execute('select id, info from series;').fetchall():
            self._series_info[row[0]] = json.loads(row[1])

    def convert_raw_query_to_fts(self, query):
        """
        Convert a raw user query to a series of single words, joined by boolean
        AND, and suitable for passing along to SQLite FTS.

        Parameters:
            query (str): a search string.

        Returns:
            str: search terms cleaned and separated by ' AND '.
        """
        if query:
            # limit queries to 256 characters. (size chosen arbitrarily.)
            query = query[:256]

            # replace all non-unicode letters or numbers in the query with a
            # single space. This should strip out punctuation, etc. 
            query = re.sub(u"[^\p{L}\p{N}]+", " ", str(query))

            # replace all whitespace with a single space.
            query = ' '.join(query.split())

        # join all search terms with AND. 
        # limit queries to 32 search terms. (size chosen arbitrarily.)
        match_string = []
        for q in query.split(' '):
            match_string.append(q)
        match_string = ' AND '.join(match_string[:32])

        return match_string

    def get_browse(self, browse_type):
        """
        Get browse.
    
        Parameters:
            browse_type (str): type of browse terms to retrieve. 
    
        Returns:
            list: a list of browse terms.
        """
        assert browse_type in (
            'contributor', 
            'creator',
            'date', 
            'decade', 
            'language',
            'location'
        )

        if not self.con:
            self.connect()
   
        # sort browse results on case-insensitive characters only, stripping
        # out things like leading quotation marks. Because SQLite doesn't let
        # us strip out things like punctuation for sorting we do that after
        # the query in python.
        return sorted(
            self.cur.execute('''
                select term, count(id)
                from browse
                where type=?
                group by term
                ''',
                (browse_type,)
            ).fetchall(),
            key=lambda i: re.sub(u'\P{L}+', '', i[0]).lower()
        )

    def get_browse_term(self, browse_type, browse_term, sort_field='dbid'):
        """
        Get a list of series for a specific browse term.

        Parameters:
            browse_type (str): type of browse term.
            browse_term (str): browse term.
            sort_field (str):  database field to sort on.

        Returns:
	    list: a list of browse results. This should contain all the
            information that search results contain.
        """
        assert browse_type in (
            'contributor', 
            'creator',
            'date', 
            'decade', 
            'language',
            'location'
        )

        assert sort_field in (
            'dbid',
            'date'
        )

        if not self.con:
            self.connect()

        results = []
        for row in self.cur.execute(
            '''
                select browse.id, series.info, 0.0
                from browse
                inner join series on series.id = browse.id
                where type=?
                and term=?
                order by series.{}
            '''.format(sort_field),
            (browse_type, browse_term)
        ).fetchall():
            results.append((row[0], json.loads(row[1]), row[2]))
        return results

    def get_item(self, identifier):
        """
        Get item metadata.
    
        Parameters:
            identifier (str): item identifier.
    
        Returns:
            dict: a metadata dictionary.
        """
        if not self.con:
            self.connect()

        info = json.loads(
            self.cur.execute(
                'select info from item where id = ?',
                (identifier,)
            ).fetchone()[0]
        )

        # load item hasFormat / isFormatOf relationships
        for p in ('has_format', 'is_format_of'):
            if p in info and isinstance(info[p], list):
                for i in range(len(info[p])):
                    url = info[p][i]
                    for row in self.cur.execute(
                        'select info from item where id = ?;', 
                        (url,)
                    ).fetchall():
                        info[p][i] = json.loads(row[0])

        return info

    def get_item_info(self, item_id):
        """
        Get info dict for an item.
    
        Parameters:
            item_id (str): item identifier. 
    
        Returns:
            dict: a dictionary of item information.
        """
        if not self.con:
            self.connect()

        return self._item_info[item_id]

    def get_item_list(self):
        """
        Get all item identifiers.
    
        Parameters:
            None
    
        Returns:
            list: a list of item identifiers
        """
        if not self.con:
            self.connect()

        item_ids = []
        for row in self.cur.execute('select id from item;').fetchall():
            item_ids.append(row[0])
        return item_ids

    def get_items_for_series(self, identifier):
        """
        Get items for a series.
    
        Parameters:
            identifier (str): series identifier. 
    
        Returns:
            list: a list of series identifiers.
        """
        if not self.con:
            self.connect()

        results = []   
        for row in self.cur.execute('''
            select id
            from item 
            where series_ids like ?
            ''',
            ('%' + identifier + '%',)
        ).fetchall():
            results.append(str(row[0]))
        return results

    def get_search(self, query, facets=[], sort_type='rank'):
        """
        Get search results.
    
        Parameters:
            query (str):     a search string.
            facets (list):   a list of strings, where each string begins with a
                             browse/facet type, followed by a colon, followed
                             by the term.
            sort_type (str): e.g., 'rank', 'date'
    
        Returns:
            list: a list, where each element contains a three-tuple with a
                  series identifier, a list of item identifiers with hits in
                  that series, and a rank.
        """
        assert sort_type in ('date', 'rank', 'series.id')

        if not self.con:
            self.connect()

        if query:
            query = self.convert_raw_query_to_fts(query)

        subqueries = []
        for f in facets:
            subqueries.append('''
                select id
                from browse
                where type=?
                and term=? 
            ''')

        vars = []
        if query:
            vars.append(query)
        for f in facets:
            m = re.match('^([^:]*):(.*)$', f)
            vars.append(m.group(1))
            vars.append(m.group(2))

        # Execute series search.

        if query and facets:
            sql = '''
                    select id, rank
                    from series
                    where text match ?
                    and id in ({})
                    order by {};
            '''.format(' intersect '.join(subqueries), sort_type)
        elif query:
            sql = '''
                    select id, rank
                    from series
                    where text match ?
                    order by {};
            '''.format(sort_type)
        elif facets:
            sql = '''
                    select id
                    from series
                    where id in ({})
                    order by id
            '''.format(' intersect '.join(subqueries))
        else:
            sql = '''
                    select id
                    from series
                    order by id
            '''

        series_results = []
        for row in self.cur.execute(sql, vars).fetchall():
            if len(row) == 1:
                series_results.append([row[0], [], 0.0])
            else:
                series_results.append([row[0], [], row[1]])

        # Execute item search.

        if query and facets:
            sql = '''
                    select id, series_ids
                    from item
                    where text match ?
                    and id in ({})
                    order by cast (dbid as unsigned);
            '''.format(' intersect '.join(subqueries))
        elif query:
            sql = '''
                    select id, series_ids
                    from item
                    where text match ?
                    order by cast (dbid as unsigned);
            '''
        elif facets:
            sql = '''
                    select id, series_ids
                    from item
                    where id in ({})
                    order by cast (dbid as unsigned);
            '''.format(' intersect '.join(subqueries))
        else:
            sql = '''
                    select id, series_ids
                    from item
                    order by cast (dbid as unsigned);
            '''

        item_results = []
        for row in self.cur.execute(sql, vars).fetchall():
            item_results.append((
                row[0],
                row[1].split('|')
            ))

        # Build a series lookup to speed up processing.
        series_lookup = {}

        for s in range(len(series_results)):
            series_ids = series_results[s][0].split('|')
            for series_id in series_ids:
                series_lookup[series_id] = s

        # Add item result to appropriate series. 
        for i in range(len(item_results)):
            item_id = item_results[i][0]
            series_ids = item_results[i][1]
            for series_id in series_ids:
                if series_id in series_lookup:
                    series_index = series_lookup[series_id]
                    series_results[series_index][1].append(item_id)
                    
        return series_results

    def get_series(self, identifier):
        """
        Get series metadata.
    
        Parameters:
            identifier (str): a series identifier.
    
        Returns:
            dict: a metadata dictionary.
        """
        if not self.con:
            self.connect()

        return json.loads(
            self.cur.execute(
                'select info from series where id = ?',
                (identifier,)
            ).fetchone()[0]
        )

    def get_series_for_item(self, identifier):
        """
        Get series for item.
    
        Parameters:
            identifier (str): item identifier. 
    
        Returns:
            list: a list of series identifiers.
        """
        if not self.con:
            self.connect()

        results = []   
        for row in self.cur.execute('''
            select series_ids
            from item 
            where id = ?
            ''',
            (identifier,)
        ).fetchall():
            for series_id in row[0].split('|'):
                results.append(series_id)
        return results

    def get_series_info(self, series_id):
        """
        Get info dict for a series.
    
        Parameters:
            series_id (str): item identifier. 
    
        Returns:
            dict: a dictionary of item information.
        """
        if not self.con:
            self.connect()

        return self._series_info[series_id]

    def get_series_list(self):
        """
        Get all series identifiers.
    
        Parameters:
            None
    
        Returns:
            list: a list of series identifiers.
        """
        if not self.con:
            self.connect()

        series_ids = []
        for row in self.cur.execute('select id from series;').fetchall():
            series_ids.append(row[0])
        return series_ids

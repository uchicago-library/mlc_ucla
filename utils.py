import json, os, rdflib, sqlite3, sys, timeit
from docopt import docopt
from rdflib.plugins.sparql import prepareQuery

import regex as re

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
            results.add(row[0])
        return sorted(list(results))

    def get_item_info(self, item_id):
        """
        Get info for search snippets and page views for a given series.
    
        Parameters:
            item_id (str): a series identifier.
    
        Returns:
            str: series title.
        """
        data = {}
    
        for label, p in {
            'content_type':         'http://id.loc.gov/ontologies/bibframe/content',
            'linguistic_data_type': 'http://lib.uchicago.edu/dma/olacLinguisticDataType',
            'creator':              'http://purl.org/dc/terms/creator',
            'description':          'http://purl.org/dc/elements/1.1/description',
            'identifier':           'http://purl.org/dc/elements/1.1/identifier',
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
            for preferred_name in self.get_tgn_preferred_place_name(
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
            for preferred_name in self.get_glottolog_language_preferred_names(
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
            for preferred_name in self.get_glottolog_language_preferred_names(
                c
            ):
                preferred_names.add(preferred_name)

        data['subject_language'] = []
        for preferred_name in preferred_names:
            data['subject_language'].append(preferred_name)

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

        return data

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
            for preferred_name in self.get_tgn_preferred_place_name(
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
            for preferred_name in self.get_glottolog_language_preferred_names(
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
            for preferred_name in self.get_glottolog_language_preferred_names(
                c
            ):
                preferred_names.add(preferred_name)

        data['subject_language'] = []
        for preferred_name in preferred_names:
            data['subject_language'].append(preferred_name)

        return data

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
                for label in self.get_glottolog_language_preferred_names(
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
                    for label in self.get_tgn_preferred_place_name(
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

    def get_search_tokens_for_series_identifier(self, i):
        """
        Get the search tokens for a given series identifier from the graph.
    
        Parameters:
            i (str): a series identifier
    
        Returns:
            str: a string that can be searched via SQLite.
        """
    
        search_tokens = []
    
        # series-level non-blank triples with no special processing
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
    
        # series-level edm:datasetName
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
    
        # series-level dc:language 
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
       
        # series-level dcterms:spatial 
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
        # TODO
    
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
    
        # replace all whitespace with single spaces and return all search tokens in
        # a single string.
        return ' '.join([' '.join(s.split()) for s in search_tokens])

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
                    ?tgn <http://www.w3.org/2000/01/rdf-schema#label> ?label
                }
            '''),
            initBindings={
                'tgn': rdflib.URIRef('http://vocab.getty.edu/tgn/' + str(i))
            }
        ):
            results.add(str(row[0]))
        return list(results)
    
    def get_tgn_place_name_en(self, i):
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
                    ?tgn <http://www.w3.org/2000/01/rdf-schema#label> ?label .
                    FILTER langMatches(lang(?label), "EN")
                }
            '''),
            initBindings={
                'tgn': rdflib.URIRef('http://vocab.getty.edu/tgn/' + str(i))
            }
        ):
            results.add(str(row[0]).strip())
        return list(results)
    
    def get_tgn_preferred_place_name(self, i):
        """Get English-language place names if we can, otherwise get a list of all
           place names.
    
        Parameters:
            i (str): TGN identifier, e.g., '7005493'
    
        Returns:
            list: a list of strings, e.g., "Guatemala"
        """
        place_names = self.get_tgn_place_name_en(i)
        if len(place_names) > 0:
            return place_names
        else:
            return self.get_tgn_place_names(i)
    
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
      
    def get_glottolog_language_preferred_names(self, c):
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


class MLCDB:
    def __init__(self, config):
        """
        Parameters:
            config (dict): a configuration dict, e.g., .config from Flask.
        """
        self.con = sqlite3.connect(':memory:')
        self.cur = self.con.cursor()

        with open(config['DB'], encoding='utf-8') as f:
            self.cur.executescript(f.read())

        # build the search table after loading data to avoid issues dumping and
        # reloading virtual tables.
        self.cur.execute('''
            create virtual table search using fts5(
                id,
                text,
                tokenize="porter unicode61"
            );
        ''')
    
        for row in self.cur.execute('select id, text from series;').fetchall():
            self.cur.execute(
                'insert into search(id, text) values (?, ?);',
                row
            )

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

    def get_browse_term(self, browse_type, browse_term):
        """
        Get a list of series for a specific browse term.

        Parameters:
            browse_type (str): type of browse term.
            browse_term (str): browse term.

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

        results = []
        for row in self.cur.execute(
            '''
                select browse.id, series.info, 0.0
                from browse
                inner join series on series.id = browse.id
                where type=?
                and term=?
                order by browse.id
            ''',
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
        return json.loads(
            self.cur.execute(
                'select info from item where id = ?',
                (identifier,)
            ).fetchone()[0]
        )
    
    def get_item_list(self):
        """
        Get all item identifiers.
    
        Parameters:
            None
    
        Returns:
            list: a list of identifier, metadata dict tuples. 
        """
        results = []
        for row in self.cur.execute('select id, info from item;').fetchall():
            results.append((row[0], json.loads(row[1])))
        return results

    def get_items_for_series(self, identifier):
        """
        Get items for a series.
    
        Parameters:
            identifier (str): series identifier. 
    
        Returns:
            list: a list of tuples, where the first element is an item
                  identifier and the second is an item info dictionary.
        """
        results = []   
        for row in self.cur.execute('''
            select series_item.item_id, item.info
            from series_item 
            inner join item on item.id = series_item.item_id
            where series_item.series_id = ?
            ''',
            (identifier,)
        ).fetchall():
            results.append((row[0], json.loads(row[1])))
        return results

    def get_series_for_item(self, identifier):
        """
        Get series for item.
    
        Parameters:
            identifier (str): item identifier. 
    
        Returns:
            tuple: where the first element is a series identifier and the
                   second is an item info dictionary.
        """
        results = []   
        for row in self.cur.execute('''
            select series_item.series_id, series.info
            from series_item 
            inner join series on series.id = series_item.series_id
            where series_item.item_id = ?
            ''',
            (identifier,)
        ).fetchall():
            results.append((row[0], json.loads(row[1])))
        return results[0]
    
    def get_search(self, query, facets=[]):
        """
        Get search results.
    
        Parameters:
            query (str):   a search string.
            facets (list): a list of strings, where each string begins with a
                           browse/facet type, followed by a colon, followed by
                           the term.
    
        Returns:
            list: a list, where each element contains a three-tuple with a
                  series identifier, a series info dictionary for constructing
                  search snippets, and a rank. 
        """
        # limit queries to 256 characters. (size chosen arbitrarily.)
        query = query[:256]

        # replace all non-unicode characters in the query with a single space.
        # this should strip out punctuation, etc. 
        query = re.sub(u"\P{L}+", " ", str(query))

        # replace all whitespace with a single space.
        query = ' '.join(query.split())

        # join all search terms with AND. 
        # limit queries to 32 search terms. (size chosen arbitrarily.)
        match_string = []
        for q in query.split(' '):
            match_string.append(q)
        match_string = ' AND '.join(match_string[:32])

        subqueries = []
        for f in facets:
            subqueries.append('''
                select browse.id
                from browse
                where browse.type=?
                and browse.term=? 
            ''')

        if query and facets:
            sql = '''
                    select search.id, series.info, rank
                    from search
                    inner join series on series.id = search.id
                    where search.text match ?
                    and search.id in ({})
                    order by rank;
            '''.format(' intersect '.join(subqueries))
        elif query:
            sql = '''
                    select search.id, series.info, rank
                    from search
                    inner join series on series.id = search.id
                    where search.text match ?
                    order by rank;
            '''.format(' intersect '.join(subqueries))
        elif facets:
            sql = '''
                    select series.id, series.info
                    from series
                    where series.id in ({})
                    order by series.id;
            '''.format(' intersect '.join(subqueries))
        else:
            sql = '''
                    select series.id, series.info
                    from series
                    order by series.id;
            '''

        vars = []
        if query:
            vars.append(query)
        for f in facets:
            m = re.match('^([^:]*):(.*)$', f)
            vars.append(m.group(1))
            vars.append(m.group(2))

        results = []
        for row in self.cur.execute(sql, vars).fetchall():
            if len(row) == 2:
                results.append((row[0], json.loads(row[1]), 0.0))
            else:
                results.append((row[0], json.loads(row[1]), row[2]))
        return results
    
    def get_series(self, identifier):
        """
        Get series metadata.
    
        Parameters:
            identifier (str): a series identifier.
    
        Returns:
            dict: a metadata dictionary.
        """
        return json.loads(
            self.cur.execute(
                'select info from series where id = ?',
                (identifier,)
            ).fetchone()[0]
        )
    
    def get_series_list(self):
        """
        Get all series identifiers.
    
        Parameters:
            None
    
        Returns:
            list: a list of identifier, metadata dict tuples. 
        """
        results = []
        for row in self.cur.execute('select id, info from series;').fetchall():
            results.append((row[0], json.loads(row[1])))
        return results


def build_sqlite_db(cur):
    g = rdflib.Graph()
    g.parse('meso.big.20230816.ttl', format='turtle')
    g.parse('glottolog_language.ttl', format='turtle')
    g.parse('TGN.ttl')
    mlc_graph = MLCGraph(g)

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
        create table item(
            id text,
            info text
        );
    ''')
    cur.execute('''
        create table series(
            id text,
            info text,
            text text
        );
    ''')
    cur.execute('''
        create table series_item(
            series_id text,
            item_id text
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
            insert into item (id, info) 
            values (?, ?);
            ''',
            (
                i,
                json.dumps(mlc_graph.get_item_info(i))
            )
        )

    # load series 
    for i in mlc_graph.get_series_identifiers(): 
        cur.execute('''
            insert into series (
                id, 
                info,
                text) values (?, ?, ?);
            ''',
            (
                i,
                json.dumps(mlc_graph.get_series_info(i)),
                mlc_graph.get_search_tokens_for_series_identifier(i)
            )
        )

    # load series_item
    for series_id in mlc_graph.get_series_identifiers(): 
        for item_id in mlc_graph.get_item_identifiers_for_series(series_id):
            cur.execute('''
                insert into series_item (
                    series_id,
                    item_id
                ) values (?, ?);
            ''',
            (
                series_id,
                item_id,
            ) 
        )
    cur.execute('commit')

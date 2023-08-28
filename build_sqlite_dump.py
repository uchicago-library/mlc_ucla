"""Usage:
    build_sqlite_dump.py --graph=<graph>
"""

import json, os, rdflib, re, sqlite3, sqlite_dump, sys, timeit
from docopt import docopt
from rdflib.plugins.sparql import prepareQuery

def get_series_identifiers(g):
    """
    Get all series identifiers from the graph.

    Parameters:
        g (rdflib.Graph): a graph to search.

    Returns:
        list: series identifiers. 
    """
    qres = g.query('''
        SELECT ?series_id
        WHERE {
            ?series_id <http://purl.org/dc/terms/hasPart> ?_
        }
    ''')

    results = set()
    for row in qres:
        results.add(str(row[0]))
    return sorted(list(results))

def get_item_identifiers(g):
    """
    Get all item identifiers from the graph.

    Parameters:
        g (rdflib.Graph): a graph to search.

    Returns:
        list: item identifiers. 
    """
    qres = g.query('''
        SELECT ?item_id
        WHERE {
            ?_ <http://purl.org/dc/terms/hasPart> ?item_id
        }
    ''')

    results = set()
    for row in qres:
        results.add(str(row[0]))
    return sorted(list(results))

def get_item_identifiers_for_series(g, i):
    """
    Get the item identifiers for a given series.
  
    Parameters:
        g (rdflib.Graph): a graph to search.
        i (str): a series identifier.

    Returns:
        list: a list of item identifiers.
    """
    r = g.query(
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

def get_item_info(g, i):
    """
    Get info for search snippets and page views for a given series.

    Parameters:
        g (rdflib.Graph): a graph to search.
        i (str): a series identifier.

    Returns:
        str: series title.
    """
    data = {}

    for label, p in {
        'content_type':         'http://id.loc.gov/ontologies/bibframe/content',
        'linguistic_data_type': 'http://lib.uchicago.edu/dma/olacLinguisticDataType',
        'creator':              'http://purl.org/dc/elements/1.1/creator',
        'description':          'http://purl.org/dc/elements/1.1/description',
        'identifier':           'http://purl.org/dc/elements/1.1/identifier',
        'language':             'http://purl.org/dc/elements/1.1/language',
        'title':                'http://purl.org/dc/elements/1.1/title',
        'access_rights':        'http://purl.org/dc/terms/accessRights',
        'alternative_title':    'http://purl.org/dc/terms/alternative',
        'contributor':          'http://purl.org/dc/terms/contributor',
        'date':                 'http://purl.org/dc/terms/date',
        'is_part_of':           'http://purl.org/dc/terms/isPartOf',
        'location':             'http://purl.org/dc/terms/spatial',
        'discourse_type':       'http://www.language−archives.org/OLAC/metadata.htmldiscourseType'
    }.items():
        values = set()
        for row in g.query(
            prepareQuery('''
                SELECT ?value
                WHERE {
                    ?series_id ?p ?value
                }
            '''),
            initBindings={
                'p': rdflib.URIRef(p),
                'series_id': rdflib.URIRef(i)
            }
        ):
            values.add(' '.join(row[0].split()))
        data[label] = sorted(list(values))

    # special processing
    # 'http://lib.uchicago.edu/language where http://lib.uchicago.edu/icu/languageRole is 'Primary' or 'Both'
    #  https://www.iso.org/standard/39534.htmliso639P3PCode

    # Indigenous Language -> uchicago:language where icu:languageRole is 'Primary' or 'Both'
    # Language -> uchicago:language where icu:languageRole is 'Subject' or 'Both'

    # Location Where Indigenous Language is Spoken -> dcterms:spatial

    return data

def get_series_info(g, i):
    """
    Get info for search snippets and page views for a given series.

    Parameters:
        g (rdflib.Graph): a graph to search.
        i (str): a series identifier.

    Returns:
        str: series title.
    """
    data = {}

    # edm:datasetName translate "DMA" to "Digital Media Archive"
    # language (indigenous and interview)

    for label, p in {
        'content_type':      'http://id.loc.gov/ontologies/bibframe/content',
        'creator':           'http://purl.org/dc/elements/1.1/creator',
        'description':       'http://purl.org/dc/elements/1.1/description',
        'identifier':        'http://purl.org/dc/elements/1.1/identifier',
        'language':          'http://purl.org/dc/elements/1.1/language',
        'title':             'http://purl.org/dc/elements/1.1/title',
        'access_rights':     'http://purl.org/dc/terms/accessRights',
        'alternative_title': 'http://purl.org/dc/terms/alternative',
        'contributor':       'http://purl.org/dc/terms/contributor',
        'date':              'http://purl.org/dc/terms/date',
        'location':          'http://purl.org/dc/terms/spatial'
    }.items():
        values = set()
        for row in g.query(
            prepareQuery('''
                SELECT ?value
                WHERE {
                    ?series_id ?p ?value
                }
            '''),
            initBindings={
                'p': rdflib.URIRef(p),
                'series_id': rdflib.URIRef(i)
            }
        ):
            values.add(' '.join(row[0].split()))
        data[label] = sorted(list(values))
    return data

def get_browse_terms(g, browse_type, sort_key='label'):
    """
    Get a dictionary of browse terms, along with the items for each term. It's
    currently not documented whether a browse should return series nodes, item
    nodes, or both - so this includes both. 

    Paramters:
        g (rdflib.Graph): a graph to search.
        browse_type (str): e.g., 'contributor', 'date', 'language', 'location'
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
        'date'       : 'http://purl.org/dc/terms/date',
        'language'   : 'http://purl.org/dc/elements/1.1/language',
        'location'   : 'http://purl.org/dc/terms/spatial'
    }
    assert browse_type in browse_types

    browse_dict = {}
    if browse_type == 'date':
        qres = g.query(
            prepareQuery('''
                SELECT ?date_str ?identifier 
                WHERE {{
                    ?identifier ?browse_type ?date_str .
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
        qres = g.query(
            prepareQuery('''
                SELECT ?browse_term ?identifier 
                WHERE {
                    ?identifier ?browse_type ?browse_term .
                }
            '''),
            initBindings={
                'browse_type': rdflib.URIRef(browse_types[browse_type])
            }
        )
        for browse_term, identifier in qres:
            label = GLOTTOLOG_LOOKUP[str(browse_term)]
            if not label in browse_dict:
                browse_dict[label] = set()
            browse_dict[label].add(str(identifier))
    else:
        qres = g.query(
            prepareQuery('''
                SELECT ?browse_term ?identifier 
                WHERE {
                    ?identifier ?browse_type ?browse_term .
                }
            '''),
            initBindings={
                'browse_type': rdflib.URIRef(browse_types[browse_type])
            }
        )
        for label, identifier in qres:
            if not label in browse_dict:
                browse_dict[label] = set()
            browse_dict[label].add(str(identifier))

    # convert identifiers set to a list.
    for k in browse_dict.keys():
        browse_dict[k] = sorted(list(browse_dict[k]))

    return browse_dict

def get_search_tokens_for_series_identifier(g, i):
    """
    Get the search tokens for a given series identifier from the graph.

    Parameters:
        g (rdflib.Graph): a graph to search.
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
        r = g.query(
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
    r = g.query(
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
    # NOTE: this currently only retrieves English-language labels. 
    r = g.query(
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
        search_tokens.append(GLOTTOLOG_LOOKUP[str(row[0])])
   
    # series-level dcterms:spatial (get every place name)
    # TODO

    # series-level dc:date (expand ranges)
    # TODO

    # item-level description
    for iid in get_item_identifiers_for_series(g, i):
        r = g.query(
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


if __name__ == '__main__':
    options = docopt(__doc__)

    with open('build_sqlite_dump.glotto.json') as f:
        GLOTTOLOG_LOOKUP = json.load(f)

    g = rdflib.Graph()
    g.parse(options['--graph'], format='turtle')

    con = sqlite3.connect(':memory:')
    cur = con.cursor()

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
        create virtual table search using fts5(
            id,
            text,
            tokenize="porter unicode61"
        );
    ''')
    cur.execute('''
        create table series(
            id text,
            info text
        );
    ''')
    cur.execute('commit')

    # load data
    cur.execute('begin')

    # load browses
    for browse_type, sort_key in {
        'contributor': 'count',
        'date': 'label',
        'language': 'count',
        'location': 'count'
    }.items():
        for browse_term, identifiers in get_browse_terms(
            g,
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
    for i in get_item_identifiers(g): 
        cur.execute('''
            insert into item (id, info) 
            values (?, ?);
            ''',
            (
                i,
                json.dumps(get_item_info(g, i))
            )
        )

    # load search
    for i in get_series_identifiers(g): 
        cur.execute('''
            insert into search (
                id, 
                text) values (?, ?);
            ''',
            (
                i,
                get_search_tokens_for_series_identifier(g, i)
            )
        )

    # load series 
    for i in get_series_identifiers(g): 
        cur.execute('''
            insert into series (
                id, 
                info) values (?, ?);
            ''',
            (
                i,
                json.dumps(get_series_info(g, i))
            )
        )
    cur.execute('commit')

    for line in sqlite_dump.iterdump(con):
        print(line)

"""Usage:
    build_sqlite_dump.py --graph=<graph>
"""

import json, os, rdflib, sqlite3, sqlite_dump, sys, timeit
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

def get_series_snippet_info(g, i):
    """
    Get the title, contributors, languages, locations, dates, resource type and
    access for a given series.

    Parameters:
        g (rdflib.Graph): a graph to search.
        i (str): a series identifier.

    Returns:
        str: series title.
    """
    data = {}

    for label, p in {
        'title': 'http://purl.org/dc/elements/1.1/title',
        'contributors': 'http://purl.org/dc/terms/contributor',
        'languages': 'http://purl.org/dc/elements/1.1/language',
        'locations': 'http://purl.org/dc/terms/spatial',
        'date': 'http://purl.org/dc/terms/date',
        'content': 'http://id.loc.gov/ontologies/bibframe/',
        'access_rights': 'http://purl.org/dc/terms/accessRights'
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
            values.add(row[0])
        data[label] = sorted(list(values))
    return data

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
    cur.execute('''
        create table item(
            id text,
            info text
        );
    ''')
    cur.execute('''
        create table browse(
            id text,
            type text,
            text text
        );
    ''')

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
        con.commit()

    # load series 
    for i in get_series_identifiers(g): 
        cur.execute('''
            insert into series (
                id, 
                info) values (?, ?);
            ''',
            (
                i,
                json.dumps(get_series_snippet_info(g, i))
            )
        )
        con.commit()

    # load item
    for i in get_item_identifiers(g): 
        cur.execute('''
            insert into item (
                id, 
                info) values (?, ?);
            ''',
            (
                i,
                ''
            )
        )
        con.commit()

    # add browse for contributor
    # add browse for date
    # add browse for language
    # add browse for location
    # extend snippet info so it shows all information about an item. 

    for line in sqlite_dump.iterdump(con):
        print(line)

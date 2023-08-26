"""Usage:
    build_sqlite_db.py [--graph=<graph>] [--db=<db>]
"""

import os, rdflib, sqlite3, sys
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
        results.add(row[0])
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
            search_tokens.append(r[0])

    # series-level edm:datasetName (from Aggregation expand DMA to "Digital Media Archive"
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
        search_tokens.append(lookup[r[0]])

    # series-level dc:language (get every language name)
    r = g.query(
        prepareQuery('''
            SELECT ?o
                WHERE {
                    ?series_id <http://purl.org/dc/elements/1.1/language> ?o
               }
        '''),
        initBindings={
            'p': rdflib.URIRef(p),
            'series_id': rdflib.URIRef(i)
        }
    )
    lookup = {
        'DMA': 'Digital Media Archive'
    }
    for row in r:
        search_tokens.append(lookup[r[0]])
   
    # series-level dcterms:spatial (get every place name)

    # series-level dc:date (expand ranges)

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
            search_tokens.append(r[0])
        

if __name__ == '__main__':
    options = docopt(__doc__)

    g = rdflib.Graph()
    g.parse(options['--graph'], format='turtle')

    if os.isfile(options['--db']): 
        # be sure the file is an SQLite database (by opening it) before
        # deleting it.
        con = sqlite3.connect(options['--db'])
        con.close()
        os.remove(options['--db'])
    # set up a connection to a fresh SQLite database.
    con = sqlite3.connect(options['--db'])
    
 
    # from the graph, get a list of all series identifiers in the system.
    # these are nodes with dcterms:hasPart.

    # make a searchable table, however you do that. 
    # the table has two fields: series_id and text.

    # for each series id...
    # insert the series id and full text.

    # test it out. 
    # does it return multiple language names?
    # can it handle searches without accents?
    # can it handle searches with accents? 
    # can it return multiple place names? 
    # how fast is it? 

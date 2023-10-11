import rdflib, sqlite3, sys
from rdflib.plugins.sparql import prepareQuery

'''Build a .dot file that diagrams hasFormat/isFormatOf relationships in MLC.

   Usage:
   cat meso.big.20230911.ttl | python diagram_has_part_relationships.py https://ark.lib.uchicago.edu/ark:61001/b2379fd2g51g | neato -Tsvg > output.svg
'''

def get_label(g, cur, ark):
    '''Get the label for a given ARK.
  
       Parameters:
          g (rdflib.Graph)
          cur (sqlite3 cursor)
          ark (str)
    '''
    # get an identifier. 
    for row in g.query(
        prepareQuery('''
            SELECT ?identifier
            WHERE {
                ?item_id <http://purl.org/dc/elements/1.1/identifier> ?identifier
            }
        '''),
        initBindings={
            'item_id': rdflib.URIRef(ark)
        }
    ):
        identifier = row[0]

    # get Medium_t from Item. 
    for row in cur.execute('''
        SELECT Medium_t
        FROM Item
        WHERE __kp_ItemID = ?
    ''', (identifier,)):
        medium = row[0]

    return '{} (#{}, {})'.format(
        ark.replace('https://ark.lib.uchicago.edu/ark:61001/', ''),
        identifier,
        medium
    )

if __name__ == '__main__':
    # load the graph from stdin. 
    g = rdflib.Graph()
    g.parse(data=sys.stdin.read(), format='turtle')

    # get the database to output formats. 
    con = sqlite3.connect('ucla.db')
    cur = con.cursor()

    # get command line argument and convert noids and plain ARKs to their full form.
    ark = sys.argv[1] 
    if ark.startswith('b2'):
        ark = 'https://ark.lib.uchicago.edu/ark:61001/' + ark
    elif ark.startswith('ark:61001/'):
        ark = 'https://ark.lib.uchicago.edu/' + ark

    # build a dictionary of hasFormat / isFormatOf relationships.
    need_to_search = set((ark,))
    searched = set()

    chos = {}
    while True:
        if len(list(need_to_search)) == 0:
            break
        else:
            ark = list(need_to_search)[0]

            for subject in g.subjects(
                rdflib.URIRef('http://purl.org/dc/terms/hasFormat'),
                rdflib.URIRef(ark)
            ):
                subject = str(subject)
                if not subject in chos:
                    chos[subject] = set()
                if not subject in searched:
                   need_to_search.add(subject)

            for object in g.objects(
                rdflib.URIRef(ark),
                rdflib.URIRef('http://purl.org/dc/terms/hasFormat')
            ):
                object = str(object)
                if not ark in chos:
                    chos[ark] = set()
                chos[ark].add(object)
                if not object in searched:
                    need_to_search.add(object)

            need_to_search.remove(ark)
            searched.add(ark)

    # output .dot file.
    print('digraph {')
    print('overlap=false;')
    print('sep="60";')
    for k, vs in chos.items():
        for v in vs:
            print('"{}" -> "{}" [ label="dcterms:hasFormat" lblstyle="above, sloped" ];'.format(
                get_label(g, cur, k),
                get_label(g, cur, v)
            ))
    print('}')

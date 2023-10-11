import rdflib, sys

# add kernel metadata to triples.

if __name__ == '__main__':
    g = rdflib.Graph()

    BASE = rdflib.Namespace('https://ark.lib.uchicago.edu/ark:61001/')

    NAMESPACES = {}
    for k, v in {
        'aes60-2011': 'https://www.aes.org/publications/standards/',
        'audioMD':    'http://www.loc.gov/audioMD',
        'bf':         'http://id.loc.gov/ontologies/bibframe/',
        'dc':         'http://purl.org/dc/elements/1.1/',
        'dcterms':    'http://purl.org/dc/terms/',
        'dma':        'http://lib.uchicago.edu/dma/',
        'edm':        'http://www.europeana.eu/schemas/edm/',
        'erc':        'http://purl.org/kernel/elements/1.1/',
        'lexvo':      'https://www.iso.org/standard/39534.html',
        'olac':       'http://www.language−archives.org/OLAC/metadata.html',
        'ore':        'http://www.openarchives.org/ore/terms/',
        'vra':        'http://purl.org/vra/'
    }.items():
        NAMESPACES[k] = rdflib.Namespace(v)
        g.bind(k, rdflib.Namespace(v))

    g.parse(data=sys.stdin.read(), format='turtle')

    for provided_cho in g.subjects(rdflib.RDF['type'], NAMESPACES['edm']['ProvidedCHO']):

        # erc:who
        whos = set()
        if len(whos) == 0:
            for o in g.objects(provided_cho, rdflib.DC['creator']):
                whos.add(o)
        if len(whos) == 0:
            for o in g.objects(provided_cho, rdflib.DCTERMS['creator']):
                whos.add(o)
        if len(whos) == 0:
            for o in g.objects(provided_cho, rdflib.DC['contributor']):
                whos.add(o)
        if len(whos) == 0:
            for o in g.objects(provided_cho, rdflib.DCTERMS['contributor']):
                whos.add(o)
        if len(whos) == 0:
            for o in g.objects(provided_cho, rdflib.DC['publisher']):
                whos.add(o)
        if len(whos) == 0:
            for o in g.objects(provided_cho, rdflib.DCTERMS['publisher']):
                whos.add(o)
        if len(whos) == 0:
            g.add((
                provided_cho,
                NAMESPACES['erc']['who'],
                rdflib.Literal('(:unav)')
            ))
        else:
            g.add((
                provided_cho,
                NAMESPACES['erc']['who'],
                rdflib.Literal('; '.join(sorted(list(whos))))
            ))

        # erc:what
        # pulls from dc:title or dc:description, in that order.
        # dc:title can be a literal, or it can be a blank node 
        # where dma:collectionTitle contains the actual title.
        whats = set()
        if len(whats) == 0:
            for o in g.objects(provided_cho, rdflib.DC['title']):
                whats.add(o)
        if len(whats) == 0:
            for o in g.objects(provided_cho, rdflib.DCTERMS['title']):
                whats.add(o)
        if len(whats) == 0:
            for o in g.objects(provided_cho, rdflib.DC['description']):
                whats.add(o)
        if len(whats) == 0:
            for o in g.objects(provided_cho, rdflib.DCTERMS['description']):
                whats.add(o)
        if len(whats) == 0:
            g.add((
                provided_cho,
                NAMESPACES['erc']['what'],
                rdflib.Literal('(:unav)')
            ))
        else:
            g.add((
                provided_cho,
                NAMESPACES['erc']['what'],
                rdflib.Literal('; '.join(sorted(list(whats))))
            ))

        # erc:when
        whens = set()
        for o in g.objects(provided_cho, rdflib.DCTERMS['date']):
            whens.add(o)
        if len(whens) == 0:
            g.add((
                provided_cho,
                NAMESPACES['erc']['when'],
                rdflib.Literal('(:unav)')
            ))
        else:
            g.add((
                provided_cho,
                NAMESPACES['erc']['when'],
                rdflib.Literal('; '.join(sorted(list(whens))))
            ))

        # erc:where
        wheres = set()
        for identifier in g.objects(provided_cho, rdflib.DCTERMS['identifier']):
            wheres.add(identifier)
        if len(wheres) == 0:
            g.add((
                provided_cho,
                NAMESPACES['erc']['where'],
                rdflib.Literal('(:unav)')
            ))
        else:
            g.add((
                provided_cho,
                NAMESPACES['erc']['where'],
                sorted(list(wheres))[0]
            ))

    sys.stdout.write(g.serialize(format='turtle', base=BASE))

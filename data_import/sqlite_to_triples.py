#!/usr/bin/env python
"""Usage:
    sqlite_to_triples.py (--mesoamerican|--ucla) <DATABASE>
"""

import datetime, json, pytz, rdflib, re, sqlite3, sys
from docopt import docopt

mesoamerican_language_codes = set((
'acc', 'acr', 'agu', 'aig', 'amu', 'azd', 'azg', 'azm', 'azn', 'azz', 'brn',
'bzd', 'caa', 'cab', 'cac', 'cak', 'cbm', 'cco', 'ccr', 'chd', 'chf', 'chj',
'chq', 'chz', 'cip', 'cjp', 'cjr', 'ckc', 'ckd', 'cke', 'ckf', 'cki', 'ckj',
'ckk', 'ckw', 'ckz', 'cle', 'clo', 'cly', 'cnl', 'cnm', 'cnt', 'cob', 'coc',
'coj', 'cok', 'coz', 'cpa', 'crn', 'csa', 'cso', 'csr', 'cta', 'cte', 'cti',
'ctl', 'ctp', 'ctu', 'ctz', 'cuc', 'cun', 'cut', 'cux', 'cuy', 'cvn', 'cya',
'czn', 'dih', 'emy', 'esn', 'gsm', 'gut', 'gym', 'hch', 'hds', 'hsf', 'hue',
'hus', 'huv', 'hva', 'hve', 'hvv', 'itz', 'ixc', 'ixi', 'ixj', 'ixl', 'jac',
'jai', 'jic', 'jmx', 'kek', 'kjb', 'klb', 'knj', 'lac', 'len', 'lsp', 'maa',
'mab', 'maj', 'mam', 'maq', 'mat', 'mau', 'maz', 'mbz', 'mce', 'mco', 'mdv',
'meh', 'mfs', 'mfy', 'mhc', 'mib', 'mie', 'mig', 'mih', 'mii', 'mil', 'mim',
'mio', 'mip', 'miq', 'mir', 'mit', 'miu', 'mix', 'miy', 'miz', 'mjc', 'mks',
'mmc', 'mms', 'mom', 'mop', 'mpf', 'mpm', 'mqh', 'msd', 'mtn', 'mto', 'mtu',
'mtx', 'mtz', 'mvc', 'mvg', 'mvj', 'mxa', 'mxb', 'mxp', 'mxq', 'mxs', 'mxt',
'mxv', 'mxy', 'mza', 'mzi', 'mzl', 'naz', 'nch', 'nci', 'ncj', 'ncl', 'ncs',
'ncx', 'neq', 'ngu', 'nhc', 'nhe', 'nhg', 'nhi', 'nhk', 'nhm', 'nhn', 'nhp',
'nhq', 'nht', 'nhv', 'nhw', 'nhx', 'nhy', 'nhz', 'nln', 'nlv', 'npl', 'nsu',
'ntp', 'nuz', 'ocu', 'ood', 'opt', 'ote', 'otl', 'otm', 'otn', 'otq', 'ots',
'ott', 'otx', 'otz', 'pay', 'pbe', 'pbf', 'pbs', 'pca', 'pei', 'pia', 'plo',
'pls', 'pmq', 'pmz', 'poa', 'pob', 'poc', 'poe', 'poh', 'poi', 'poq', 'pos',
'pou', 'pow', 'ppi', 'ppl', 'pps', 'pua', 'pxm', 'qcs', 'quc', 'quj', 'qum',
'qut', 'quu', 'quv', 'qxi', 'rma', 'sab', 'sei', 'stp', 'sum', 'sut', 'tac',
'tar', 'tbu', 'tcf', 'tcu', 'tcw', 'tee', 'tep', 'tfr', 'thh', 'tku', 'tla',
'tlc', 'tlp', 'toc', 'toj', 'too', 'top', 'tos', 'tpc', 'tpl', 'tpp', 'tpt',
'tpx', 'tqt', 'trc', 'trq', 'trs', 'tsz', 'ttc', 'twr', 'tzb', 'tzc', 'tze',
'tzh', 'tzj', 'tzo', 'tzs', 'tzt', 'tzu', 'tzz', 'ulw', 'usp', 'var', 'vmc',
'vmj', 'vmm', 'vmp', 'vmq', 'vmx', 'vmy', 'vmz', 'xcm', 'xcn', 'xgr', 'xin',
'xpo', 'xta', 'xtb', 'xtd', 'xti', 'xtj', 'xtl', 'xtm', 'xtn', 'xtp', 'xts',
'xtt', 'xtu', 'xty', 'yan', 'yaq', 'yua', 'yus', 'zaa', 'zab', 'zac', 'zad',
'zae', 'zaf', 'zai', 'zam', 'zao', 'zap', 'zaq', 'zar', 'zas', 'zat', 'zav',
'zaw', 'zax', 'zca', 'zoc', 'zoh', 'zoo', 'zoq', 'zor', 'zos', 'zpa', 'zpb',
'zpc', 'zpd', 'zpe', 'zpf', 'zpg', 'zph', 'zpi', 'zpj', 'zpk', 'zpl', 'zpm',
'zpn', 'zpo', 'zpp', 'zpq', 'zpr', 'zps', 'zpt', 'zpu', 'zpv', 'zpw', 'zpx',
'zpy', 'zpz', 'zsr', 'zte', 'ztg', 'ztl', 'ztm', 'ztn', 'ztp', 'ztq', 'zts',
'ztt', 'ztu', 'ztx', 'zty'))

def get_collections(cur):
    """Get a list of all CollectionIDs.

       Args:
           cur - an SQLite3 cursor.

       Returns:
           a list of strings.

       Notes:
           In July 2022 I found a few dangling references- of approximately 
           2000 Collection IDs, the following Collection IDs appear in the
           Collection table but not in the Item table:

           '4614', '1213', '4715', '4540', '2237', '4328', '1859'

           And the following Items appear in the Item table but not in the 
           Collection table:

           '4718', '45467'
    """
    results = set()

    sql = 'SELECT __kp_CollectionID FROM Collection WHERE NOT (recommendation = "N/A" AND z_Digitization = "N/A");'
    cur.execute(sql)
    for r in cur.fetchall():
        if r[0].isnumeric():
            results.add(int(r[0]))
    # sort as integers and return strings.
    return [str(r) for r in sorted(results)]

def get_items(cur):
    """Get a list of all ItemIDs.

       Args:
           cur - an SQLite3 cursor.

       Returns:
           a list of strings.
    """
    items = set()
    for cid in get_collections(cur):
        for iid in collection_itemids(cur, cid):
            items.add(iid)
    return sorted(list(items))

def get_is_format_of(cur, iid):
    """Make sure the items returned actually exist in the Item table."""
    items = set()
    sql = '''SELECT     ItemSource.__kf_ItemID_Source 
             FROM       ItemSource 
             WHERE      ItemSource.__kf_ItemID = ?
             AND        ItemSource.relationship = 'Is Format Of';'''
    cur.execute(sql, (iid,))
    for r in cur.fetchall():
        items.add(r[0])

    items_checked = set()
    for i in items:
        sql = '''SELECT     Item.__kp_ItemID
                 FROM       Item
                 WHERE      Item.__kp_ItemID = ?;'''
        cur.execute(sql, (i,))
        if len(cur.fetchall()) > 0:
            items_checked.add(i)

    return sorted(list(items_checked))

def get_has_format(cur, iid):
    """Make sure the items returned actually exist in the Item table."""
    items = set()
    sql = '''SELECT ItemSource.__kf_ItemID
             FROM   ItemSource 
             WHERE  ItemSource.__kf_ItemID_Source = ?
             AND    ItemSource.relationship = 'Is Format Of';'''
    cur.execute(sql, (iid,))
    for r in cur.fetchall():
        items.add(r[0])

    items_checked = set()
    for i in items:
        sql = '''SELECT     Item.__kp_ItemID
                 FROM       Item
                 WHERE      Item.__kp_ItemID = ?;'''
        cur.execute(sql, (i,))
        if len(cur.fetchall()) > 0:
            items_checked.add(i)

    return sorted(list(items_checked))

def collection_itemids(cur, cid):
    """Get the ItemIDs for a given Collection.

       Args:
           cur - an SQLite3 cursor.
           cid - a CollectionID as a numeric string.

       Returns:
           a list of ItemIDs as numeric strings, or an empty list. 

       Notes:
           The first time this function runs it populates a 'lookup' 
           attribute to keep track of item and collection IDs.
    """
    if collection_itemids.lookup == {}:
        collection_itemids_build_lookup(cur)
            
    if cid in collection_itemids.lookup:
        return collection_itemids.lookup[cid]
    else:
        return []

def item_collectionids(cur, iid):
    """Get the ItemIDs for a given Collection.

       Args:
           cur - an SQLite3 cursor.
           cid - a CollectionID as a numeric string.

       Returns:
           a list of ItemIDs as numeric strings, or an empty list. 

       Notes:
           The first time this function runs it populates a 'lookup' 
           attribute to keep track of item and collection IDs.
    """
    if collection_itemids.lookup == {}:
        collection_itemids_build_lookup(cur)

    lookup = {}
    for cid, iids in collection_itemids.lookup.items():
        for iid in iids:
            if not iid in lookup:
                lookup[iid] = []
            lookup[iid].append(cid)
   
    if iid in lookup: 
        return lookup[iid]
    else:
        return []

def collection_itemids_build_lookup(cur):
    """Build a global variable lookup for Collection IDs and Item IDs to speed
       the script up. 

       Args:
           cur - an SQLite3 cursor.

       Side Effect:
           populates the collection_itemids.lookup global variable.
    """
    sql = 'SELECT __kp_ItemID, z_CollectionIDs FROM Item'
    cur.execute(sql)
    for r in cur.fetchall():
        if r[1] not in ('None', ''):
            for cid in r[1].split(','):
                if cid:
                    if not cid in collection_itemids.lookup:
                        collection_itemids.lookup[cid] = []
                    if not r[0] in collection_itemids.lookup[cid]:
                        # store itemids as integers before sorting.
                        collection_itemids.lookup[cid].append(int(r[0]))

    # sort itemids numerically and convert to strings.
    for cid in collection_itemids.lookup.keys():
        collection_itemids.lookup[cid].sort()
        collection_itemids.lookup[cid] = [str(i) for i in collection_itemids.lookup[cid]]
collection_itemids.lookup = {}

def coverageids(cur, iid):
    """Get a list of ItemCoverage identifiers for a given Item ID.

       Args: 
           cur - an SQLite3 cursor.
           iid - an item identifier as a numeric string.

       Returns:
           a sorted list of __kp_ItemCoverageID's.
    """
    results = set()
    sql = 'SELECT __kp_ItemCoverageID FROM ItemCoverage WHERE __kf_ItemID = ?'
    cur.execute(sql, (iid,))
    for r in cur.fetchall():
        if r[0] != '' and r[0] != 'None':
            results.add(r[0])
    # sort as integers and return strings.
    return [str(r) for r in sorted(results)]

def itemlanguage_ids(cur, iid):
    """Get a list of ItemLanguages identifiers for a given Item ID.

       Args: 
           cur - an SQLite3 cursor.
           iid - an item identifier as a numeric string.

       Returns:
           a sorted list of __ItemLanguageID's.
    """
    results = set()
    sql = 'SELECT __ItemLanguageID FROM ItemLanguages WHERE __kp_ItemID = ?;'
    cur.execute(sql, (iid,))
    for r in cur.fetchall():
        if r[0] != 'None':
            assert r[0].isnumeric()
            results.add(int(r[0]))
    # sort as integers and return strings.
    return [str(r) for r in sorted(results)]

def get_mappings_data():
    """Get the MAPPINGS file as data.

       Args: 
           none

       Returns:
           A list of tuples, where each tuple represents a row in MAPPINGS.
           Each row includes:
           - a subject as a string, e.g., "ProvidedCHO"
           - a predicate as a string, e.g., "dc:title"
           - a table as a string, e.g., "Item"
           - a field as a string, e.g., "__kp_ItemID"
    """
    mappings = []
    with open('MAPPINGS') as f:
        for line in f:
            if line[0] == '#':
                continue
            if line.strip() == '':
                continue
            field_table, predicate, subject = line.strip().split('\t')
            field = '_'.join(field_table.split('_')[0:-1])
            table = field_table.split('_')[-1]
            predicate = tuple(predicate.split('--'))
            mappings.append((subject, predicate, table, field))
    return mappings

def filter_mappings_data(mappings, tables = [], fields = [], predicates = [], subjects = []):
    """Filter mappings data for simple predicates. This function will not
         return anything from MAPPINGS where the resulting triple will include
         blank nodes or classes.

       Args:
           mappings - a data structure as returned by get_mappings_data()
           tables - a list of table names as strings.
           fields - a list of field names as strings.
           predicates - a list of linked data predicates as strings.
           subjects - a list of linked data subjects as strings.

       Returns:
           a filtered mappings data structure.
    """
    result = []
    if fields or predicates:
        raise NotImplementedError
    for record in mappings:
        if tables and not record[2] in tables:
            continue
        if any(['[' in r for r in record[1]]):
            continue
        if subjects and not record[0] in subjects:
            continue
        result.append(record)
    return result

def filter_mappings_data_for_classes(mappings, tables = [], fields = [], predicates = [], subjects = []):
    """Filter mappings data for predicates including classes. These will be
       represented in MAPPINGS in entries like:
       bf:identifiedBy [ a bf:Local; rdf:value xs:string ]

       Args:
           mappings - a data structure as returned by get_mappings_data()
           tables - a list of table names as strings.
           fields - a list of field names as strings.
           predicates - a list of linked data predicates as strings.
           subjects - a list of linked data subjects as strings.

       Returns:
           a filtered mappings data structure.
    """
    result = []
    if fields or predicates:
        raise NotImplementedError
    for record in mappings:
        if tables and not record[2] in tables:
            continue
        if not '[' in record[1][0]:
            continue
        if subjects and not record[0] in subjects:
            continue

        # in a string like: 
        # bf:identifiedBy [ a bf:Local ; rdf:value xs:string ]
        # extract bf:identifiedBy and bf:Local
        m = re.search('^([^[ ]+)\s*\[\s*a\s*([^[; ]+)', record[1][0])
        if not m:
            continue
        
        result.append((record[0], ((m.group(1), m.group(2)),), record[2], record[3]))
    return result

def dblookup(cur, pk, table, fields):
    if table == 'AssociatedCollections':
        s = '''SELECT     {}
               FROM       AssociatedCollections
               INNER JOIN CollectionRelated
               ON         CollectionRelated.__kf_AssociatedCollectionID = AssociatedCollections.__kp_AssociatedCollectionID
               WHERE      CollectionRelated.__kf_CollectionID=?
               ORDER BY   CAST(AssociatedCollections.__kp_AssociatedCollectionID AS INTEGER)'''
    elif table == 'Collection':
        s = '''SELECT     {}
               FROM       Collection
               WHERE      __kp_CollectionID = ?
               ORDER BY   CAST(__kp_CollectionID AS INTEGER)'''
    elif table == 'CollectionTitles':
        s = '''SELECT     {}
               FROM       CollectionTitles
               WHERE      __kp_CollectionID = ?
               ORDER BY   CAST(__kp_CollectionID AS INTEGER), 
                          CAST(__ItemTitleID AS INTEGER)'''
    elif table == 'Containers':
        s = '''SELECT     {}
               FROM       Containers
               WHERE      __kf_ItemID = ?
               ORDER BY   CAST(Containers.__kp_ContainersID AS INTEGER)'''
    elif table == 'Coverage':
        s = '''SELECT     {}
               FROM       Coverage
               INNER JOIN ItemCoverage 
               ON         ItemCoverage.__kf_AreaID = Coverage.__kp_CoverageID
               WHERE      ItemCoverage.__kp_ItemCoverageID = ?
               ORDER BY   CAST(ItemCoverage.__kp_ItemCoverageID AS INTEGER),
                          CAST(Coverage.__kp_CoverageID AS INTEGER)'''
    elif table == 'Item':
        s = '''SELECT     {}
               FROM       Item
               WHERE      __kp_ItemID = ?
               ORDER BY   CAST(Item.__kp_ItemID AS INTEGER)'''
    elif table == 'ItemContributors':
        s = '''SELECT     {}
               FROM       ItemContributors
               WHERE      __kp_ItemID = ?
               ORDER BY   CAST(ItemContributors.__ItemContributionID AS INTEGER)'''
    elif table == 'ItemCoverage':
        s = '''SELECT     {}
               FROM       ItemCoverage
               INNER JOIN Coverage
               ON         Coverage.__kp_CoverageID = ItemCoverage.__kf_AreaID
               WHERE      __kp_ItemCoverageID = ?
               ORDER BY   CAST(ItemCoverage.__kp_ItemCoverageID AS INTEGER),
                          CAST(Coverage.__kp_CoverageID AS INTEGER)'''
    elif table == 'ItemFormat':
        s = '''SELECT     {}
               FROM       ItemFormat
               WHERE      __kf_ItemID = ?
               ORDER BY   CAST(ItemFormat.__kp_ItemFormatID AS INTEGER)'''
    elif table == 'ItemLanguages':
        s = '''SELECT     {}
               FROM       ItemLanguages
               INNER JOIN Language
               ON         Language.__kp_LanguageID = ItemLanguages.__kp_LanguageID
               WHERE      __ItemLanguageID = ?
               ORDER BY   CAST(ItemLanguages.__ItemLanguageID AS INTEGER), 
                          CAST(ItemLanguages.__kp_LanguageID AS INTEGER)'''
    elif table == 'ItemSource':
        s = '''SELECT     {}
               FROM       ItemSource
               WHERE      __kf_ItemID = ?
               ORDER BY   CAST(ItemSource.__kp_ItemSouceID AS INTEGER)'''
    elif table == 'ItemTitle':
        s = '''SELECT     DISTINCT {}
               FROM       ItemTitle
               WHERE      __kp_ItemID = ?
               ORDER BY   CAST(ItemTitle.__ItemTitleID AS INTEGER)'''
    elif table == 'Language':
        s = '''SELECT     {}
               FROM       Language
               INNER JOIN ItemLanguages 
               ON         ItemLanguages.__kp_LanguageID = Language.__kp_LanguageID
               WHERE      ItemLanguages.__ItemLanguageID = ?
               ORDER BY   CAST(ItemLanguages.__ItemLanguageID AS INTEGER), 
                          CAST(Language.__kp_LanguageID AS INTEGER)'''
    elif table == 'LanguageMacro':
        s = '''SELECT     {}
               FROM       LanguageMacro
               INNER JOIN ItemLanguages 
               ON         ItemLanguages.__kp_LanguageID = Language.__kp_LanguageID
               INNER JOIN Language
               ON         Language.Code_t = LanguageMacro.Code_t
               WHERE      ItemLanguages.__ItemLanguageID = ?
               ORDER BY   CAST(ItemLanguages.__ItemLanguageID AS INTEGER),
                          CAST(LanguageMacro.__kp_LanguageMacroID AS INTEGER)'''
    elif table == 'LanguageNames':
        s = '''SELECT     {}
               FROM       LanguageNames
               INNER JOIN ItemLanguages 
               ON         ItemLanguages.__kp_LanguageID = Language.__kp_LanguageID
               INNER JOIN Language
               ON         Language.Code_t = LanguageNames.Code_t
               WHERE      ItemLanguages.__ItemLanguageID = ?
               ORDER BY   CAST(ItemLanguages.__ItemLanguageID AS INTEGER),
                          CAST(Language.__kp_LanguageID AS INTEGER),
                          CAST(LanguageNames.__kp_LanguageNamesID AS INTEGER)'''
    elif table == 'SoundFormat':
        s = '''SELECT     {}
               FROM       SoundFormat
               INNER JOIN Item        
               ON         Item.__kp_ItemID = ItemFormat.__kf_ItemID
               INNER JOIN ItemFormat  
               ON         ItemFormat.__kp_ItemFormatID = SoundFormat.__kf_ItemFormatID
               WHERE      Item.__kp_ItemID = ?
               ORDER BY   CAST(ItemFormat.__kp_ItemFormatID AS INTEGER), 
                          CAST(SoundFormat.__kp_SoundFormatID AS INTEGER)'''
    elif table == 'UNESCOAtlas':
        s = '''SELECT     {}
               FROM       UNESCOAtlas
               INNER JOIN ItemLanguages 
               ON         ItemLanguages.__kp_LanguageID = UNESCOAtlas.__kp_LanguageID
               WHERE      ItemLanguages.__ItemLanguageID = ?
               ORDER BY   CAST(ItemLanguages.__ItemLanguageID AS INTEGER),
                          CAST(UNESCOAtlas.__kp_LanguageID AS INTEGER)'''
    else:
        print(table)
        raise NotImplementedError

    results = []

    # if any field doesn't already include a dot, prepend it with the table name.
    full_field_names = []
    for f in fields:
        if '.' in f:
            full_field_names.append(f)
        else:
            full_field_names.append('{}.{}'.format(table, f))

    sql = s.format(', '.join(full_field_names))
    try:
        cur.execute(sql, (pk,))
    except sqlite3.OperationalError:
        print(pk)
        print(table)
        print(fields)
        raise

    for sql_result in cur.fetchall():
        if all([r == 'None' or r == '' for r in sql_result]):
            continue
        else:
            result = []
            for r in sql_result:
                if r == 'None':
                    result.append('')
                else:
                    result.append(r)
        results.append(result)
    return results

if __name__ == '__main__':
    options = docopt(__doc__)

    with open('sqlite_to_triples.soundfile_data.json') as f:
        soundfile_data = json.load(f)
    with open('sqlite_to_triples.collection_id_arks.json') as f:
        collection_id_arks = json.load(f)
    with open('sqlite_to_triples.item_id_arks.json') as f:
        item_id_arks = json.load(f)
    with open('sqlite_to_triples.filenames_to_identifiers.json') as f:
        filenames_to_identifiers = json.load(f)
    with open('sqlite_to_triples.collection_language_codes.json') as f:
        collection_language_codes = json.load(f)
    with open('sqlite_to_triples.item_language_codes.json') as f:
        item_language_codes = json.load(f)

    con = sqlite3.connect(options['<DATABASE>'])
    cur = con.cursor()

    mappings = get_mappings_data()

    # confirm that every table and field in MAPPINGS appears in the database.
    for m in mappings:
        sql = 'SELECT name FROM sqlite_master WHERE type=\'table\' AND name=\'{}\''.format(m[2])
        cur.execute(sql)
        try:
            assert len(cur.fetchall()) == 1
        except:
            print(m)
            sys.exit()

        sql = 'PRAGMA table_info({});'.format(m[2])
        cur.execute(sql)
        assert any([r[1] == m[3] for r in cur.fetchall()])

    g = rdflib.Graph()

    BASE = rdflib.Namespace('https://ark.lib.uchicago.edu/ark:61001/')

    NAMESPACES = {}
    for k, v in {
        'ac':         'http://www.audiocommons.org/ac-ontology/aco',
        'aes60-2011': 'https://www.aes.org/publications/standards/',
        'audioMD':    'http://www.loc.gov/audioMD',
        'bf':         'http://id.loc.gov/ontologies/bibframe/',
        'dc':         'http://purl.org/dc/elements/1.1/',
        'dcterms':    'http://purl.org/dc/terms/',
        'dma':        'http://lib.uchicago.edu/dma/',
        'ebucore':    'https://www.ebu.ch/metadata/ontologies/ebucore/',
        'edm':        'http://www.europeana.eu/schemas/edm/',
        'erc':        'http://purl.org/kernel/elements/1.1/',
        'fn':         'http://www.w3.org/2005/xpath-functions',
        'foaf':       'http://xmlns.com/foaf/spec/',
        'icu':        'http://lib.uchicago.edu/icu/',
        'lexvo':      'https://www.iso.org/standard/39534.html',
        'olac':       'http://www.language−archives.org/OLAC/metadata.html',
        'ore':        'http://www.openarchives.org/ore/terms/',
        'premis':     'https://id.loc.gov/ontologies/premis−3−0−0.html',
        'rel':        'http://id.loc.gov/vocabulary/relators/',
        'uchicago':   'http://lib.uchicago.edu/',
        'vra':        'http://purl.org/vra/'
    }.items():
        NAMESPACES[k] = rdflib.Namespace(v)
        g.bind(k, rdflib.Namespace(v))

    now = datetime.datetime.now()

    # JEJ: to speed up development, set a collection limit here.
    c_count = 0 
    c_limit = -1

    for cid in get_collections(cur):
        output = False
        if options['--mesoamerican'] and \
        bool(mesoamerican_language_codes & set(collection_language_codes[cid])):
            output = True
        if options['--ucla'] and \
        not(bool(mesoamerican_language_codes & set(collection_language_codes[cid]))):
            output = True
        if not output:
            continue
       
        if c_limit != -1: 
            if c_count > c_limit:
                break
            else:
                c_count += 1

        cark = collection_id_arks[cid]
        cnoid = cark.replace('ark:61001/', '')

        # JEJ: to speed up development, uncomment the following two lines to
        #      retrieve a subgraph for testing.
        #if not cnoid in ('b27332c4zp6g', 'b2tw6sr2xh2v', 'b2zz3qj0kb9b', 'b2zz97j0vb2v', 'b2s46wx8cv10', 'b2kd9bc4mz25', 'b2ht2fr8dx9k'):
        #    continue
            
        #if not cnoid in ('b20j4f69h52j',):
        #    continue

        csagg = BASE['{}/aggregation'.format(cnoid)]
        cscho = BASE['{}'.format(cnoid)]
        csrem = BASE['{}/rem'.format(cnoid)]
        csark = rdflib.URIRef('https://n2t.net/ark:61001/{}'.format(cnoid))

        # collection -- ore:Aggregation -- rdf:type
        g.add((
            csagg,
            rdflib.RDF['type'],
            NAMESPACES['ore']['Aggregation']
        ))

        # collection -- ore:Aggregation -- edm:aggregatedCHO
        g.add((
            csagg,
            NAMESPACES['edm']['aggregatedCHO'],
            cscho
        ))

        # collection -- ore:Aggregation -- edm:dataProvider
        g.add((
            csagg,
            NAMESPACES['edm']['dataProvider'],
            rdflib.Literal('University of Chicago Library')
        ))

        # collection -- ore:Aggregation -- edm:isShownAt
        g.add((
            csagg,
            NAMESPACES['edm']['isShownAt'],
            rdflib.Literal('https://n2t.net/ark:61001/{}'.format(cnoid))
        ))

        # collection -- ore:Aggregation -- edm:provider
        g.add((
            csagg,
            NAMESPACES['edm']['provider'],
            rdflib.Literal('University of Chicago Library')
        ))

        # collection -- ore:Aggregation -- edm:rights
        g.add((
            csagg,
            NAMESPACES['edm']['rights'],
            rdflib.URIRef('https://rightsstatements.org/vocab/NoC-US/1.0/')
        ))

        # collection -- ore:Aggregation -- fn:collection
        g.add((
            csagg,
            NAMESPACES['fn']['collection'],
            rdflib.Literal('dma')
        ))
        g.add((
            csagg,
            NAMESPACES['fn']['collection'],
            rdflib.URIRef('http://lib.uchicago.edu/mlc')
        ))

        # collection -- ore:Aggregation -- ore:isDescribedBy
        g.add((
            csagg,
            NAMESPACES['ore']['isDescribedBy'],
            csrem
        ))

        # collection -- edm:ProvidedCHO -- rdf:type
        g.add((
            cscho,
            rdflib.RDF['type'],
            NAMESPACES['edm']['ProvidedCHO']
        ))

        # collection -- edm:ProvidedCHO 
        for subject, predicates, table, field in filter_mappings_data(
            mappings, 
            tables = ('AssociatedCollections', 'Collection', 'CollectionTitles'),
            subjects = ('edm:ProvidedCHO')
        ):
            for o in dblookup(cur, cid, table, [field]):
                if len(predicates) == 1:
                    p = predicates[0].split(':')
                    g.add((
                        cscho,
                        NAMESPACES[p[0]][p[1]],
                        rdflib.Literal(o[0].strip())
                    ))
                else:
                    raise NotImplementedError

        for subject, predicates, table, field in filter_mappings_data_for_classes(
            mappings, 
            tables = ('AssociatedCollections', 'Collection', 'CollectionTitles'),
            subjects = ('edm:ProvidedCHO')
        ):
            for o in dblookup(cur, cid, table, [field]):
                if len(predicates) == 1:
                    p0 = predicates[0][0].split(':')
                    p1 = predicates[0][1].split(':')

                    b = rdflib.BNode()

                    g.add((
                        cscho,
                        NAMESPACES[p0[0]][p0[1]],
                        b
                    ))
                    g.add((
                        b,
                        rdflib.RDF['type'],
                        NAMESPACES[p1[0]][p1[1]]
                    ))
                    g.add((
                        b,
                        rdflib.RDF['value'],
                        rdflib.Literal(o[0].strip())
                    ))
                else:
                    raise NotImplementedError

        # collection -- edm:ProvidedCHO -- dc:language
        # collection -- edm:ProvidedCHO -- dcterms:language
        codes = set()
        for iid in collection_itemids(cur, cid):
            for lid in itemlanguage_ids(cur, iid):
                for row in dblookup(
                    cur, 
                    lid, 
                    'Language', 
                    ['Language.Code_t']
                ):
                    codes.add(row[0])
        for code in codes:
            g.add((
                cscho,
                NAMESPACES['dc']['language'],
                rdflib.Literal(code)
            ))
            g.add((
                cscho,
                NAMESPACES['dcterms']['language'],
                rdflib.Literal(code)
            ))

        # collection -- edm:ProvidedCHO -- dcterms:contributor
        contributors = set()
        for iid in collection_itemids(cur, cid): 
            for name, role in dblookup( 
                cur, 
                iid,
                 'ItemContributors',
                 ['name', 'role']
            ):
                if role in ('consultant', 'participant', 'performer', 'singer', 'speaker'):
                    contributors.add(name)
        for contributor in contributors:
            g.add((
                cscho,
                NAMESPACES['dcterms']['contributor'],
                rdflib.Literal(contributor)
            ))

        # collection -- edm:ProvidedCHO -- dcterms:creator
        creators = set()
        for iid in collection_itemids(cur, cid): 
            for name, role in dblookup( 
                cur, 
                iid,
                 'ItemContributors',
                 ['name', 'role']
            ):
                if role in ('author', 'compiler', 'depositor', 'editor', 'interviewer', 'recorder', 'researcher', 'translator'):
                    creators.add(name)
        for creator in creators:
            g.add((
                cscho,
                NAMESPACES['dcterms']['creator'],
                rdflib.Literal(creator)
            ))

        # collections -- edm:ProvidedCHO -- dcterms:date
        dates = []
        for iid in collection_itemids(cur, cid):
            for start_year, end_year in dblookup(
                cur,
                iid,
                'Item',
                ['DateCreation_t', 'DateCreationRange2_t']
            ):
                if start_year.strip():
                    dates.append(start_year.strip())
                if end_year.strip():
                    dates.append(end_year.strip())
        dates.sort()
        if len(dates) == 0:
            g.add((
                cscho,
                rdflib.DCTERMS['date'],
                rdflib.Literal('(:unav)')
            ))
        elif len(dates) == 1:
            g.add((
                cscho,
                rdflib.DCTERMS['date'],
                rdflib.Literal(dates[0])
            ))
        else:
            g.add((
                cscho,
                rdflib.DCTERMS['date'],
                rdflib.Literal('{}/{}'.format(dates[0], dates[-1]))
            ))

        # collections -- edm:ProvidedCHO -- dcterms:hasPart
        for iid in collection_itemids(cur, cid):
            iark = item_id_arks[iid]
            inoid = iark.replace('ark:61001/', '')
            ischo = BASE['{}'.format(inoid)]
            g.add((
                cscho,
                rdflib.DCTERMS['hasPart'],
                ischo
            ))

        # collections -- edm:ProvidedCHO -- dcterms:identifier
        g.add((
            cscho,
            rdflib.DCTERMS['identifier'],
            rdflib.Literal('https://n2t.net/ark:61001/{}'.format(cnoid))
        ))

        # collections -- edm:ProvidedCHO -- dcterms:rights
        for result in dblookup(cur, cid, 'Collection', ['CodesAccess_t']):
            if result[0].strip():
                g.add((
                    cscho,
                    rdflib.DCTERMS['rights'],
                    rdflib.Literal(result[0])
                ))
        
        # collections -- edm:ProvidedCHO -- dcterms:spatial
        spatials = set()
        for iid in collection_itemids(cur, cid):
            for vid in coverageids(cur, iid):
                for geonameid in dblookup(
                    cur, 
                    vid, 
                    'ItemCoverage', 
                    ['Coverage.GeoNameID_n']
                ):
                    for v in geonameid:
                        spatials.add(v)
        if len(spatials) == 0:
            g.add((
                cscho,
                rdflib.DCTERMS['spatial'],
                rdflib.Literal('(:unav)')
            ))
        else:
            for geonameid in spatials: 
                g.add((
                    cscho,
                    rdflib.DCTERMS['spatial'],
                    rdflib.Literal(geonameid)
                ))

        # collection -- edm:ProvidedCHO -- dcterms:type
        types = set()
        for iid in collection_itemids(cur, cid):
            for result in dblookup(cur, iid, 'Item', ['TypeItemContent_t']):
                if result[0].lower().strip() in ('performed music', 'spoken word'):
                    types.add('Sound')
                if result[0].lower().strip() in ('text',):
                    types.add('Text')
        for t in types:
            g.add((
                cscho,
                rdflib.DCTERMS['type'],
                rdflib.Literal(t)
            ))

        # collection -- edm:ProvidedCHO -- dma:contentType
        content_types = set()
        for iid in collection_itemids(cur, cid):
            for c in dblookup(
                cur,
                iid,
                'Item',
                ['TypeDMAContent_t']
            ):
                content_types.add(c[0])
        for content_type in content_types:
            g.add((
                cscho, 
                NAMESPACES['dma']['contentType'],
                rdflib.Literal(content_type)
            ))

        # collection -- edm:ProvidedCHO -- edm:type
        types = set()
        for iid in collection_itemids(cur, cid):
            for result in dblookup(cur, iid, 'Item', ['TypeItemContent_t']):
                if result[0].lower().strip() in ('performed music', 'spoken word'):
                    types.add('SOUND')
                if result[0].lower().strip() in ('text',):
                    types.add('TEXT')
        for t in types:
            g.add((
                cscho,
                NAMESPACES['edm']['type'],
                rdflib.Literal(t)
            ))

        # collection -- edm:ProvidedCHO -- icu:contributor
        contributor_roles = set()
        for iid in collection_itemids(cur, cid): 
            for name, role in dblookup( 
                cur, 
                iid,
                 'ItemContributors',
                 ['name', 'role']
            ):
                if role in ('consultant', 'participant', 'performer', 'singer', 'speaker'):
                    contributor_roles.add((name, role))
        for name, role in sorted(list(contributor_roles)):
            g.add((
                cscho,
                NAMESPACES['icu']['contributor'],
                rdflib.Literal('{}:{}'.format(name, role))
            ))

        # collection -- edm:ProvidedCHO -- icu:creator
        creator_roles = set()
        for iid in collection_itemids(cur, cid): 
            for name, role in dblookup( 
                cur, 
                iid,
                 'ItemContributors',
                 ['name', 'role']
            ):
                if role in ('author', 'compiler', 'depositor', 'editor', 'interviewer', 'recorder', 'researcher', 'translator'):
                    creator_roles.add((name, role))
        for name, role in creator_roles:
            g.add((
                cscho,
                NAMESPACES['icu']['creator'],
                rdflib.Literal('{}:{}'.format(name, role))
            ))

        # collection -- edm:ProvidedCHO -- icu:language
        code_roles = set()
        for iid in collection_itemids(cur, cid):
            for lid in itemlanguage_ids(cur, iid):
                for code, role in dblookup(
                    cur, 
                    lid, 
                    'Language', 
                    ['Language.Code_t', 'ItemLanguages.type']
                ):
                    code_roles.add((code, role))
        for code, role in code_roles:
            if role:
                g.add((
                    cscho,
                    NAMESPACES['icu']['language'],
                    rdflib.Literal('{}:{}'.format(role, code))
                ))

        # collection -- edm:ProvidedCHO -- olac:discourseType
        discourse_types = set()
        for iid in collection_itemids(cur, cid):
            for d in dblookup(cur, iid, 'Item', ['TypeDiscourse_t']):
                discourse_types.add(d[0])
        for discourse_type in discourse_types:
            g.add((
                cscho,
                NAMESPACES['olac']['discourseType'],
                rdflib.Literal(discourse_type)
            ))

        # collection -- edm:providedcho -- uchicago:contributor
        contributor_roles = set()
        for iid in collection_itemids(cur, cid): 
            for name, role in dblookup( 
                cur, 
                iid,
                 'ItemContributors',
                 ['name', 'role']
            ):
                if role in ('consultant', 'participant', 'performer', 'singer', 'speaker'):
                    contributor_roles.add((name, role))
        for name, role in sorted(list(contributor_roles)):
            b = rdflib.BNode()
            g.add((
                cscho,
                NAMESPACES['uchicago']['contributor'],
                b
            ))
            g.add((
                b,
                NAMESPACES['dcterms']['contributor'],
                rdflib.Literal(name)
            ))
            g.add((
                b,
                NAMESPACES['rel']['relator'],
                rdflib.Literal(role)
            ))

        # collection -- edm:ProvidedCHO -- uchicago:creator
        creator_roles = set()
        for iid in collection_itemids(cur, cid): 
            for name, role in dblookup( 
                cur, 
                iid,
                 'ItemContributors',
                 ['name', 'role']
            ):
                if role in ('author', 'compiler', 'depositor', 'editor', 'interviewer', 'recorder', 'researcher', 'translator'):
                    creator_roles.add((name, role))
        for name, role in creator_roles:
            b = rdflib.BNode()
            g.add((
                cscho,
                NAMESPACES['uchicago']['creator'],
                b
            ))
            g.add((
                b,
                NAMESPACES['dcterms']['creator'],
                rdflib.Literal(name)
            ))
            g.add((
                b,
                NAMESPACES['rel']['relator'],
                rdflib.Literal(role)
            ))

        # collection -- edm:providedcho -- uchicago:language
        code_roles = set()
        for iid in collection_itemids(cur, cid):
            for lid in itemlanguage_ids(cur, iid):
                for code, role in dblookup(
                    cur, 
                    lid, 
                    'Language', 
                    ['Language.Code_t', 'ItemLanguages.type']
                ):
                    code_roles.add((code, role))
        for code, role in sorted(list(code_roles)):
            # only output non-blank language types.
            if role:
                b = rdflib.BNode()
                g.add((
                    cscho,
                    NAMESPACES['uchicago']['language'],
                    b
                ))
                g.add((
                    b,
                    NAMESPACES['lexvo']['iso639P3PCode'],
                    rdflib.Literal(code)
                ))
                g.add((
                    b,
                    NAMESPACES['icu']['languageRole'],
                    rdflib.Literal(role)
                ))

        # collection -- ore:ResourceMap -- rdf:type
        g.add((
            csrem,
            rdflib.RDF['type'],
            NAMESPACES['ore']['ResourceMap']
        ))

        # collection -- ore:ResourceMap -- dcterms:creator
        g.add((
            csrem,
            rdflib.DCTERMS['creator'],
            rdflib.URIRef('https://dldc.lib.uchicago.edu/')
        ))

        now = datetime.datetime.now(
            pytz.timezone('America/Chicago')
        ).isoformat()

        # collection -- ore:ResourceMap -- dcterms:created
        g.add((
            csrem,
            rdflib.DCTERMS['created'],
            rdflib.Literal(now, datatype=rdflib.XSD.dateTime)
        ))

        # collection -- ore:ResourceMap -- dcterms:modified
        g.add((
            csrem,
            rdflib.DCTERMS['modified'],
            rdflib.Literal(now, datatype=rdflib.XSD.dateTime)
        ))

        # collection -- ore:ResourceMap -- ore:describes
        g.add((
            csrem,
            NAMESPACES['ore']['describes'],
            csagg
        ))

        for iid in collection_itemids(cur, cid):
            # commenting out handling for MLP/UCLA here, because we already 
            # checked to see if the collection itself is MLP or UCLA.
            # output = False
            # if options['--mesoamerican'] and \
            # bool(mesoamerican_language_codes & set(item_language_codes[iid])):
            #     output = True
            # if options['--ucla'] and \
            # not(bool(mesoamerican_language_codes & set(item_language_codes[iid]))):
            #     output = True
            # if not output:
            #     continue

            iark = item_id_arks[iid]
            inoid = iark.replace('ark:61001/', '')

            isagg = BASE['{}/aggregation'.format(inoid)]
            ischo = BASE['{}'.format(inoid)]
            ispro = BASE['{}/file.dc.xml'.format(inoid)]
            isrem = BASE['{}/rem'.format(inoid)]
            iswav = BASE['{}/file.wav'.format(inoid)]

            isark = rdflib.URIRef('https://n2t.net/ark:61001/{}'.format(inoid))

            # item -- ore:Aggregation -- rdf:type
            g.add((
                isagg,
                rdflib.RDF['type'],
                NAMESPACES['ore']['Aggregation']
            ))
    
            # item -- ore:Aggregation -- edm:aggregatedCHO
            g.add((
                isagg,
                NAMESPACES['edm']['aggregatedCHO'],
                ischo
            ))
    
            # item -- ore:Aggregation -- edm:dataProvider
            g.add((
                isagg,
                NAMESPACES['edm']['dataProvider'],
                rdflib.Literal('University of Chicago Library')
            ))

            # item -- ore:Aggregation -- edm:isShownAt
            g.add((
                isagg,
                NAMESPACES['edm']['isShownAt'],
                rdflib.Literal('https://n2t.net/ark:61001/{}'.format(inoid))
            ))
  
            for i_title, i_type in dblookup(cur, iid, 'ItemTitle', ['title', 'type']): 
                if i_type == 'Primary' and i_title in soundfile_data:
                    a = soundfile_data[i_title]['ark']
                    n = a.split('/')[1]

                    # item -- ore:Aggregation -- edm:isShownBy
                    g.add((
                        isagg,
                        NAMESPACES['edm']['isShownBy'],
                        BASE[n]
                    ))
        
                    # item -- ore:Aggregation -- edm:object
                    g.add((
                        isagg,
                        NAMESPACES['edm']['object'],
                        BASE[n]
                    ))

            # item -- ore:Aggregation -- edm:provider
            g.add((
                isagg,
                NAMESPACES['edm']['provider'],
                rdflib.Literal('University of Chicago Library')
            ))

            # item -- ore:Aggregation -- edm:rights
            g.add((
                isagg,
                NAMESPACES['edm']['rights'],
                rdflib.URIRef('https://rightsstatements.org/vocab/NoC-US/1.0/')
            ))

            # item -- ore:Aggregation -- fn:collection
            g.add((
                isagg,
                NAMESPACES['fn']['collection'],
                rdflib.Literal('dma')
            ))
            g.add((
                isagg,
                NAMESPACES['fn']['collection'],
                rdflib.URIRef('http://lib.uchicago.edu/mlc')
            ))
    
            # item -- ore:Aggregation -- ore:isDescribedBy
            g.add((
                isagg,
                NAMESPACES['ore']['isDescribedBy'],
                isrem
            ))

            # item -- ore:Proxy -- rdf:type
            g.add((
                ispro,
                rdflib.RDF['type'],
                NAMESPACES['ore']['Proxy']
            ))

            # item -- ore:Proxy -- dc:format
            g.add((
                ispro,
                rdflib.DC['format'],
                rdflib.Literal('application/xml')
            ))

            # item -- ore:Proxy -- ore:proxyFor
            g.add((
                ispro,
                NAMESPACES['ore']['proxyFor'],
                ischo
            ))

            # item -- ore:Proxy -- ore:proxyIn
            g.add((
                ispro,
                NAMESPACES['ore']['proxyIn'],
                isagg
            ))

            # item -- edm:ProvidedCHO -- rdf:type
            g.add((
                ischo,
                rdflib.RDF['type'],
                NAMESPACES['edm']['ProvidedCHO']
            ))

            # item -- edm:ProvidedCHO 
            for subject, predicates, table, field in filter_mappings_data(
                mappings, 
                tables = ('Containers', 'Item', 'ItemContributors',
                          'ItemFormat', 'ItemSource', 'ItemTitle',
                          'SoundFormat'),
                subjects = ('edm:ProvidedCHO')
            ):
                for o in dblookup(cur, iid, table, [field]):
                    p = [i.split(':') for i in predicates]
                    if len(predicates) == 1:
                        g.add((
                            ischo,
                            NAMESPACES[p[0][0]][p[0][1]],
                            rdflib.Literal(o[0].strip())
                        ))
                    else:
                        raise NotImplementedError

            for subject, predicates, table, field in filter_mappings_data_for_classes(
                mappings, 
                tables = ('Containers', 'Item', 'ItemContributors',
                          'ItemFormat', 'ItemSource', 'ItemTitle',
                          'SoundFormat'),
                subjects = ('edm:ProvidedCHO')
            ):
                for o in dblookup(cur, iid, table, [field]):
                    if len(predicates) == 1:
                        p0 = predicates[0][0].split(':')
                        p1 = predicates[0][1].split(':')
    
                        b = rdflib.BNode()

                        g.add((
                            ischo,
                            NAMESPACES[p0[0]][p0[1]],
                            b
                        ))
                        g.add((
                            b,
                            rdflib.RDF['type'],
                            NAMESPACES[p1[0]][p1[1]]
                        ))
                        g.add((
                            b,
                            rdflib.RDF['value'],
                            rdflib.Literal(o[0].strip())
                        ))
                    else:
                        raise NotImplementedError

            # item -- edm:ProvidedCHO -- dcterms:contributor
            contributors = set()
            for name, role in dblookup( 
                cur, 
                iid,
                 'ItemContributors',
                 ['name', 'role']
            ):
                if role in ('consultant', 'participant', 'performer', 'singer', 'speaker'):
                    contributors.add(name)
            for contributor in contributors:
                g.add((
                    ischo,
                    NAMESPACES['dcterms']['contributor'],
                    rdflib.Literal(contributor)
                ))

            # item -- edm:ProvidedCHO -- dcterms:creator
            creators = set()
            for name, role in dblookup( 
                cur, 
                iid,
                 'ItemContributors',
                 ['name', 'role']
            ):
                if role in ('author', 'compiler', 'depositor', 'editor', 'interviewer', 'recorder', 'researcher', 'translator'):
                    creators.add(name)
            for creator in creators:
                g.add((
                    ischo,
                    NAMESPACES['dcterms']['creator'],
                    rdflib.Literal(creator)
                ))

            # item -- edm:ProvidedCHO -- dcterms:date
            for start_year, end_year in dblookup(
                cur,
                iid,
                'Item',
                ['DateCreation_t', 'DateCreationRange2_t']
            ):
                dates = []
                if start_year.strip():
                    dates.append(start_year.strip())
                if end_year.strip():
                    dates.append(end_year.strip())
                dates.sort()
                if len(dates) == 0:
                    g.add((
                        ischo,
                        rdflib.DCTERMS['date'],
                        rdflib.Literal('(:unav)')
                    ))
                else:
                    g.add((
                        ischo,
                        rdflib.DCTERMS['date'],
                        rdflib.Literal('/'.join(dates))
                    ))

            # item -- edm:ProvidedCHO -- dcterms:hasFormat
            for fiid in get_has_format(cur, iid):
                fark = item_id_arks[fiid]
                fnoid = fark.replace('ark:61001/', '')
                fcho = BASE['{}'.format(fnoid)]
                g.add((
                    ischo,
                    rdflib.DCTERMS['hasFormat'],
                    fcho
                ))

            # item -- edm:ProvidedCHO -- dcterms:identifier
            g.add((
                ischo,
                rdflib.DCTERMS['identifier'],
                rdflib.Literal('https://n2t.net/ark:61001/{}'.format(inoid))
            ))

            # item -- edm:ProvidedCHO -- dcterms:isFormatOf
            for foiid in get_is_format_of(cur, iid):
                foark = item_id_arks[foiid]
                fonoid = foark.replace('ark:61001/', '')
                focho = BASE['{}'.format(fonoid)]
                g.add((
                    ischo,
                    rdflib.DCTERMS['isFormatOf'],
                    focho
                ))

            # item -- edm:ProvidedCHO -- dcterms:isPartOf
            g.add((
                ischo,
                rdflib.DCTERMS['isPartOf'],
                cscho
            ))

            # item -- edm:ProvidedCHO -- dc:language
            # item -- edm:ProvidedCHO -- dcterms:language
            code_types = set()
            for lid in itemlanguage_ids(cur, iid):
                for code_t in dblookup(
                    cur, 
                    lid, 
                    'Language', 
                    ['Language.Code_t']
                ):
                    code_types.add(code_t[0])
            for code_t in code_types:
                g.add((
                    ischo,
                    NAMESPACES['dc']['language'],
                    rdflib.Literal(code_t)
                ))
                g.add((
                    ischo,
                    NAMESPACES['dcterms']['language'],
                    rdflib.Literal(code_t)
                ))

            # item -- edm:ProvidedCHO -- dcterms:medium
            mediums = set()
            for row in dblookup(
                cur,
                iid,
                'Item',
                ['Medium_t']
            ):
                if row[0] != 'None': 
                    mediums.add(row[0].strip())
            if mediums:
                for medium in mediums:
                    g.add((
                        ischo,
                        rdflib.DCTERMS['medium'],
                        rdflib.Literal(medium)
                    ))
            else:
                g.add((
                    ischo,
                    rdflib.DCTERMS['medium'],
                    rdflib.Literal('(:unav)')
                ))

            # item -- edm:ProvidedCHO -- dcterms:spatial
            spatials = set()
            for vid in coverageids(cur, iid):
                for geonameid in dblookup(
                    cur, 
                    vid, 
                    'ItemCoverage', 
                    ['Coverage.GeoNameID_n']
                ):
                    for v in geonameid:
                        spatials.add(v)
            if len(spatials) == 0:
                g.add((
                    ischo,
                    rdflib.DCTERMS['spatial'],
                    rdflib.Literal('(:unav)')
                ))
            else:
                for geonameid in spatials: 
                    g.add((
                        ischo,
                        rdflib.DCTERMS['spatial'],
                        rdflib.Literal(geonameid)
                    ))

            # item -- edm:ProvidedCHO -- dcterms:type
            types = set()
            for result in dblookup(cur, iid, 'Item', ['TypeItemContent_t']):
                if result[0].lower().strip() in ('performed music', 'spoken word'):
                    types.add('Sound')
                if result[0].lower().strip() in ('text',):
                    types.add('Text')
            for t in types:
                g.add((
                    ischo,
                    rdflib.DCTERMS['type'],
                    rdflib.Literal(t)
                ))

            # item -- edm:ProvidedCHO -- edm:type
            types = set()
            for result in dblookup(cur, iid, 'Item', ['TypeItemContent_t']):
                if result[0].lower().strip() in ('performed music', 'spoken word'):
                    types.add('SOUND')
                if result[0].lower().strip() in ('text',):
                    types.add('TEXT')
            for t in types:
                g.add((
                    ischo,
                    NAMESPACES['edm']['type'],
                    rdflib.Literal(t)
                ))

            # item -- edm:ProvidedCHO -- icu:contributor
            for name, role in dblookup( 
                cur, 
                iid,
                'ItemContributors',
                ['name', 'role']
            ):
                if role in ('consultant', 'participant', 'performer', 'singer', 'speaker'):
                    g.add((
                        ischo,
                        NAMESPACES['icu']['contributor'],
                        rdflib.Literal('{}:{}'.format(name, role))
                    ))

            # item -- edm:ProvidedCHO -- icu:creator
            for name, role in dblookup( 
                cur, 
                iid,
                 'ItemContributors',
                 ['name', 'role']
            ):
                if role in ('author', 'compiler', 'depositor', 'editor', 'interviewer', 'recorder', 'researcher', 'translator'):
                    g.add((
                        ischo,
                        NAMESPACES['icu']['creator'],
                        rdflib.Literal('{}:{}'.format(name, role))
                    ))

            # item -- edm:ProvidedCHO -- icu:language
            code_types = set()
            for lid in itemlanguage_ids(cur, iid):
                for code, role in dblookup(
                    cur, 
                    lid, 
                    'Language', 
                    ['Language.Code_t', 'ItemLanguages.type']
                ):
                    code_types.add((code, role))
            for code, role in code_types:
                # only output non-blank language roles
                if role:
                    g.add((
                        ischo,
                        NAMESPACES['icu']['language'],
                        rdflib.Literal('{}:{}'.format(role, code))
                    ))

            # item -- edm:ProvidedCHO -- uchicago:contributor
            for name, role in dblookup( 
                cur, 
                iid,
                 'ItemContributors',
                 ['name', 'role']
            ):
                if role in ('consultant', 'participant', 'performer', 'singer', 'speaker'):
                    b = rdflib.BNode()
                    g.add((
                        ischo,
                        NAMESPACES['uchicago']['contributor'],
                        b
                    ))
                    g.add((
                        b,
                        NAMESPACES['dcterms']['contributor'],
                        rdflib.Literal(name)
                    ))
                    g.add((
                        b,
                        NAMESPACES['rel']['relator'],
                        rdflib.Literal(role)
                    ))

            # item -- edm:ProvidedCHO -- uchicago:creator
            for name, role in dblookup( 
                cur, 
                iid,
                 'ItemContributors',
                 ['name', 'role']
            ):
                if role in ('author', 'compiler', 'depositor', 'editor', 'interviewer', 'recorder', 'researcher', 'translator'):
                    b = rdflib.BNode()
                    g.add((
                        ischo,
                        NAMESPACES['uchicago']['creator'],
                        b
                    ))
                    g.add((
                        b,
                        NAMESPACES['dcterms']['creator'],
                        rdflib.Literal(name)
                    ))
                    g.add((
                        b,
                        NAMESPACES['rel']['relator'],
                        rdflib.Literal(role)
                    ))

            # item -- edm:ProvidedCHO -- uchicago:language
            code_roles = set()
            for lid in itemlanguage_ids(cur, iid):
                for code, role in dblookup(
                    cur, 
                    lid, 
                    'Language', 
                    ['Language.Code_t', 'ItemLanguages.type']
                ):
                    code_roles.add((code, role))
            for code, role in code_roles:
                b = rdflib.BNode()
                g.add((
                    ischo,
                    NAMESPACES['uchicago']['language'],
                    b
                ))
                g.add((
                    b,
                    NAMESPACES['icu']['languageRole'],
                    rdflib.Literal(role)
                ))
                g.add((
                    b,
                    NAMESPACES['lexvo']['iso639P3PCode'],
                    rdflib.Literal(code)
                ))

            # JEJ
            # we have a name like "tzh-amat-57-58-7". 
            # this will be in item data, in dma:title/dma:itemTitle.

            # item -- edm:WebResource

            wav_basename = ''

            for i_title, i_type in dblookup(cur, iid, 'ItemTitle', ['title', 'type']): 
                if i_type == 'Primary' and i_title in soundfile_data:
                    wav_basename = i_title

            if wav_basename:

                # item -- edm:WebResource -- rdf:type
                try:
                    g.add((
                        iswav,
                        rdflib.RDF['type'],
                        NAMESPACES['edm']['WebResource']
                    ))
                except KeyError:
                    pass
  
                # item -- edm:WebResource -- dcterms:format
                try:
                    g.add((
                        iswav,
                        rdflib.DCTERMS['format'],
                        rdflib.Literal('audio/x-wav')
                    ))
                except KeyError:
                    pass

                # item -- edm:WebResource -- dcterms:identifier
                g.add((
                    iswav,
                    rdflib.DCTERMS['identifier'],
                    rdflib.Literal('https://n2t.net/ark:61001/{}/file.wav'.format(inoid))
                ))

                if wav_basename in filenames_to_identifiers:
                    g.add((
                        iswav,
                        rdflib.DCTERMS['identifier'],
                        rdflib.Literal('https://uchicago.hosted.panopto.com/Panopto/Pages/Embed.aspx?id={}'.format(filenames_to_identifiers[wav_basename]))
                    ))

                # item -- edm:WebResource -- premis:fixity
                b = rdflib.BNode()
                g.add((
                    iswav,
                    NAMESPACES['premis']['fixity'],
                    b
                ))
                g.add((
                    b,
                    rdflib.RDF['type'],
                    rdflib.URIRef('https://id.loc.gov/vocabulary/preservation/cryptographicHashFunctions/sha512')
                ))
                g.add((
                    b,
                    rdflib.RDF['value'],
                    rdflib.Literal(soundfile_data[wav_basename]['sha512'])
                ))

                # item -- edm:WebResource -- premis:originalName
                g.add((
                    iswav,
                    NAMESPACES['premis']['originalName'],
                    rdflib.Literal(soundfile_data[wav_basename]['name'])
                ))

                # item -- edm:WebResource -- premis:size
                g.add((
                    iswav,
                    NAMESPACES['premis']['size'],
                    rdflib.Literal(soundfile_data[wav_basename]['size'])
                ))

            # item -- ore:ResourceMap -- rdf:type
            g.add((
                isrem,
                rdflib.RDF['type'],
                NAMESPACES['ore']['ResourceMap']
            ))
    
            # item -- ore:ResourceMap -- dcterms:creator
            g.add((
                isrem,
                rdflib.DCTERMS['creator'],
                rdflib.URIRef('https://dldc.lib.uchicago.edu/')
            ))
    
            now = datetime.datetime.now(
                pytz.timezone('America/Chicago')
            ).isoformat()
    
            # item -- ore:ResourceMap -- dcterms:created
            g.add((
                isrem,
                rdflib.DCTERMS['created'],
                rdflib.Literal(now, datatype=rdflib.XSD.dateTime)
            ))
    
            # item -- ore:ResourceMap -- dcterms:modified
            g.add((
                isrem,
                rdflib.DCTERMS['modified'],
                rdflib.Literal(now, datatype=rdflib.XSD.dateTime)
            ))
    
            # item -- ore:ResourceMap -- ore:describes
            g.add((
                isrem,
                NAMESPACES['ore']['describes'],
                isagg
            ))

    # THIRD PASS
    # Required Elements:
    # see https://dldc.lib.uchicago.edu/local/ldr/template.pdf

    # dma:coverage -> dcterms:spatial is required. if it's not there, do (:unav) 
    # should I descend into blank nodes? That seems overly complicated, and not ideal, since blank nodes
    # aren't recommended. 

    # dcterms:created is start year.
    # dma:endDate is end year. If these elements are compatible with ISO8601,
    # output them as a new dcterms:temporal element. see https://github.com/uchicago-library/ucla/issues/49
    # for additional implementation details.

    print(g.serialize(format='turtle', base=BASE))

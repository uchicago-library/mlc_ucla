#!/usr/bin/env python
"""Usage:
    sqlite_to_triples.update_language_codes.py 
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

def item_contains_language_codes(cur, iid, codes):
    """Check to see if an item contains a language code from a larger set
       of language codes. Use this function to find records for MLP or UCLA.

       Args:
           cur - an SQLite3 cursor.
           cid - collection identifier.
           codes - a set of collection codes.

       Returns:
           True or False
    """
    parent_and_self_iids = set([iid] + get_item_sources(cur, iid))

    item_codes = set()
    for i in parent_and_self_iids:
        for lid in itemlanguage_ids(cur, i):
            for r in dblookup(
                cur, 
                lid, 
                'Language', 
                ['Language.Code_t']
            ):
                for code_t in r:
                    item_codes.add(code_t)
    return bool(codes & item_codes)

def collection_contains_language_code(cur, cid, codes):
    """Check to see if a collection contains a language code from a larger set
       of language codes. Use this function to find records for MLP or UCLA.

       Args:
           cur - an SQLite3 cursor.
           cid - collection identifier.
           codes - a set of collection codes.

       Returns:
           True or False
    """
    for iid in collection_itemids(cur, cid):
        if item_contains_language_codes(cur, iid, codes):
            return True
    return False

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

    sql = 'SELECT DISTINCT __kp_CollectionID FROM Collection;'
    cur.execute(sql)
    for r in cur.fetchall():
        if r[0] != 'None':
            assert r[0].isnumeric()
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

def get_item_sources(cur, iid):
    """With a (digital) child in hand, get the (analog) parent.
 
       Args:
           cur - an SQLite3 cursor.
           iid - a string, the ItemID.

       Returns:
           a list of strings.
    """
    item_sources = set()
    sql = '''SELECT __kf_ItemID_Source 
             FROM   ItemSource 
             WHERE   __kf_ItemID = ? 
             AND     relationship = 'Is Format Of';'''
    cur.execute(sql, (iid,))
    for r in cur.fetchall():
        item_sources.add(r[0])
    return sorted(list(item_sources))

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
    con = sqlite3.connect('ucla.db')
    cur = con.cursor()

    collection_code_dict = {}
    item_code_dict = {}

    c = 0
    for cid in get_collections(cur):
        collection_codes = set()
        for iid in collection_itemids(cur, cid):
            print(c)
            c = c + 1
            item_codes = set()
            for lid in itemlanguage_ids(cur, iid):
                for r in dblookup(
                    cur, 
                    lid, 
                    'Language', 
                    ['Language.Code_t']
                ):
                    for code_t in r:
                        item_codes.add(code_t)
            item_code_dict[iid] = list(item_codes)
            collection_codes.update(item_codes)
        collection_code_dict[cid] = list(collection_codes)
    with open('sqlite_to_triples.collection_language_codes.json', 'w') as f:
        f.write(json.dumps(collection_code_dict))
    with open('sqlite_to_triples.item_language_codes.json', 'w') as f:
        f.write(json.dumps(item_code_dict))

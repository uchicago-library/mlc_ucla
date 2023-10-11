#!/usr/bin/env python
"""Usage:
    list_missing_arks.py
"""

import csv, json, openpyxl, os, re, sqlite3, sys
from docopt import docopt

EXPORT_DIR = '../export.2023.10'

def get_ws_data(ws, header):
    col = 1
    for c in range(1, ws.max_column + 1):
        if ws.cell(column=c, row=1).value == header:
            col = c

    data = []
    for r in range(2, ws.max_row + 1):
        v = ws.cell(column=col, row=r).value
        if v:
            data.append(str(v))
    return data

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
    """Get a list of all of the ItemIDs in the system. Because some tables
       contain ItemIDs that are not present in the Item table, we collect
       ItemIDs from wherever they occur.

       Args:
           cur - an SQLite3 cursor.

       Returns:
           a list of strings.
    """
    results = set()

    for table, fields in {
        'CollectionItems':  ['__kp_ItemID'],
        'Containers':       ['__kf_ItemID'],
        'Event':            ['__kf_ItemID'],
        'Item':             ['__kp_ItemID'],
        'ItemContributors': ['__kp_ItemID'],
        'ItemCoverage':     ['__kf_ItemID'],
        'ItemFormat':       ['__kf_ItemID'],
        'ItemLanguages':    ['__kp_ItemID'],
        'ItemSource':       ['__kf_ItemID', '__kf_ItemID_Source'],
        'ItemTitle':        ['__kp_ItemID'],
        'MaterialData':     ['__kf_ItemID']
    }.items():
        for field in fields:
            sql = 'SELECT DISTINCT {0} FROM {1};'.format(field, table)
            try:
                cur.execute(sql)
            except sqlite3.OperationalError:
                print('error trying to check ' + table + '.' + field)
                sys.exit()
            for r in cur.fetchall():
                if r[0] != 'None':
                    assert r[0].isnumeric()
                    results.add(int(r[0]))
    # sort as integers.
    results = sorted(results)
    # return strings.
    return [str(r) for r in results]


if __name__ == '__main__':
    coll_ids_ws = set(
        get_ws_data(
            openpyxl.load_workbook(
                os.path.join(
                    EXPORT_DIR,
                    'ac_cr_CL_Collection.xlsx'
                )
            ).active,
            '__kp_CollectionID'
        )
    )
    item_ids_ws = set(
        get_ws_data(
            openpyxl.load_workbook(
                os.path.join(
                    EXPORT_DIR,
                    'Item.xlsx'
                )
            ).active,
            '__kp_ItemID'
        )
    )


with open('sqlite_to_triples.collection_id_arks.json') as f:
    coll_id_arks = json.load(f)

with open('sqlite_to_triples.item_id_arks.json') as f:
    item_id_arks = json.load(f)

    missing = {
        'http://lib.uchicago.edu/digital_collections/dma/collectionids': {
            '': []
        },
        'http://lib.uchicago.edu/digital_collections/dma/itemids': {
            '': []
        }
    }    

    d = coll_ids_ws - set(coll_id_arks.keys())
    for i in sorted(list(d)):
        missing['http://lib.uchicago.edu/digital_collections/dma/collectionids'][''].append(i)

    d = item_ids_ws - set(item_id_arks.keys())
    for i in sorted(list(d)):
        missing['http://lib.uchicago.edu/digital_collections/dma/itemids'][''].append(i)

    print(json.dumps(missing, indent=2))

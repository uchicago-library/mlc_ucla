#!/usr/bin/env python
"""Usage:
    check_SQLITE_export.py <db_a> <db_b>
"""

import os, sqlite3, sys
from docopt import docopt

def get_db_cur(db):
    con = sqlite3. connect(db)
    return con.cursor()

def get_db_tables(cur):
    cur.execute("SELECT name FROM sqlite_master WHERE type='table';")
    return sorted([r[0] for r in cur.fetchall()])

def get_db_table_fields(cur, table):
    cur.execute("SELECT * FROM {};".format(table))
    return list(map(lambda x: x[0], cur.description))

if __name__ == '__main__':
    """Check to see that a new SQLITE database looks correct by comparing it
       to an old one. Be sure the number and names of tables matches, and 
       be sure the fields in each table are the same. Although I expect the
       number of rows in each datafile to change frequently, and the number of
       headers to change infreqently, and the tables themselves to not change
       very often, this script should help keep the process of re-exporting
       data under control."""

    options = docopt(__doc__)

    cur_a = get_db_cur(options['<db_a>'])
    cur_b = get_db_cur(options['<db_b>'])

    tables_a = get_db_tables(cur_a)
    tables_b = get_db_tables(cur_b)

    if tables_a != tables_b:
        print(tables_a)
        print(tables_b)

    for table in tables_a:
        fields_a = get_db_table_fields(cur_a, table)
        fields_b = get_db_table_fields(cur_b, table)
        if fields_a != fields_b:
            print('table mismatch in {}'.format(table))
            print(fields_a)
            print(fields_b)
            print('')

import sqlite3, sys

'''List UCLA(OLA) database tables and fields. -v for verbose output.'''

if __name__ == '__main__':
    con = sqlite3.connect('ucla.db')
    cur = con.cursor()

    # get a list of table names.
    cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = sorted([r[0] for r in cur.fetchall()])

    # each key in fields is a table name- each value is a list of field names.
    fields = {}
    for table in tables:
        cur.execute("SELECT * FROM {}".format(table))
        fields[table] = sorted(list(map(lambda x: x[0], cur.description)))

    # maximum string length of table names.
    max_table_strlen = max([len(t) for t in tables])

    # maximums string length of field names.
    max_field_strlen = max([len(v) for vs in fields.values() for v in vs])

    for table in sorted(tables):
        if '-v' in sys.argv:
            cur.execute("SELECT count(*) FROM {};".format(table))
            count = cur.fetchall()[0][0]
            print('{} {} ({})'.format(table.ljust(max_table_strlen), ''.ljust(max_field_strlen), count))
            print('{}'.format('=' * (max_table_strlen + 1 + max_field_strlen + 8)))
            for f in sorted(fields[table]):
                cur.execute("SELECT count(\"0\") FROM {1} WHERE \"{0}\" != 'None';".format(f, table))
                count = cur.fetchall()[0][0]
                print('{} {} ({})'.format(''.ljust(max_table_strlen), f.ljust(max_field_strlen), count))
            print('')
        else:
            print(table)
            print('=' * len(table))
            print('\n'.join(sorted(fields[table])))
            print('')

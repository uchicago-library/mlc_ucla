import sqlite3, sys

# Look for specific values anywhere in the database.

def get_tables(cur):
    """List all tables in the database."""
    cur.execute("SELECT name FROM sqlite_schema WHERE type='table' ORDER BY name;")
    results = []
    for r in cur.fetchall():
        results.append(r[0])
    return results

def get_fields(cur, table):
    """List fields for a particular table."""
    cur.execute("PRAGMA table_info({})".format(table))
    results = []
    for r in cur.fetchall():
        results.append(r[1])
    return results

def table_field_value_exists(cur, table, field, value):
    """Check to see if a particular value appears in a table and field."""
    return bool(
        len(
            cur.execute(
                'SELECT "{}" FROM "{}" WHERE "{}"="{}";'.format(
                    field, 
                    table, 
                    field, 
                    value
                )
            ).fetchall()
        )
    )
    
if __name__ == '__main__':
    con = sqlite3.connect('ucla.db')
    cur = con.cursor()

    if len(sys.argv) < 2:
        print('usage: python {} value'.format(sys.argv[0]))
        sys.exit()
    else:
        value = sys.argv[1]

    for table in get_tables(cur):
        for field in get_fields(cur, table):
            if table_field_value_exists(cur, table, field, value):
                print(table)
                print(field)
                print('')

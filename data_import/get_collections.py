#!/usr/bin/env python
"""Usage:   
    get_items.py <DATABASE>
""" 

import sqlite3

from docopt import docopt
from sqlite_to_triples import get_collections

if __name__ == '__main__':
    options = docopt(__doc__)

    con = sqlite3.connect(options['<DATABASE>'])
    cur = con.cursor()
    for c in get_collections(cur):
        print(c)

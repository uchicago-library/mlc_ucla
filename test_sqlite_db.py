import sqlite3, sys

if __name__ == '__main__':
    con = sqlite3.connect(':memory:')
    cur = con.cursor()
    cur.executescript(sys.stdin.read())

 
# tests:
# does it return multiple language names?
# can it handle searches without accents?
# can it handle searches with accents? 
# can it return multiple place names? 
# how fast is it? 

# mlc

## Running this site locally

Set up a Python virtual environment:

```console
python3 -m venv venv
```

Activate the virtual environment:

```console
source venv/bin/activate
```

Clone this repo:
```console
git clone https://github.com/uchicago-library/mlc
```

Change into the repo directory:
```console
cd mlc
```

Install python modules:
```console
pip install --upgrade pip
pip install -r requirements.txt
```

Get a copy of local.py from another developer or from one of the production
servers and place it in the mlc directory. Get a copy of either meso.db or 
ucla.db from one of the production servers and update the path to the file
in local.py. Get glottolog_lookup.json, glottolog_language.ttl, tgn.ttl, and
the project triples (meso.big.yyyymmdd.ttl or ucla.big.yyyymmdd.ttl) from
one of the production servers, and update the locations of those files in 
local.py too. 

Set an environmental variable for the FLASK_APP:
```console
export FLASK_APP=mlc
```

Or
```console
export FLASK_APP=ucla
```

Start a development server on localhost:5000:
```console
flask run
```

Alternatively, once you get a copy of local.py, you can run the site locally
with mod_wsgi with Docker:
```console
docker build -t <imagename> .
docker run -p 8080:80 -it <imagename>
```

# Building the Website Database
The website uses an SQLite database for full text search and browse. To build the database:

```console
flask build-db
```

Note that when you run this command, you'll get a large number of ISO8601Errors- this is because 
of dirty data in our triples, you can ignore these. 

## Translating
- Strings can be labelled in templates with 
	`{% trans %}string to be translated{% endtrans %}`
	or in the code with	`gettet(u'string to be translated')` 
	or	`lazy_gettet(u'string to be translated')` if outside a request
- Two identical strings will be labeled together for translation.
- Strings can be injected into all templates through `@app.context_processor`. There is a `dict()` that is already being injected.
- The doc for the translation package is [Flask Babel](https://python-babel.github.io/flask-babel/)
- sheet being used for translation https://docs.google.com/spreadsheets/d/18m-8sN6Gqu6HFgZNIp1QST-3hy_ul_sm3QQCr_z4W6k/edit?usp=sharing
- [po2csv](https://docs.translatehouse.org/projects/translate-toolkit/en/latest/commands/csv2po.html) is being used to convert the output `.po` files to `.csv` for easily translation. That's why the `translation-toolkit` required package.
- The current strings were translated using `=GOOGLETRANSLATE()`function from the Google Sheet.

extract all strings
`pybabel extract -F babel.cfg -k lazy_gettext -o messages.pot .`

create the first translation or update the translation
`pybabel init -i messages.pot -d translations -l es`
`pybabel update -i messages.pot -d translations`

convert file to CSV
`po2csv .\translations\es\LC_MESSAGES\messages.po .\translations-csv\messages-to-translate.csv`

translate csv file into new file named `messages-translated.csv` in the same location

convert csv back to po 
`csv2po .\translations-csv\messages-translated.csv .\translations\es\LC_MESSAGES\messages.po`

compile the translations
`pybabel compile -d translations`

## Converting FileMaker to Linked Data

Getting data from FileMaker to the triplestore is a multi-step process. First, export the FileMaker database as a sequence of XLSX files. Then import those XLSX files into a local SQLite database, and finally produce triples from that SQLite database. 

You need to use FileMaker 18 to work with this database. Do not upgrade to FileMaker 19. 

Scripts for importing data are in the data_import directory.

### Exporting the FileMaker database as a sequence of XLSX files

1. Save the exported database in a local_db directory. I rename each database
   to include a datestamp, like LA_ACS.yyyymm.fmp12.
2. Create a new export directory using the following format:
   export.&lt;yyyy&gt;.&lt;mm&gt; where yyyy and mm are the current year and month.
3. Open the database. The encryption password and password for the user "Admin"
   are the same- after you have entered the encryption password be sure to 
   log in as the "Admin" user.
4. import.py contains a dictionary of filenames/layouts and database tables. For each:
    1. Go to the "Items" layout in FileMaker.
    2. Go to File > Manage > Layouts.
    3. Click "New", "Layout/Report" in the lower left corner. 
    4. Under "Show records from" select the basename of the filename from
       import.py.
    5. Under "Layout Name" enter export_&lt;basename&gt;. 
    6. Below, select "Computer" and "Table". 
    7. Click "Finish". 
    8. Under "Add Fields", select all fields. 
    9. Click "OK". 
    10. Go to the "Items" layout.
    11. Select the new layout, "export_&lt;basename&gt;". 
    12. Go to File > Export Records. 
    13. Under "Save As" enter "&lt;basename&gt;.xlsx". 
    14. Save the table export in your export.&lt;yyyy&gt;.&lt;mm&gt; directory.
    15. Under "Type" select "Excel Workbooks (.xlsx)". 
    16. Be sure the "Use field names as column names in first row" boolean is
       checked. It's ok to leave all other fields blank. Click "Continue..."
    17. Under "Specify Field Order for Export", click "Move All". Click "Export".
       Repeat for each file. 
5. Run python check_FM_to_XLSX_export.py to check the export directory.
   This script will check to be sure that files are named correctly, and it
   will report back on differences between the number of rows and columns in
   the exported data. It's normal for the number of rows in export data to
   differ when the data is being edited.

### Importing data from XLSX to SQLite
Run import.py to import the XLSX outputs from FileMaker into SQLite tables.

### Check the import
Run check_import.py. 

### Build triples
Run the following commands to export SQLite data as triples:
time python sqlite_to_triples.py --mesoamerican | python kernel_metadata.py > mlp.big.yyyymmdd.ttl
time python sqlite_to_triples.py --ucla | python kernel_metadata.py > ucla.big.yyyymmdd.ttl
(as of February 2023, the ucla export takes longer, and runs in about 5.6 hours.)

### find_value_in_database.py

Find which database tables and fields contain a particular value. This command can be handy if you see a value in the FileMaker GUI and you're not exactly sure where it's being stored in the underlying database. 

### Diagram relationships in the data
Look at diagram_has_part_relationships.py for an example of how to do this. 

### noid_to_panopto_mapping.py

Create a NOID to Panopto mapping, for the ARK resolver.

### tables.py

List tables and fields in the SQLite database. Use -v for verbose output.


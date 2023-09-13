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
servers and place it in the mlc directory.

Build an SQlite data dump from triples:
```console
flask build-db
```

Start a development server on localhost:5000:
```console
flask run
```

## Debugging

The flask command has been extended with a few custom subcommands to
browse data from the command line.

Get a list of item identifiers in the system:
```console
flask list-items
flask list-items --verbose
```

Get a list of series identifiers in the system:
```console
flask list-series
flask list-series --verbose
```

Get information about a particular item:
```console
flask get-item flask get-item https://ark.lib.uchicago.edu/ark:61001/b2zz8gz9rf5z
```

Get information about a particular series:
```console
flask get-series https://ark.lib.uchicago.edu/ark:61001/b2zn98n7s774
```

Test some cluster browses:
```console
flask get-browse contributor
flask get-browse creator
flask get-browse date
flask get-browse decade
flask get-browse language
flask get-browse location
```
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
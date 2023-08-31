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
```cosole
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

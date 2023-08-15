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
pip install -r requirements.txt
```

Get a copy of local.py from another developer or from one of the production
servers and place it in the mlc directory.

Start a development server on localhost:5000:
```console
flask run
```

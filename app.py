import click
import json
import logging
import os
import re
import sqlite3
import sqlite_dump
import sys
from flask import abort, Flask, render_template, request, session, redirect
from flask_session import Session
from utils import GlottologLookup, MLCDB
from flask_babel import Babel, gettext, lazy_gettext, get_locale
from mlc_ucla_search import mlc_ucla_search

app = Flask(__name__, template_folder='templates/mlc')
app.config.from_pyfile('local.py')
app.register_blueprint(mlc_ucla_search)

Session(app)

BASE = 'https://ark.lib.uchicago.edu/ark:61001/'


# Language switching

def get_locale():
    """Language switching."""
    if 'language' not in session:
        session['language'] = 'en'
    return session.get('language')


babel = Babel(app, default_locale='en', locale_selector=get_locale)


@app.context_processor
def inject_dict():
    cnetid = None
    if request.environ:
        if 'REMOTE_USER' in request.environ: 
            cnetid = request.environ["REMOTE_USER"]
    return {
        'cnet_id' : cnetid,
        'cgimail' : {
            'default' : {
                'from' : 'Vitor G <vitorg@uchicago.edu>'
            },
            'request_access': {
                'rcpt': 'askscrc',
                'subject': '[TEST] Request for access to MLC restricted series',
            },
            'request_account': {
                'rcpt': 'askscrc',
                'subject': '[TEST] Request for MLC account',
            }, 
            'feedback': {
                'rcpt': 'vitor',
                'subject': '[TEST] Feedback about Mesoamerican Language Collection Portal',
            }, 
        },
        'locale': get_locale(),
        'trans': {
            'collection_title': lazy_gettext(
                'Mesoamerican Language Collections'
            )
        }
    }


if __name__ == '__main__':
    app.run(host='0.0.0.0')

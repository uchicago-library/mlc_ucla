from flask import Flask, request, session
from flask_babel import Babel, lazy_gettext
from flask_session import Session
from utils import GlottologLookup, MLCDB
from mlc_ucla_search import get_locale, mlc_ucla_search


BASE = 'https://ark.lib.uchicago.edu/ark:61001/'

app = Flask(__name__, template_folder='templates/mlc')
app.config.from_pyfile('local.py')
app.register_blueprint(mlc_ucla_search)

Session(app)

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
            ),
            'collection_title_banner': lazy_gettext(
                'Indigenous Mesoamerican Languages Portal'
            )
        }
    }


if __name__ == '__main__':
    app.run(host='0.0.0.0')

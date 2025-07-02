from flask import Flask, request, session
from flask_babel import Babel, lazy_gettext
from flask_session import Session
from utils import GlottologLookup, MLCDB
from mlc_ucla_search import get_locale, mlc_ucla_search, turnstile


BASE = 'https://ark.lib.uchicago.edu/ark:61001/'

app = Flask(__name__, template_folder='templates/mlc')
app.config.from_pyfile('local.py')
app.register_blueprint(mlc_ucla_search)

turnstile.init_app(app)

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
        'locale': get_locale(),
        'trans': {
            'collection_title': lazy_gettext(
                'Mesoamerican Languages Collection'
            ),
            'collection_title_banner': lazy_gettext(
                'Mesoamerican Languages Collection'
            )
        }
    }


if __name__ == '__main__':
    app.run(host='0.0.0.0')

from flask import Flask, request, session
from flask_babel import Babel, lazy_gettext
from flask_session import Session
from mlc_ucla_search import get_locale, mlc_ucla_search


BASE = 'https://ark.lib.uchicago.edu/ark:61001/'

app = Flask(__name__, template_folder='templates/ucla')
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
        'locale': get_locale(),
        'trans': {
            'collection_title': lazy_gettext(
                'University of Chicago Language Archive'
            ),
            'collection_title_banner': lazy_gettext(
                'University of Chicago Language Archive'
            )
        }
    }


if __name__ == '__main__':
    app.run(host='0.0.0.0')

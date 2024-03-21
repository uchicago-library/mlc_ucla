from flask import Flask, request, session, render_template
from flask_babel import Babel, lazy_gettext
from flask_session import Session
from utils import GlottologLookup, MLCDB
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
                'Online Language Archive'
            ),
            'collection_title_banner': lazy_gettext(
                'Online Language Archive'
            )
        }
    }


if __name__ == '__main__':
    app.run(host='0.0.0.0')


@app.route('/history')
def history():
    return render_template(
        'static-history.html',
        title_slug = lazy_gettext(u'History'),
    )
@app.route('/contribute-material')
def contribute_material():
    return render_template(
        'form-contribute-material.html',
        title_slug = lazy_gettext(u'Contribute your Material'),
    )
@app.route('/about-contributors')
def about_contributors():
    return render_template(
        'static-about-contributors.html',
        title_slug = lazy_gettext(u'About the Contributors'),
    )
@app.route('/aquisitions-guidelines')
def aquisitions_guidelines():
    return render_template(
        'static-aquisitions-guidelines.html',
        title_slug = lazy_gettext(u'Aquisitions Guidelines'),
    )
@app.route('/aquisitions-policy')
def aquisitions_policy():
    return render_template(
        'static-aquisitions-policy.html',
        title_slug = lazy_gettext(u'Aquisitions Policy'),
    )

@app.route('/access-terms')
def access_terms_ucla():
    return render_template(
        'static-access-terms.html',
        title_slug = lazy_gettext(u'Access Terms'),
    )
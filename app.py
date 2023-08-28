import io, json, logging, os, re, rdflib, requests, sys, urllib
from flask import abort, Flask, jsonify, render_template, request
from lxml import etree as etree

app = Flask(__name__)
app.config.from_pyfile('local.py')

app.logger.setLevel(logging.DEBUG)

MARKLOGIC_SERVER=app.config['MARKLOGIC_SERVER']
PROXY_SERVER=app.config['PROXY_SERVER']

if __name__ == '__main__':
    app.run(host='0.0.0.0')

class SetEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, set):
            return list(obj)
        return json.JSONEncoder.default(self, obj)

def glotto_labels(code):
    #with open('glotto.json') as f:
    with open(app.config['GLOTTO_JSON']) as f:
        lookup = json.load(f)
    try:
        return lookup[code]
    except KeyError:
        return ''


@app.errorhandler(400)
def bad_request(e):
    return (render_template('400.html'), 400)

@app.errorhandler(404)
def not_found(e):
    return (render_template('404.html'), 404)

@app.errorhandler(500)
def bad_request(e):
    return (render_template('500.html'), 500)

@app.route('/')
def home():
    return render_template(
        'home.html'
    )

# =============================== hard routing by Vitor
@app.route('/item-vmg/') # Normal route givess 400
def item_vmg():
    return render_template(
        'item.html'
    )
@app.route('/browse-vmg/') # Normal route givess 400
def browse_vmg():
    return render_template(
        'browse.html'
    )
@app.route('/browse-kathy/') # To compare with Kathy's Mock
def browse_kathy():
    return render_template(
        'browse-kathy.html'
    )
# =============================== END hard routing by Vitor

@app.route('/browse/')
def browse():
    browses = {
        'contributor': '/getBrowseListContributors',
        'date':        '/getBrowseListDates',
        'language':    '/getBrowseListLanguages',
        'location':    '/getBrowseListLocations'
    }

    title_slugs = {
        'contributor': 'Browse by Contributors',
        'date':        'Browse by Date',
        'language':    'Browse by Language',
        'location':    'Browse by Location'
    }

    browse_type = request.args.get('type')
    if not browse_type in browses.keys():
        app.logger.debug(
            'in {}(), type parameter not a key in browses dict.'.format(
                sys._getframe().f_code.co_name
            )
        )
        abort(400)

    response = requests.get(
        '{}{}?group=dma&collection=mlc'.format(
            app.config['COLLECTIONS_ENDPOINT_PREFIX'],
            browses[browse_type]
        )
    )
    assert response.status_code == 200

    browse_data = json.loads(response.content.decode('utf-8'))

    assert 'ok' in browse_data

    if browse_type in ('contributor', 'date'):
        browse_terms = [(i, i) for i in browse_data['ok']]
    elif browse_type in ('language', 'location'):
        browse_terms = []
        for k in browse_data['ok'].keys():
            try:
                label = browse_data['ok'][k]['en']
            except KeyError:
                label = k
            browse_terms.append((k, label))
        browse_terms.sort(key=lambda i: i[1])

    return render_template(
        'browse.html',
        title_slug = title_slugs[browse_type],
        browse_terms = browse_terms
    )

@app.route('/item/<noid>/')
def item(noid):
    if not re.match('^[a-z0-9]{12}$', noid):
        app.logger.debug(
            'in {}(), user-supplied noid appears invalid.'.format(
                sys._getframe().f_code.co_name
            )
        )
        abort(400)

    response = requests.get(
        '{}{}'.format(
            app.config['COLLECTIONS_ENDPOINT_PREFIX'],
            '/getItem'
        ),
        params = {
            'collection': 'mlc',
            'identifier': noid,
            'group': 'dma'
        }
    )

    item_data = json.loads(response.content.decode('utf-8'))

    assert 'ok' in item_data

    try:
        title_stub = item_data['ok']['titles'][0]
    except (IndexError, KeyError):
        title_stub = ''
        
    return render_template(
        'item.html',
        **(item_data['ok'] | {'title_stub': title_stub})
    )

@app.route('/search/')
def search():
    raise NotImplementedError

    return render_template(
        'search.html',
        facets = results['facets'],
        results = results['results']
    )
    
@app.route('/series/<noid>/')
def series(noid):
    if not re.match('^[a-z0-9]{12}$', noid):
        app.logger.debug(
            'in {}(), user-supplied noid appears invalid.'.format(
                sys._getframe().f_code.co_name
            )
        )
        abort(400)

    response = requests.get(
        '{}{}'.format(
            app.config['COLLECTIONS_ENDPOINT_PREFIX'],
            '/getSeries'
        ),
        params = {
            'collection': 'mlc',
            'identifier': noid,
            'group': 'dma'
        }
    )

    series_data = json.loads(response.content.decode('utf-8'))

    assert 'ok' in series_data

    try:
        title_stub = series_data['ok']['title'][0]
    except (IndexError, KeyError):
        title_stub = ''
        
    return render_template(
        'series.html',
        **(series_data['ok'] | {'title_stub': title_stub})
    )


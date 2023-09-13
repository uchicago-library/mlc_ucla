import click, json, logging, os, re, sqlite3, sqlite_dump, sys
from flask import abort, Flask, render_template, request, session, redirect
from flask_session import Session
from utils import MLCDB, build_sqlite_db
from flask_babel import Babel, gettext, lazy_gettext, get_locale
import requests
from urllib.parse import parse_qs, urlparse

app = Flask(__name__)

def get_locale():
    if (session):
        if( 'language' in session):
            return session.get('language', 'en')
        else:
            session['language'] = 'en'
            return session.get('language', 'en')

app.config.from_pyfile('local.py')
babel = Babel(app, default_locale='en', locale_selector=get_locale)

app.config["SESSION_PERMANENT"] = True
app.config["SESSION_TYPE"] = "filesystem"
Session(app)
# To define strings in code, it has to be with lazy_gettext()
# test_string_lazy = lazy_gettext(u'Test Lazy String Original') 
@app.context_processor
def inject_locale():
    return dict(locale = get_locale())

@app.route('/language-change', methods=["POST"])
def change_language():
    if( 'language' in session and session['language'] == 'en'):
        session['language'] = 'es'
    else:
        session['language'] = 'en'
    return redirect(request.referrer) 

app.logger.setLevel(logging.DEBUG)

if __name__ == '__main__':
    app.run(host='0.0.0.0')

class SetEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, set):
            return list(obj)
        return json.JSONEncoder.default(self, obj)

# CLI

@app.cli.command(
    'build-db', 
    short_help='Build or rebuild SQLite database from linked data triples.'
)
def cli_build_db():
    con = sqlite3.connect(':memory:')
    build_sqlite_db(con.cursor())

    with open(app.config['DB'], 'w', encoding='utf-8') as f:
        for line in sqlite_dump.iterdump(con):
            f.write(line + '\n')

@app.cli.command(
    'get-browse',
    short_help='Get a contributor, creator, date, decade, language or location browse.'
)
@click.argument('browse_type')
def cli_get_browse(browse_type):
    mlc_db = MLCDB(app.config)
    for row in mlc_db.get_browse(browse_type):
        print('{} ({})'.format(row[0], row[1]))

@app.cli.command(
    'get-browse-term',
    short_help='Get series for a specific browse term.'
)
@click.argument('browse_type')
@click.argument('browse_term')
def cli_get_browse_term(browse_type, browse_term):
    mlc_db = MLCDB(app.config)
    for row in mlc_db.get_browse_term(browse_type, browse_term):
        print(row)

@app.cli.command(
    'get-item',
    short_help='Get item info for an item identifier.'
)
@click.argument('item_identifier')
def cli_get_item(item_identifier):
    mlc_db = MLCDB(app.config)
    i = mlc_db.get_item(item_identifier)
    print(item_identifier)
    sys.stdout.write(('{}: {}\n' * 14 + '\n').format(
        'Panopto Links',
        ' '.join(i['panopto_links']),
        'Access Rights',
        ' | '.join(i['access_rights']),
        'Item Title',
        ' '.join(i['titles']),
        'Item Identifier',
        i['identifier'][0],
        'Contributor',
        ' | '.join(i['contributor']),
        'Indigenous Language',
        ' | '.join(i['subject_language']),
        'Language',
        ' | '.join(i['primary_language']),
        'Location Where Indigenous Language is Spoken',
        ' | '.join(i['location']),
        'Date',
        ' | '.join(i['date']),
        'Description',
        ' | '.join(i['description']),
        'Linguistic Data Type',
        ' | '.join(i['linguistic_data_type']),
        'Discourse Type',
        ' | '.join(i['discourse_type']),
        'Item Content Type',
        ' | '.join(i['content_type']),
        'Part of Series',
        i['is_part_of'][0]
    ))

@app.cli.command(
    'get-series',
    short_help='Get series info for a series identifier.'
)
@click.argument('series_identifier')
def cli_get_series(series_identifier):
    mlc_db = MLCDB(app.config)
    i = mlc_db.get_series(series_identifier)
    print(series_identifier)
    sys.stdout.write(('{}: {}\n' * 8 + '\n').format(
        'Series Title',
        ' '.join(i['titles']),
        'Series Identifier',
        i['identifier'][0],
        'Collection',
        '',
        'Indigenous Language',
        ' | '.join(i['subject_language']),
        'Language',
        ' | '.join(i['primary_language']),
        'Location Where Indigenous Language is Spoken',
        ' | '.join(i['location']),
        'Date',
        ' | '.join(i['date']),
        'Description',
        ' | '.join(i['description'])
    ))

@app.cli.command(
    'list-items',
    short_help='List item objects.'
)
@click.option('--verbose', '-v', is_flag=True, help='Verbose output.')
def cli_list_items(verbose):
    mlc_db = MLCDB(app.config)
    for i in mlc_db.get_item_list():
        print(i[0])
        if verbose:
            sys.stdout.write(('{}: {}\n' * 8 + '\n').format(
                'Item Title',
                ' '.join(i[1]['titles']),
                'Panopto Links',
                ' | '.join(i[1]['panopto_links']),
                'Access Rights',
                ' | '.join(i[1]['access_rights']),
                'Contributor',
                ' | '.join(i[1]['contributor']),
                'Indigenous Language',
                ' | '.join(i[1]['subject_language']),
                'Location',
                ' | '.join(i[1]['location']),
                'Date',
                ' | '.join(i[1]['date']),
                'Resource Type',
                ' | '.join(i[1]['content_type'])
            ))

@app.cli.command(
    'list-series',
    short_help='List series objects.'
)
@click.option('--verbose', '-v', is_flag=True, help='Verbose output.')
def cli_list_series(verbose):
    mlc_db = MLCDB(app.config)
    for i in mlc_db.get_series_list():
        print(i[0])
        if verbose:
            sys.stdout.write(('{}: {}\n' * 6 + '\n').format(
                'Series Title',
                ' '.join(i[1]['titles']),
                'Contributor',
                ' | '.join(i[1]['contributor']),
                'Indigenous Language',
                ' | '.join(i[1]['subject_language']),
                'Location',
                ' | '.join(i[1]['location']),
                'Date',
                ' | '.join(i[1]['date']),
                'Resource Type',
                ' | '.join(i[1]['content_type'])
            ))

@app.cli.command(
    'search',
    short_help='Search for term.'
)
@click.argument('term')
@click.argument('facet')
def cli_search(term, facet):
    mlc_db = MLCDB(app.config)
    for i in mlc_db.get_search(term, [facet]):
        print(i[0])
        print(i[2])
        sys.stdout.write(('{}: {}\n' * 6 + '\n').format(
            'Series Title',
            ' '.join(i[1]['titles']),
            'Contributor',
            ' | '.join(i[1]['contributor']),
            'Indigenous Language',
            ' | '.join(i[1]['language']),
            'Location',
            ' | '.join(i[1]['location']),
            'Date',
            ' | '.join(i[1]['date']),
            'Resource Type',
            ' | '.join(i[1]['content_type'])
        ))
        print('')

# WEB

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

@app.route('/suggest-corrections/')
def suggest_corrections():
    item_title = request.args.get('ittt')
    rec_id = request.args.get('rcid')
    item_url = request.args.get('iurl')
    return render_template(
        'suggest-corrections.html',
        item_title = item_title,
        rec_id = rec_id,
        item_url = item_url,
        title_slug = 'Suggest Corrections',
        hide_right_column = True
    )

@app.route('/browse/')
def browse():
    mlc_db = MLCDB(app.config)

    title_slugs = {
        'contributor': 'Browse by Contributors',
        'creator':     'Browse by Creator',
        'date':        'Browse by Date',
        'decade':      'Browse by Decade',
        'language':    'Browse by Language',
        'location':    'Browse by Location'
    }

    browse_type = request.args.get('type')
    if not browse_type in title_slugs.keys():
        app.logger.debug(
            'in {}(), type parameter not a key in browses dict.'.format(
                sys._getframe().f_code.co_name
            )
        )
        abort(400)

    browse_term = request.args.get('term')

    if browse_term:
        if browse_type:
            title_slug = "Results with "+browse_type+": "+browse_term+""
        else:
            title_slug = "Results for search: "+browse_term+""
        results = mlc_db.get_browse_term(browse_type, browse_term)
        return render_template(
            'search.html',
            facets = [],
            query = browse_term,
            query_field = browse_type,
            results = results,
            title_slug = title_slug
        )
    else:
        return render_template(
            'browse.html',
            title_slug = title_slugs[browse_type],
            browse_terms = mlc_db.get_browse(browse_type),
            browse_type = browse_type
        )

access_key = {
    'restricted': {
        'trans': lazy_gettext(u'Restricted'),
        'class': 'warning'
    },
    'public domain':  {
        'trans': lazy_gettext(u'Public Domain'),
        'class': 'success'
    }
}

def get_access_label_obj(item):
    # list of results
        # tuple for item
            # string for url
            # dictionary of data
                # list of values
    ar = item['access_rights']

    # [<string from database>, <translated string>, <bootstrap label class>]
    if( len(ar) > 0 and ar[0].lower() in access_key):
        return [
            ar[0], 
            access_key[ar[0].lower()]['trans'], 
            access_key[ar[0].lower()]['class']
            ]
    else:
        return ['emtpy','empty','info']

@app.route('/item/<noid>/')
def item(noid):
    def ark_to_panopto(ark_url):
        req = requests.head(ark_url, allow_redirects=True)
        percent_url = req.url
        return parse_qs(
            urlparse(
                parse_qs(
                    urlparse(percent_url).query
                )['ReturnUrl'][0]
            ).query
        )["id"][0]

    mlc_db = MLCDB(app.config)

    if not re.match('^[a-z0-9]{12}$', noid):
        app.logger.debug(
            'in {}(), user-supplied noid appears invalid.'.format(
                sys._getframe().f_code.co_name
            )
        )
        abort(400)

    item_data = mlc_db.get_item('https://ark.lib.uchicago.edu/ark:61001/' + noid)

    if item_data['panopto_links']:
        panopto_identifier = ark_to_panopto(item_data['panopto_links'][0])
    else:
        panopto_identifier = ''

    series = mlc_db.get_series_for_item('https://ark.lib.uchicago.edu/ark:61001/' + noid)

    try:
        title_stub = item_data['titles'][0]
    except (IndexError, KeyError):
        title_stub = ''
        
    return render_template(
        'item.html',
        **(item_data | {'series': series,
                        'title_slug': title_stub,
                        'access_rights': get_access_label_obj(item_data),
                        'panopto_identifier': panopto_identifier })
    )

@app.route('/search/')
def search():
    mlc_db = MLCDB(app.config)

    facets = request.args.getlist('facet')
    query = request.args.get('query')

    results = mlc_db.get_search(query, facets)
    mod_results = []
    
    for item in results:
        item_data = item[1]
        item_data['access_rights'] = get_access_label_obj(item_data)
        mod_results.append( (item[0], item_data ) )

    if( facets ):
        title_slug = 'Search Results for '+facets[0]
    else:
        title_slug = "Search Results for '"+query+"'"

    return render_template(
        'search.html',
        facets = [],
        query = query,
        query_field = '',
        results = mod_results,
        title_slug = title_slug
    )
    
@app.route('/series/<noid>/')
def series(noid):
    mlc_db = MLCDB(app.config)

    if not re.match('^[a-z0-9]{12}$', noid):
        app.logger.debug(
            'in {}(), user-supplied noid appears invalid.'.format(
                sys._getframe().f_code.co_name
            )
        )
        abort(400)

    series_data = mlc_db.get_series('https://ark.lib.uchicago.edu/ark:61001/' + noid)

    items = mlc_db.get_items_for_series('https://ark.lib.uchicago.edu/ark:61001/' + noid)
    print(json.dumps(items, indent=2))

    try:
        title_stub = series_data['titles'][0]
    except (IndexError, KeyError):
        title_stub = ''
        
    return render_template(
        'series.html',
        **(series_data | {
            'items': items,
            'title_slug': title_stub,
            'access_rights': get_access_label_obj(series_data)
        })
    )


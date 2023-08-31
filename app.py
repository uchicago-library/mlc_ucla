import click, json, logging, os, re, sqlite3, sqlite_dump, sys
from flask import abort, Flask, render_template, request
from utils import MLCDB, build_sqlite_db

app = Flask(__name__)
app.config.from_pyfile('local.py')

app.logger.setLevel(logging.DEBUG)

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

# CLI

@app.cli.command(
    'build-db', 
    short_help='Build or rebuild SQLite database from linked data triples.'
)
def cli_build_db():
    con = sqlite3.connect(':memory:')
    build_sqlite_db(con.cursor(), app.config['GRAPH'])

    with open(app.config['DB'], 'w') as f:
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
    'get-item',
    short_help='Get item info for an item identifier.'
)
@click.argument('item_identifier')
def cli_get_item(item_identifier):
    mlc_db = MLCDB(app.config)
    i = mlc_db.get_item(item_identifier)
    print(item_identifier)
    sys.stdout.write(('{}: {}\n' * 12 + '\n').format(
        'Item Title',
        ' '.join(i['titles']),
        'Item Identifier',
        i['identifier'][0],
        'Contributor',
        ' | '.join(i['contributor']),
        'Indigenous Language',
        ' | '.join(i['language']),
        'Language',
        ' | '.join(i['language']),
        'Location Where Indigenous Language is Spoken',
        ' | '.join(i['language']),
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
        ' | '.join(i['language']),
        'Language',
        ' | '.join(i['language']),
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
            sys.stdout.write(('{}: {}\n' * 6 + '\n').format(
                'Item Title',
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
                ' | '.join(i[1]['language']),
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

    return render_template(
        'browse.html',
        title_slug = title_slugs[browse_type],
        browse_terms = mlc_db.get_browse(browse_type),
        browse_type = browse_type
    )

@app.route('/item/<noid>/')
def item(noid):
    mlc_db = MLCDB(app.config)

    if not re.match('^[a-z0-9]{12}$', noid):
        app.logger.debug(
            'in {}(), user-supplied noid appears invalid.'.format(
                sys._getframe().f_code.co_name
            )
        )
        abort(400)

    item_data = mlc_db.get_item('https://ark.lib.uchicago.edu/ark:61001/' + noid)

    series = mlc_db.get_series_for_item('https://ark.lib.uchicago.edu/ark:61001/' + noid)

    try:
        title_stub = item_data['titles'][0]
    except (IndexError, KeyError):
        title_stub = ''
        
    return render_template(
        'item.html',
        **(item_data | {'series': series, 'title_stub': title_stub})
    )

@app.route('/search/')
def search():
    mlc_db = MLCDB(app.config)

    facets = request.args.getlist('facet')
    query = request.args.get('query')

    results = mlc_db.get_search(query, facets)

    return render_template(
        'search.html',
        facets = [],
        results = results
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
            'title_stub': title_stub
        })
    )


import click
import json
import os
import requests
import sys
import time
from flask import abort, Blueprint, current_app, render_template, request, session, redirect
from flask_caching import Cache
from utils import MLCGraph
from flask_babel import lazy_gettext
from local import BASE, CACHE_DEFAULT_TIMEOUT, CACHE_DIR, CACHE_THRESHOLD, CACHE_TYPE, DB, GLOTTO_LOOKUP, GLOTTO_TRIPLES, MESO_TRIPLES, REQUESTS_CACHE_DB, TGN_TRIPLES

import regex as re


mlc_ucla_search = Blueprint('mlc_ucla_search', __name__, cli_group=None, template_folder='templates/mlc_ucla_search')


mlc_g = MLCGraph({
    'GLOTTO_LOOKUP': GLOTTO_LOOKUP,
    'GLOTTO_TRIPLES': GLOTTO_TRIPLES
})

# FUNCTIONS

def get_locale():
    """Language switching."""
    if 'language' not in session:
        session['language'] = 'en'
    return session.get('language')

def get_item_info_str(item_info):
    """Format an item info dictionary for text output, e.g., a command line
       interface.

       Parameters:
           item_info (dict): an item info dictionary.

       Returns:
           str: a string for printing to stdout, etc.
    """
    s = ''
    s += '{}\n'.format(item_info['ark'])
    s += ('{}: {}\n' * 15 + '\n').format(
        'Panopto Links',
        ' '.join(item_info['panopto_links']),
        'Panopto Identifiers',
        ' '.join(item_info['panopto_identifiers']),
        'Access Rights',
        ' | '.join(item_info['access_rights']),
        'Item Title',
        ' '.join(item_info['titles']),
        'Item Identifier',
        item_info['identifier'][0],
        'Contributor',
        ' | '.join(item_info['contributor']),
        'Indigenous Language',
        ' | '.join(item_info['subject_language']),
        'Language',
        ' | '.join(item_info['primary_language']),
        'Location Where Indigenous Language is Spoken',
        ' | '.join(item_info['location']),
        'Date',
        ' | '.join(item_info['date']),
        'Description',
        ' | '.join(item_info['description']),
        'Linguistic Data Type',
        ' | '.join(item_info['linguistic_data_type']),
        'Discourse Type',
        ' | '.join(item_info['discourse_type']),
        'Item Content Type',
        ' | '.join(item_info['content_type']),
        'Part of Series',
        item_info['is_part_of'][0]
    )
    return s

def get_series_info_str(series_info):
    """Format a series info dictionary for text output, e.g., a command line
       interface.

       Parameters:
           series_info (dict): a series info dictionary.

       Returns:
           str: a string for printing to stdout, etc.
    """
    s = ''
    s += '{}\n'.format(series_info['ark'])
    s += ('{}: {}\n' * 8 + '\n').format(
        'Series Title',
        ' '.join(series_info['titles']),
        'Series Identifier',
        series_info['identifier'][0],
        'Collection',
        '',
        'Indigenous Language',
        ' | '.join(series_info['subject_language']),
        'Language',
        ' | '.join(series_info['primary_language']),
        'Location Where Indigenous Language is Spoken',
        ' | '.join(series_info['location']),
        'Date',
        ' | '.join(series_info['date']),
        'Description',
        ' | '.join(series_info['description'])
    )
    return s

# CLI

@mlc_ucla_search.cli.command(
    'fill-db-cache',
    short_help='Cache all MarkLogic requests.'
)
@click.option('--clean', '-c', is_flag=True, help='Delete cache before rebuilding.')
def cli_fill_db_cache(clean):
    """Cache all MarkLogic requests."""
 
    # delete the backend cache, if it exists. 
    if clean:
        try:
            os.remove(REQUESTS_CACHE_DB)
        except FileNotFoundError:
            pass

    # browses
    browse_list = ('contributor', 'creator', 'date', 'decade', 'language', \
                   'location')
    for i, browse in enumerate(browse_list):
        sys.stdout.write(
            'caching browse {} of {}.\n'.format(
                i + 1,
                len(browse_list)
            )
        ) 
        mlc_g.get_browse_terms(browse)

    # items
    item_list = mlc_g.get_item_identifiers()
    for i, item in enumerate(item_list):
        sys.stdout.write(
            'caching item {} of {}.\n'.format(
                i + 1, 
                len(item_list)
            )
        )
        mlc_g.get_item_info(item)

    # series
    series_list = mlc_g.get_series_identifiers()
    for i, series in enumerate(series_list):
        sys.stdout.write(
            'caching series {} of {}.\n'.format(
                 i + 1,
                 len(series_list)
             )
        )
        mlc_g.get_series_info(series)


@mlc_ucla_search.cli.command(
    'fill-template-cache',
    short_help='Clear template cache.'
)
@click.option('--clean', '-c', is_flag=True, help='Delete cache before rebuilding.')
def cli_fill_template_cache(clean):
    cache = Cache(config={
        'CACHE_DEFAULT_TIMEOUT': CACHE_DEFAULT_TIMEOUT,
        'CACHE_DIR': CACHE_DIR,
        'CACHE_THRESHOLD': CACHE_THRESHOLD,
        'CACHE_TYPE': CACHE_TYPE
    })

    cache.init_app(current_app)
    
    # delete the backend cache, if it exists. 
    if clean:
        with current_app.app_context():
            cache.clear()

    series_ids = mlc_g.get_series_identifiers()
    for i, series_id in enumerate(series_ids):
        print('caching template for series {} of {}.'.format(i + 1, len(series_ids)))
        with current_app.test_request_context():
            render_template(
                'search.html',
                facets=[],
                query='',
                query_field='',
                results=[[
                    series_id,
                    mlc_g.get_item_identifiers_for_series(series_id),
                    0
                ]],
                title_slug=''
            )
          

@mlc_ucla_search.cli.command(
    'get-browse',
    short_help='Get a contributor, creator, date, decade, language or ' +
               'location browse.'
)
@click.argument('browse_type')
def cli_get_browse(browse_type):
    """List browse terms."""
    browse = mlc_g.get_browse_terms(browse_type)

    browse_terms = list(browse.keys())
    # sort alphabetically, ignoring punctuation. 
    browse_terms.sort(key=lambda x:re.sub('[^\\p{L}\\p{N}]+', '', x[0]))

    for browse_term in browse_terms:
        sys.stdout.write(
            '{} ({})\n'.format(
                browse_term,
                len(browse[browse_term])
            )
        )


@mlc_ucla_search.cli.command(
    'get-browse-term',
    short_help='Get series for a specific browse term.'
)
@click.argument('browse_type')
@click.argument('browse_term')
def cli_get_browse_term(browse_type, browse_term):
    browse = mlc_g.get_browse_terms(browse_type)
    for s in browse[browse_term]:
        sys.stdout.write(get_series_info_str(mlc_g.get_series_info(s)))


@mlc_ucla_search.cli.command(
    'get-item',
    short_help='Get item info for an item identifier.'
)
@click.argument('item_identifier')
@click.option('--json-output', '-j', is_flag=True, help='JSON output.')
def cli_get_item(item_identifier, json_output):
    info = mlc_g.get_item_info(item_identifier)
    if json_output:
        sys.stdout.write(json.dumps(info))
    else:
        sys.stdout.write(get_item_info_str(info))


@mlc_ucla_search.cli.command(
    'get-series',
    short_help='Get series info for a series identifier.'
)
@click.argument('series_identifier')
@click.option('--json-output', '-j', is_flag=True, help='JSON output.')
def cli_get_series(series_identifier, json_output):
    info = mlc_g.get_series_info(series_identifier)
    if json_output:
        sys.stdout.write(json.dumps(info))
    else:
        sys.stdout.write(get_series_info_str(info))


@mlc_ucla_search.cli.command(
    'list-items',
    short_help='List item objects.'
)
@click.option('--verbose', '-v', is_flag=True, help='Verbose output.')
@click.option('--json-output', '-j', is_flag=True, help='JSON output.')
def cli_list_items(verbose, json_output):
    for i in mlc_g.get_item_identifiers():
        if json_output or verbose:
            info = mlc_g.get_item_info(i)
        if json_output:
            sys.stdout.write(json.dumps(info, indent=2))
        elif verbose:
            sys.stdout.write(get_item_info_str(info))
        else:
            sys.stdout.write('{}\n'.format(i))


@mlc_ucla_search.cli.command(
    'list-series',
    short_help='List series objects.'
)
@click.option('--verbose', '-v', is_flag=True, help='Verbose output.')
@click.option('--json-output', '-j', is_flag=True, help='JSON output.')
def cli_list_series(verbose, json_output):
    for i in mlc_g.get_series_identifiers():
        if json_output or verbose:
            info = mlc_g.get_series_info(i)
        if json_output:
            sys.stdout.write(json.dumps(info, indent=2))
        elif verbose:
            sys.stdout.write(get_series_info_str(info))
        else:
            sys.stdout.write('{}\n'.format(i))


@mlc_ucla_search.cli.command(
    'search',
    short_help='Search for term.'
)
@click.argument('term')
#@click.argument('facet')
#def cli_search(term, facet):
def cli_search(term):
    for i in mlc_g.search(term):
        print(i)


# CGIMAIL
# this dictionary and the following two functions
# serve as middleman to use cgimail https://dldc.lib.uchicago.edu/local/programming/cgimail.html
# so that users receive a controlled receipt customized to our platform,
# but still making use of the security features provided by cgimail.

cgimail_dic= {
    'default' : {
        'from' : 'MLC Website <vitorg@uchicago.edu>'
    },
    'error': {
        'title': lazy_gettext('Error status'),
        'text': lazy_gettext('There was a technical issue sending your request, and we can\'t determine it\'s nature. Please try again. We apologize for any inconvenience. If the issue persists, send an email to the Digital Library Development Center (DLDC) at the The Joseph Regenstein Library dldc-info@lib.uchicago.edu')
    },
    'request_account': {
        'rcpt': 'askscrc',
        'subject': '[TEST] Request for MLC account',
        'title': lazy_gettext('Your request was successfully sent'),
        'text': lazy_gettext('Thank you for requesting an account. Requests are typically processed within 5 business days. You will be notified of any status change.')
    },
    'request_access': {
        'rcpt': 'askscrc',
        'subject': '[TEST] Request for access to MLC restricted series',
        'title': lazy_gettext('Your request was successfully sent'),
        'text': lazy_gettext('Thank you for your interest in this content. '
            'Request to content access is typically processed within 3 businessdays. '
            'You will be notified of any status change to the email associated with your account. '
            'We ask each visitor to avoid making duplicate requests by keeping a record of them, '
            'as we have no way to display these for each user at the moment.')
    },
    'feedback': {
        'rcpt': 'woken',
        'subject': '[TEST] Feedback about Mesoamerican Language Collection Portal',
        'title': lazy_gettext('Thank you for your submission'),
        'text': lazy_gettext('Your suggestions or correction is welcomed. We will revise it promptly and get back to you if we need any further information.')
    }
}

@mlc_ucla_search.route('/send-cgimail', methods=['POST'])
def send_cgimail():
    # msg_type specifies which form it is coming from.
    msg_type = request.form.get('msg_type')

    if msg_type not in cgimail_dic:
        return redirect('/submission-receipt?status=error')

    # forward all form fields to cgimail except for the msg_type
    # and add cgimail required fields
    args = {}
    for arg in request.form:
        if arg == 'msg_type':
            continue
        args[arg] = request.form[arg]

    args['from'] = cgimail_dic['default']['from']
    args['rcpt'] = cgimail_dic[msg_type]['rcpt']
    args['subject'] = cgimail_dic[msg_type]['subject']

    # Send the request to CGIMail.
    # CGIMail looks for a referer in the request header.
    cgiurl = 'https://www.lib.uchicago.edu/cgi-bin/cgimail'
    session = requests.Session()
    session.headers.update({'referer': 'https://mlc.lib.uchicago.edu/'})
    r = session.post(cgiurl, data = args)

    # Interpret the request result and redirect to receipt.
    # cgimial returns a 200 even when it refuses a request.
    # developer says that cgimail is unlikely to be changed in any predictable future.
    request_status = 'success' if ( r.text.find("Your message was delivered to the addressee") > -1 and r.status_code == 200 ) else 'failed'
    goto = '/submission-receipt?status=' + request_status +"&view=" + request.form.get('msg_type')
    return redirect(goto)

@mlc_ucla_search.route('/submission-receipt')
def submission_receipt():
    title_slug = lazy_gettext('Receipt status for Request')

    view = 'error'
    if request.args.get('status') == 'success' and request.args.get('view') in cgimail_dic:
        view = request.args.get('view')

    return (render_template(
        'cgimail-receipt.html',
        title_slug = title_slug,
        msg_title = cgimail_dic[view]['title'],
        msg_text = cgimail_dic[view]['text']
        ),400
    )

# WEB

@mlc_ucla_search.context_processor
def utility_processor():
    def get_item_breadcrumb(identifier):
        item_info = mlc_g.get_item_info(identifier)
        series_id = mlc_g.get_series_identifiers_for_item(identifier)[0]
        series_info = mlc_g.get_series_info(series_id)
        return '<a href=\'/series/{}\'>{}</a> &gt; {}'.format(
            series_id.replace(BASE, ''),
            series_info['titles'][0],
            item_info['titles'][0]
        )
    def get_request_access_button(identifier):
        is_restricted = True
        has_panopto = False
        item_id_with_panopto = ''
        item_title_with_panopto = ''
        if mlc_g.is_series(identifier):
            series_ids = [identifier]
            for item_id in mlc_g.get_item_identifiers_for_series(series_ids[0]):
                item_info = mlc_g.get_item_info(item_id)
                if item_info['panopto_identifiers'] and \
                    len(item_info['panopto_identifiers']):
                    has_panopto = True
                    item_id_with_panopto = item_info['identifier'][0]
                    item_title_with_panopto = item_info['titles'][0]
            series_info = mlc_g.get_series_info(series_ids[0]) 
            is_restricted = series_info['access_rights'][0].lower() == 'restricted'
        else:
            item_id = identifier
            series_ids = mlc_g.get_series_identifiers_for_item(identifier)
            item_info = mlc_g.get_item_info(item_id)
            if item_info['panopto_identifiers'] and \
                len(item_info['panopto_identifiers']):
                has_panopto = True
                item_id_with_panopto = item_info['identifier'][0]
                item_title_with_panopto = item_info['titles'][0]
            for series_id in series_ids:
                series_info = mlc_g.get_series_info(series_id)
                if series_info['access_rights'][0].lower() == 'restricted':
                    is_restricted = True
        return {
            'show': is_restricted and has_panopto,
            'series_id': ','.join(series_ids), # some items belong to multiple series
            'item_id': item_id_with_panopto,
            'item_title': item_title_with_panopto
        }
    return {
        'get_item_breadcrumb': get_item_breadcrumb,
        'get_item_info': lambda x: mlc_g.get_item_info(x),
        'get_series_info': lambda x: mlc_g.get_series_info(x),
        'get_request_access_button': get_request_access_button
    }


@mlc_ucla_search.route('/language-change', methods=['POST'])
def change_language():
    if 'language' in session and session['language'] == 'en':
        session['language'] = 'es'
    else:
        session['language'] = 'en'
    return redirect(request.referrer)


@mlc_ucla_search.errorhandler(400)
def bad_request(e):
    return (render_template('400.html'), 400)


@mlc_ucla_search.errorhandler(404)
def not_found(e):
    return (render_template('404.html'), 404)


@mlc_ucla_search.errorhandler(500)
def bad_request(e):
    return (render_template('500.html'), 500)


@mlc_ucla_search.route('/')
def home():
    return render_template(
        'home.html'
    )

@mlc_ucla_search.route('/browse/')
def browse():
    title_slugs = {
        'contributor': lazy_gettext(u'Browse by Contributors'),
        'creator':     lazy_gettext(u'Browse by Creator'),
        'date':        lazy_gettext(u'Browse by Date'),
        'decade':      lazy_gettext(u'Browse by Decade'),
        'language':    lazy_gettext(u'Browse by Language'),
        'location':    lazy_gettext(u'Browse by Location')
    }

    browse_sort = request.args.get('sort')

    browse_type = request.args.get('type')
    if browse_type not in title_slugs.keys():
        current_app.logger.debug(
            'in {}(), type parameter not a key in browses dict.'.format(
                sys._getframe().f_code.co_name
            )
        )
        abort(400)

    browse_term = request.args.get('term')

    browse_dict = mlc_g.get_browse_terms(browse_type)

    if browse_term:
        if browse_type:
            title_slug = lazy_gettext('Results with') + ' ' + \
                browse_type + ': ' + browse_term
        else:
            title_slug = lazy_gettext('Results for search') + \
                ': ' + browse_term

        sort_field = 'dbid'
        if browse_type == 'decade':
            sort_field = 'date'

        results = mlc_g.get_browse_terms(browse_type)[browse_term]

        results_with_label_ui_data = []
        for result in results:
            series_data = mlc_g.get_series_info(result)
            results_with_label_ui_data.append((result, series_data))

        return render_template(
            'search.html',
            facets=[],
            query=browse_term,
            query_field=browse_type,
            results=results_with_label_ui_data,
            title_slug=title_slug
        )
    else:
        browse_terms = []
        for k, v in mlc_g.get_browse_terms(browse_type).items():
            browse_terms.append((k, len(v)))

        if browse_sort:
            browse_terms.sort(key=lambda x:x[1], reverse=True)
        else:
            # sort alphabetically, ignoring punctuation. 
            browse_terms.sort(key=lambda x:re.sub('[^\\p{L}\\p{N}]+', '', x[0]))

        return render_template(
            'browse.html',
            title_slug=title_slugs[browse_type],
            browse_terms=browse_terms,
            browse_type=browse_type
        )

@mlc_ucla_search.route('/search/')
def search():
    facets = request.args.getlist('facet')
    query = request.args.get('query')
    sort_type = request.args.get('sort', 'rank')

    results = mlc_g.search(query, facets, sort_type)

    if facets:
        title_slug = lazy_gettext(u'Search Results for') + ' ' + facets[0]
    elif query:
        title_slug = lazy_gettext(u'Search Results for') + ' \'' + query + '\''
    else:
        title_slug = lazy_gettext(u'Search Results')

    return render_template(
        'search.html',
        facets=[],
        query=query,
        query_field='',
        results=results,
        title_slug=title_slug
    )


@mlc_ucla_search.route('/series/<noid>/')
def series(noid):
    if not re.match('^[a-z0-9]{12}$', noid):
        current_app.logger.debug(
            'in {}(), user-supplied noid appears invalid.'.format(
                sys._getframe().f_code.co_name
            )
        )
        abort(400)

    series_data = mlc_g.get_series_info(BASE + noid)

    grouped_items = mlc_g.get_grouped_item_identifiers_for_series(BASE + noid)

    try:
        title_slug = ' '.join(series_data['titles'])
    except (IndexError, KeyError):
        title_slug = ''

    return render_template(
        'series.html',
        **(series_data | {
            'grouped_items': grouped_items,
            'ark': BASE + noid,
            'object_type': 'series',
            'title_slug': title_slug,
            'access_rights': series_data['access_rights']
        })
    )

@mlc_ucla_search.route('/item/<noid>/')
def item(noid):
    if not re.match('^[a-z0-9]{12}$', noid):
        current_app.logger.debug(
            'in {}(), user-supplied noid appears invalid.'.format(
                sys._getframe().f_code.co_name
            )
        )
        abort(400)

    item_data = mlc_g.get_item_info(BASE + noid, True)

    if item_data['panopto_identifiers']:
        panopto_identifier = item_data['panopto_identifiers'][0]
    else:
        panopto_identifier = ''

    series = mlc_g.get_series_identifiers_for_item(BASE + noid)

    try:
        title_slug = item_data['titles'][0]
    except (IndexError, KeyError):
        title_slug = ''

    return render_template(
        'item.html',
        **(item_data | {
            'ark': BASE + noid,
            'object_type': 'item',
            'series': series,
            'title_slug': title_slug,
            'access_rights': item_data['access_rights'],
            'panopto_identifier': panopto_identifier
        })
    )

@mlc_ucla_search.route('/request-account')
def request_account():
    return render_template(
        'request-account.html'
    )

@mlc_ucla_search.route('/suggest-corrections/')
def suggest_corrections():
    return render_template(
        'suggest-corrections.html',
        item_title = request.args.get('ittt'),
        rec_id = request.args.get('rcid'),
        item_url = request.args.get('iurl'),
        title_slug = lazy_gettext(u'Suggest Corrections'),
        hide_right_column = True
    )

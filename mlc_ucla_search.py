import apsw
import click
import os
import re
import requests
import sqlite3
import sys
from flask import abort, Blueprint, current_app, g, render_template, request, session, redirect
from utils import GlottologLookup, MLCDB
from flask_babel import lazy_gettext
from local import BASE, DB, GLOTTO_LOOKUP, MESO_TRIPLES, TGN_TRIPLES
from collections import OrderedDict


mlc_ucla_search = Blueprint('mlc_ucla_search', __name__, cli_group=None, template_folder='templates/mlc_ucla_search')

# FUNCTIONS

def get_locale():
    """Language switching."""
    if 'language' not in session:
        session['language'] = 'en'
    return session.get('language')

# CLI

def print_item(item_info):
    sys.stdout.write('{}\n'.format(item_info['ark']))
    sys.stdout.write(('{}: {}\n' * 15 + '\n').format(
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
    ))


def print_series(series_info):
    sys.stdout.write('{}\n'.format(series_info['ark']))
    sys.stdout.write(('{}: {}\n' * 8 + '\n').format(
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
    ))

@mlc_ucla_search.before_app_request
def before_request():
    if 'mlc_db' not in g:
        g.mlc_db = MLCDB({
            'DB': DB,
            'GLOTTO_LOOKUP': GLOTTO_LOOKUP,
            'MESO_TRIPLES': MESO_TRIPLES,
            'TGN_TRIPLES': TGN_TRIPLES
        })
        g.mlc_db.connect()

@mlc_ucla_search.cli.command(
    'build-db',
    short_help='Build or rebuild SQLite database from linked data triples.'
)
def cli_build_db():
    """Build a SQLite database from linked data triples."""
    try: 
        os.remove(DB)
    except OSError:
        pass
    mlc_db = MLCDB({
        'DB': DB,
        'GLOTTO_LOOKUP': GLOTTO_LOOKUP,
        'MESO_TRIPLES': MESO_TRIPLES,
        'TGN_TRIPLES': TGN_TRIPLES
    })
    con = sqlite3.connect(DB)
    mlc_db.build_db(con)


@mlc_ucla_search.cli.command(
    'build-glottolog-lookup',
    short_help='Build or rebuild Glottolog lookup from linked data triples.'
)
def cli_build_glottolog_lookup():
    """Build JSON data structure from linked data triples."""
    GlottologLookup(mlc_ucla_search.config).build_lookup()


@mlc_ucla_search.cli.command(
    'get-browse',
    short_help='Get a contributor, creator, date, decade, language or ' +
               'location browse.'
)
@click.argument('browse_type')
def cli_get_browse(browse_type):
    """List browse terms."""
    for row in g.mlc_db.get_browse(browse_type):
        sys.stdout.write('{} ({})\n'.format(row[0], row[1]))


@mlc_ucla_search.cli.command(
    'get-browse-term',
    short_help='Get series for a specific browse term.'
)
@click.argument('browse_type')
@click.argument('browse_term')
def cli_get_browse_term(browse_type, browse_term):
    for row in g.mlc_db.get_browse_term(browse_type, browse_term):
        print_series(row[1])


@mlc_ucla_search.cli.command(
    'get-item',
    short_help='Get item info for an item identifier.'
)
@click.argument('item_identifier')
def cli_get_item(item_identifier):
    print_item(g.mlc_db.get_item(item_identifier))


@mlc_ucla_search.cli.command(
    'get-series',
    short_help='Get series info for a series identifier.'
)
@click.argument('series_identifier')
def cli_get_series(series_identifier):
    print_series(g.mlc_db.get_series(series_identifier))


@mlc_ucla_search.cli.command(
    'list-items',
    short_help='List item objects.'
)
@click.option('--verbose', '-v', is_flag=True, help='Verbose output.')
def cli_list_items(verbose):
    for i in g.mlc_db.get_item_list():
        if verbose:
            print_item(g.mlc_db.get_item(i))
        else:
            sys.stdout.write('{}\n'.format(i))


@mlc_ucla_search.cli.command(
    'list-series',
    short_help='List series objects.'
)
@click.option('--verbose', '-v', is_flag=True, help='Verbose output.')
def cli_list_series(verbose):
    for i in g.mlc_db.get_series_list():
        if verbose:
            print_series(g.mlc_db.get_series(i))
        else:
            sys.stdout.write('{}\n'.format(i))


@mlc_ucla_search.cli.command(
    'search',
    short_help='Search for term.'
)
@click.argument('term')
@click.argument('facet')
def cli_search(term, facet):
    for i in g.mlc_db.get_search(term, [facet], 'rank'):
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


# CGIMAIL
# this dictionary and the following two functions
# serve as middleman to use cgimail https://dldc.lib.uchicago.edu/local/programming/cgimail.html
# so that users receive a controlled receipt customized to our platform,
# but still making use of the security features provided by cgimail.

cgimail_dic= {
    'default' : {
        'from' : 'MLC Website'
    },
    'error': {
        'title': lazy_gettext('Error'),
        'text': lazy_gettext('There was a technical issue sending your request, and we can\'t determine its nature. Please try again. We apologize for any inconvenience. If the issue persists, send an email to the Digital Library Development Center (DLDC) at the The Joseph Regenstein Library web-admin@lib.uchicago.edu')
    },
    'request_account': {
        'rcpt': 'askscrc',
        'subject': 'Request for MLC account',
        'title': lazy_gettext('Your request was successfully sent'),
        'text': lazy_gettext('Thank you for requesting an account. Requests are typically processed within 5 business days. You will be notified of any status change.')
    },
    'request_access': {
        'rcpt': 'askscrc',
        'subject': 'Request for access to MLC restricted series',
        'title': lazy_gettext('Your request was successfully sent'),
        'text': lazy_gettext('Thank you for your interest in this content. '
            'Request to content access is typically processed within 3 business days. '
            'You will be notified of any status change to the email associated with your account. '
            'We ask each visitor to avoid making duplicate requests by keeping a record of them, '
            'as we have no way to display these for each user at the moment.')
    },
    'feedback': {
        'rcpt': 'woken',
        'subject': 'Feedback about Mesoamerican Language Collection Portal',
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
    title_slug = lazy_gettext('Request Receipt')

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

# removed restricted label due to issue https://github.com/uchicago-library/ucla/issues/84
# ['Restricted'], 
# ['Public domain'], 
# ['Campus'], 
access_key = {
    'restricted': {
        'trans': lazy_gettext(u'By Request'),
        'class': 'warning'
    },
    'campus': {
        'trans': lazy_gettext(u'Account Required'),
        'class': 'info'
    },
    'public domain':  {
        'trans': lazy_gettext(u'Open'),
        'class': 'success'
    }
}


def sortDictByFormat(item):
    assert type(item) in (str, list, tuple)
    if not isinstance(item, str):
        assert len(item)
        assert isinstance(item[0], str)
        item = item[0]        
    order_of_formats = ['sound','video','image','text','archival','unknown']
    return order_of_formats.index(item) if item in order_of_formats else 999
def sortDictByFormatKey(d):
    """
    Sorts a dictionary by its keys based on a custom order.

    Parameters:
    d (dict): The dictionary to sort.

    Returns:
    dict: The dictionary sorted by the custom order of keys.
    """
    order_of_formats = ['sound','video','image','text','archival','unknown']
    sorted_items = {key: d[key] for key in order_of_formats if key in d}
    d.clear()
    d.update(sorted_items)
    return d

def sortListOfItems(item):
    if isinstance(item, tuple):
        item = item[1]
    # Give priority to items with a panopto link, and then items with a 'has_format'
    # return len(item[1]['panopto_links']) * 10 + len(item[1]['has_format'])
    if 'panopto_links' in item and len(item['panopto_links']):
            return 0
    elif 'has_format' in item and len(item['has_format']):
        return 1
    else:
        return 2

def sortListOfItemsByID(item):
    if isinstance(item, tuple):
        item = item[1]
    return int(item['identifier'][0])

def get_access_label_obj(item):
    # list of results
    #   tuple for item
    #     string for url
    #     dictionary of data
    #       list of values
    # ! assumes item['access_rights'] as a list will always have only one item
    ar = item['access_rights']
    if len(ar) > 0 and ar[0].lower() in access_key:
        return [
            ar[0],
            access_key[ar[0].lower()]['trans'],
            access_key[ar[0].lower()]['class']
            ]
    else:
        return ['emtpy', 'By Request', 'info']

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

    browse_type = request.args.get('type')
    if browse_type not in title_slugs.keys():
        current_app.logger.debug(
            'in {}(), type parameter not a key in browses dict.'.format(
                sys._getframe().f_code.co_name
            )
        )
        abort(400)

    browse_term = request.args.get('term')

    if browse_term:
        if browse_type:
            title_slug = lazy_gettext('Results with') + \
                         ' ' + browse_type + ': ' + browse_term
        else:
            title_slug = lazy_gettext('Results for search') + \
                         ': ' + browse_term

        sort_field = 'dbid'
        if browse_type == 'decade':
            sort_field = 'date'

        results = g.mlc_db.get_browse_term(browse_type, browse_term, sort_field)

        results_with_label_ui_data = []
        for item in results:
            item_data = item[1]
            item_data['access_rights'] = get_access_label_obj(item_data)
            results_with_label_ui_data.append((item[0], item_data))

        return render_template(
            'search.html',
            facets=[],
            query=browse_term,
            query_field=browse_type,
            results=results_with_label_ui_data,
            title_slug=title_slug
        )
    else:
        browse_sort = request.args.get('sort')
        browse_terms_list = g.mlc_db.get_browse(browse_type, browse_sort)
        if browse_sort != "count":
            browse_terms_dic = {}
            alphabet = ""
            for b in browse_terms_list:
                if alphabet != b[0][0]:
                    alphabet = b[0][0]
                    browse_terms_dic[alphabet] = []
                browse_terms_dic[alphabet].append(b)
        else:
            browse_terms_dic = browse_terms_list

        return render_template(
            'browse.html',
            title_slug=title_slugs[browse_type],
            browse_terms=browse_terms_dic,
            is_alphabetical = browse_sort != "count",
            browse_type=browse_type
        )

@mlc_ucla_search.route('/search/')
def search():
    facets = request.args.getlist('facet')
    query = request.args.get('query')
    sort_type = request.args.get('sort', 'rank')

    db_results = g.mlc_db.get_search(query, facets, sort_type)

    processed_results = []
    for db_series in db_results:
        series_data = g.mlc_db.get_series(db_series[0])
        series_data['access_rights'] = get_access_label_obj(series_data)
        series_data['sub_items'] = []
        for i in db_series[1]:
            info = g.mlc_db.get_item(i)
            series_data['sub_items'].append(info)
        series_data['sub_items'].sort(key=sortListOfItemsByID)
        processed_results.append((db_series[0], series_data))

    if facets:
        title_slug = lazy_gettext(u'Search Results for') + ' ' + facets[0]
    elif query:
        title_slug = lazy_gettext(u'Search Results for') + ' \'' + query + '\''
    else:
        title_slug = lazy_gettext(u'Search Results')

    return render_template(
        'search.html',
        is_search=True,
        facets=[],
        query=query,
        query_field='',
        results=processed_results,
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

    series_data = g.mlc_db.get_series(BASE + noid)

    items = []
    for i in g.mlc_db.get_items_for_series(BASE + noid):
        items.append((
            i,
            g.mlc_db.get_item(i)
        ))

    # Iterate through all items to regroup
    grouped_items = {}
    available_formats = {}
    for i in items:
        # format_obj = [format_group, format_style, format_icon, original_medium, <count>]
        format_obj = i[1]['medium']
        # Get all formats available to display in Series metadata table
        if format_obj[0] not in available_formats:
            available_formats[format_obj[0]] = format_obj+[1]
        else:
            available_formats[format_obj[0]][4] += 1

        # filter out non-original items to display in series level
        if not i[1]['is_format_of']:
            # Group items by medium/format
            if format_obj[0] not in grouped_items:
                grouped_items[format_obj[0]] = []
            grouped_items[format_obj[0]].append(i[1])
    available_formats = sortDictByFormatKey(available_formats)
    # Sort Items by ID
    for format_type, item_list in grouped_items.items():
        grouped_items[format_type].sort(key=sortListOfItemsByID)

    # Get request access button info
    series_data['request_access_button'] = g.mlc_db.get_series_request_access_info(BASE + noid)

    try:
        title_slug = ' '.join(series_data['titles'])
    except (IndexError, KeyError):
        title_slug = ''

    return render_template(
        'series.html',
        **(series_data | {
            'is_series' : True,
            'grouped_items': grouped_items,
            'title_slug': title_slug,
            'available_formats': available_formats,
            'access_rights': get_access_label_obj(series_data)
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

    item_data = g.mlc_db.get_item(BASE + noid, True)

    # normalize panopto key value
    if item_data['panopto_identifiers']:
        panopto_identifier = item_data['panopto_identifiers'][0]
    else:
        panopto_identifier = ''

    # Get all series for this item
    series = []
    for s in g.mlc_db.get_series_for_item(BASE + noid):
        series.append((s, g.mlc_db.get_series_info(s)))
    series_id = []
    for s in series:
        series_id.append(s[1]['identifier'][0])

    try:
        title_slug = item_data['titles'][0]
    except (IndexError, KeyError):
        title_slug = ''

    breadcrumb = '<a href=\'/series/{}\'>{}</a> &gt; {}'.format(
        series[0][0].replace(BASE, ''),
        series[0][1]['titles'][0],
        item_data['titles'][0]
    )

    # Descendats
    # The descdants are a list of generations(levels),
    # Which have lists of items (only identifier) grouped into mediums.
    # We take them and get the full item object,
    # we also obtain all the available formats from the descendant tree to list them
    available_formats = {}
    if len(item_data['descendants'])>0:
        for level, mediums_in_level in item_data['descendants'].items():
            for medium, item_list in mediums_in_level.items():
                for k, item in reversed(list(enumerate(item_list))):
                    fetched_item = g.mlc_db.get_item(item)
                    if item_data['identifier'][0] == fetched_item['identifier'][0]:
                        item_data['descendants'][level][medium].pop(k)
                    else:
                        item_data['descendants'][level][medium][k] = fetched_item

                        # format_obj = [format_group, format_style, format_icon, original_medium, <count>]
                        format_obj = fetched_item['medium']
                        if format_obj[0] not in available_formats:
                            available_formats[format_obj[0]] = format_obj+[1]
                        else:
                            available_formats[format_obj[0]][4] += 1

        available_formats = sortDictByFormatKey(available_formats)
        for level, formats in item_data['descendants'].items():
            # sort mediums by custom order
            item_data['descendants'][level] = OrderedDict(sorted(item_data['descendants'][level].items(), key=sortDictByFormat  ))
            for medium, item_list in formats.items():
                item_data['descendants'][level][medium].sort(key=sortListOfItemsByID)
    
    request_access_button = {'show': False}
    for serie in series:
        if serie[1]['request_access_button']['show']:
            request_access_button = serie[1]['request_access_button']
            break

    return render_template(
        'item.html',
        **(item_data | {
            'is_item' : True,
            'series': series,
            'title_slug': title_slug,
            'access_rights': get_access_label_obj(item_data),
            'request_access_button' : request_access_button,
            'panopto_identifier': panopto_identifier,
            'available_formats': available_formats,
            'breadcrumb': breadcrumb})
    )

@mlc_ucla_search.route('/request-account')
def request_account():
    return render_template(
        'form-request-account.html'
    )
@mlc_ucla_search.route('/request-access')
def request_access():
    return render_template(
        'form-request-access.html'
    )

@mlc_ucla_search.route('/suggest-corrections/')
def suggest_corrections():
    return render_template(
        'form-suggest-corrections.html',
        item_title = request.args.get('ittt'),
        rec_id = request.args.get('rcid'),
        item_url = request.args.get('iurl'),
        title_slug = lazy_gettext(u'Suggest Corrections'),
        hide_right_column = True
    )

@mlc_ucla_search.route('/login')
def login():
    return redirect('/Shibboleth.sso/Login?target='+str(request.referrer))

@mlc_ucla_search.route('/credits')
def credits():
    return render_template(
        'credits.html'
    )

@mlc_ucla_search.route('/terms-of-use')
def access_terms():
    return render_template(
        'static-access-terms.html',
        title_slug = lazy_gettext(u'Terms of Use'),
    )

# @mlc_ucla_search.route('/about-the-project')
# @mlc_ucla_search.route('/about-the-collection')
# @mlc_ucla_search.route('/how-to-deposit-materials')
# @mlc_ucla_search.route('/related-collections')
# @mlc_ucla_search.route('/additional-resources')
@mlc_ucla_search.route('/page-under-development')
def wip():
    return render_template(
        'wip.html'
    )

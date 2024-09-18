import os
import re
import requests
import sys
from lxml import etree

CACHE_DIR = 'cache'

def get_ochre_url(uuid):
    """Get an OCHRE URL from a UUID.

    Args:
        uuid (str): an OCHRE UUID.

    Returns:
        string: an OCHRE URL.
    """
    return 'https://ochre.lib.uchicago.edu/ochre?uuid={}&xsl=none'.format(uuid)

def get_cached_content(uuid):
    """Simple caching for OCHRE requests.

    Args:
        uuid (str): an OCHRE UUID.

    Side effect:
        stores contents of this request in CACHE_DIR.

    Returns:
        str: request contents. 
    """
    path = os.path.join(CACHE_DIR, uuid + '.xml')
    if os.path.exists(path):
        with open(path, 'rb') as f:
            return f.read()
    else:
        content = requests.get(get_ochre_url(uuid)).content
        root = etree.fromstring(content)
        with open(path, 'wb') as f:
            f.write(etree.tostring(root, pretty_print=True, encoding='unicode').encode('utf-8'))
        return content

def get_ochre(uuid):
    """Get OCHRE ElementTree for a specific UUID.

    Args:
        uuid (str): an OCHRE UUID.

    Returns:
        lxml.ElementTree: OCHRE data.
    """
    return etree.fromstring(get_cached_content(uuid))

def get_uuid_descendants(uuid, visited=set(), depth=0, max_depth=5):
    """Get a set of a UUID and its desendants.

    Args:
        uuid (str):     an OCHRE UUID.
        visited (set):  a set of the UUIDs already visited.
        depth (int):    current depth of search.
        max_depth(int): maximum depth.

    Returns:
        set: a set of UUIDs.
    """
    if depth <= max_depth and uuid not in visited:
        ochre = get_ochre(uuid)
        for concept in ochre.xpath('''
            /ochre/concept/concept[
                interpretations/interpretation/properties/property[
                    label/content/string/text() = "Classification" and 
                    (
                        value/content/string/text() = "Digital Collection" or
                        value/content/string/text() = "Work"
                    )
                ]
            ]
        '''):
            child_uuid = concept.xpath('@uuid')[0]
            visited |= get_uuid_descendants(child_uuid, visited, depth + 1, max_depth)
        visited.add(uuid)
    return visited

def get_ochre_documents(uuid):
    """Get an OCHRE document and its descendants.

    Args:
        uuid (str): top-level UUID.

    Returns:
        lxml.ElementTree: a xml document with a <documents> root containing multiple <ochre> trees.
    """
    documents = etree.Element('documents')
    for descendant_uuid in get_uuid_descendants(uuid):
        documents.append(get_ochre(descendant_uuid))
    return etree.ElementTree(documents)

def _get_properties(documents, category, language, labels):
    """Helper function to get a property from one or more OCHRE documents.

    Args:
        documents (lxml.ElementTree): documents to search.
        category (str):               property category. 
        language (str):               property label language.
        labels (list):                list of labels to search.

    Returns:
        dict: a dictionary where keys are labels and values are a set of
              values.
    """
    results = set()
    for property in documents.xpath('//property[value/@category="{}"]'.format(category)):
        label = property.xpath('label/content[@xml:lang="{}"]/string'.format(language))[0].text
        if label in labels:
            results |= set([e.text for e in property.xpath('value')])
    return results

def get_contributors(documents):
    """Get contributors from one or more OCHRE documents.

    Args:
        documents (lxml.ElementTree): documents to search.

    Returns:
        list: a set of names.
    """
    return '\n'.join(
        list(
            _get_properties(
                documents,
                'person',
                'zxx',
                set(('Consultant',))
            )
        )
    )

def get_creators(documents):
    """Get creators from one or more OCHRE documents.

    Args:
        documents (lxml.ElementTree): documents to search.

    Returns:
        list: a set of names.
    """
    return '\n'.join(
        list(
            _get_properties(
                documents,
                'person',
                'zxx',
                set(('Compiler', 'Recorder', 'Researcher'))
            )
        )
    )

def get_subject_languages(documents):
    """Get subject languages from one or more OCHRE documents.

    Args:
        documents (lxml.ElementTree): documents to search.

    Returns:
        list: a set of languages.
    """
    return '\n'.join(
        list(
            _get_properties(
                documents,
                'concept',
                'eng',
                set(('Subject language ... ',))
            )
        )
    )

def get_primary_languages(documents):
    """Get primary languages from one or more OCHRE documents.

    Args:
        documents (lxml.ElementTree): documents to search.

    Returns:
        list: a set of languages.
    """
    return '\n'.join(
        list(
            _get_properties(
                documents,
                'concept',
                'eng',
                set(('Primary language ... ',))
            )
        )
    )

def _get_elements_text(documents, xpath):
    """Helper function to return multiple text elements.

    Args:
        documents (lxml.ElementTree): OCHRE XML to search.
        xpath (str):                  xpath for search.
    
    Returns:
        str: concatenated search results.
    """
    if not xpath.endswith('/text()'):
        xpath = xpath + '/text()'
    return ' '.join([e for e in documents.xpath(xpath)])

def get_title(ochre):
    """Get the title for an item or series.

    Args:
        ochre (lxml.ElementTree): OCHRE XML to search.
    
    Returns:
        str: a title.
    """
    assert ochre.tag == 'ochre'
    return _get_elements_text(
        ochre,
        '/ochre/metadata/item/label/content/string/text()'
    )

def get_description(ochre):
    """Get primary languages from one or more OCHRE documents.

    Args:
        ochre (lxml.ElementTree): OCHRE XML to search.

    Returns:
        str: a description.
    """
    assert ochre.tag == 'ochre'
    return _get_elements_text(
        ochre,
        '/ochre/concept/description/content/string/text()'
    )

def get_identifier(ochre):
    """Get identifier for an item or series.

    Args:
        ochre (lxml.ElementTree): OCHRE XML to search.

    Returns:
        str: an identifier.
    """
    assert ochre.tag == 'ochre'
    return _get_elements_text(
        ochre,
        '/ochre/metadata/item/abbreviation/content/string/text()'
    )

def is_item(ochre):
    """Check whether the document describes an item.

    Args:
        ochre (lxml.ElementTree): OCHRE XML to check.

    Returns:
        bool
    """
    assert ochre.tag == 'ochre'
    n = ochre.xpath('''
        /ochre/concept/context/context/concept[
            text()="Open Language Archive "
        ]/@n
    ''')
    if len(n):
        return int(n[0]) <= -2
    else:
        return False

def is_series(ochre):
    """Check whether the document describes a series.

    Args:
        ochre (lxml.ElementTree): OCHRE XML to check.

    Returns:
        bool
    """
    assert ochre.tag == 'ochre'
    return bool(ochre.xpath('''
        /ochre/concept/context/context/concept[
            @n="-1" and 
            text()="Open Language Archive "
        ]
    '''))

def is_open_language_archive(ochre):
    """Check whether the document describes the Open Language Archive.

    Args:
        ochre (lxml.ElementTree): OCHRE XML to check.

    Returns:
        bool
    """
    assert ochre.tag == 'ochre'
    return bool(
        ochre.xpath('/ochre[@uuid="b9f4fde4-649c-491f-a813-2405cea57915"]')
    )

def get_uuid(ochre):
    """Get the UUID for a document.

    Args:
        ochre (lxml.ElementTree): OCHRE XML to check.

    Returns:
        str: the UUID.
    """
    assert ochre.tag == 'ochre'
    return ochre.xpath('/ochre/@uuid')[0]

def get_parent(ochre):
    """Get the UUID and title for this documents parent.

    Args:
        ochre (lxml.ElementTree): OCHRE XML to search.

    Returns:
        list: containing the parent's UUID and title.
    """
    assert ochre.tag == 'ochre'
    parent = ochre.xpath('/ochre/concept/context/context/concept[@n="-1"]')[0]
    return [
        parent.xpath('@uuid')[0],
        parent.xpath('text()')[0]
    ]

if __name__ == '__main__':
    if len(sys.argv) < 2:
        sys.stdout.write('usage:\n')
        sys.stdout.write(sys.argv[0] + ' {uuid}\n')
        sys.stdout.write('e.g., 9614938c-82b0-4668-a3a5-625f8fa1fad7 (a series)\n')
        sys.stdout.write('or    b9f4fde4-649c-491f-a813-2405cea57915 (the entire Open Language Archive)\n')
        sys.exit()

    uuid = sys.argv[1]
    if not re.match(
        '^[a-z0-9]{8}-[a-z0-9]{4}-[a-z0-9]{4}-[a-z0-9]{4}-[a-z0-9]{12}$',
        uuid
    ):
        sys.stderr.write('malformed UUID?\n')
        sys.exit()
        
    top_level = get_ochre(uuid)
    all_documents = get_ochre_documents(uuid)

    if not is_open_language_archive(top_level):
        sys.stdout.write('PARENT\n')
        parent = get_parent(top_level)
        sys.stdout.write(parent[1] + '\n')
        sys.stdout.write(parent[0] + '\n\n')

    if is_open_language_archive(top_level):
        sys.stdout.write('THE OPEN LANGUAGE ARCHIVE - {}\n\n'.format(get_uuid(top_level)))

    if is_series(top_level):
        sys.stdout.write('SERIES {}\n\n'.format(get_uuid(top_level)))
        for label, func, param in (
            ('TITLE',                    get_title,             top_level),
            ('ALTERNATIVE SERIES TITLE', None,                  None),
            ('IDENTIFIER',               get_identifier,        top_level),
            ('COLLECTION',               None,                  None),
            ('CREATORS',                 get_creators,          all_documents),
            ('CONTRIBUTORS',             get_contributors,      all_documents),
            ('SUBJECT LANGUAGES',        get_subject_languages, all_documents),
            ('PRIMARY LANGUAGES',        get_primary_languages, all_documents),
            ('LOCATION',                 None,                  None),
            ('DATE',                     None,                  None),
            ('DESCRIPTION',              get_description,       top_level),
            ('FORMATS',                  None,                  None)
        ):
            sys.stdout.write(label + '\n')
            sys.stdout.write(func(param) if func is not None else '(not available in OCHRE?)')
            sys.stdout.write('\n\n')

    if is_item(top_level):
        sys.stdout.write('ITEM {}\n\n'.format(get_uuid(top_level)))
        for label, func, param in (
            ('TITLE',                    get_title,             top_level),
            ('IDENTIFIER',               get_identifier,        top_level),
            ('CREATORS',                 get_creators,          top_level),
            ('SUBJECT LANGUAGES',        get_subject_languages, top_level),
            ('PRIMARY LANGUAGES',        get_primary_languages, top_level),
            ('LOCATION',                 None,                  None),
            ('DATE',                     None,                  None),
            ('DESCRIPTION',              None,                  None),
            ('ITEM CONTENT TYPE',        None,                  None),
            ('MEDIA TYPE',               None,                  None),
            ('OTHER MEDIA TYPE',         None,                  None),
        ):
            sys.stdout.write(label + '\n')
            sys.stdout.write(func(param) if func is not None else '(not available in OCHRE?)')
            sys.stdout.write('\n\n')

    children = []
    for concept in top_level.xpath('/ochre/concept/concept'):
        child_uuid = concept.xpath('@uuid')[0].strip()
        child_title = concept.xpath('identification/label/content/string/text()')[0].strip()
        children.append([child_title, child_uuid])

    if children:
        sys.stdout.write('CHILDREN -\n\n')
        for child in children:
            sys.stdout.write(child[0] + '\n')
            sys.stdout.write(child[1] + '\n\n')

#!/usr/bin/env python
"""Usage:
    import.py <XLSX_DIR> <DATABASE>
"""

import os, sqlite3, sys
from openpyxl import load_workbook
from docopt import docopt

# Import FileMaker XLSX dumps into SQLite.

filenames_to_tables = {
    'AC_AssociatedCollections~tog.xlsx': 'AssociatedCollections',
    'ac_cr_CL_Collection.xlsx': 'Collection',
    'cl_TC_TitleCoverage.xlsx': 'CollectionCoverage',
    'ac_cr_CL_CI_CollectionItems.xlsx': 'CollectionItems',
    'cl_TL_TitleLanguages.xlsx': 'CollectionLanguages',
    'ac_CR_CollectionRelated.xlsx': 'CollectionRelated',
    'CollectionTitles.xlsx': 'CollectionTitles',
    'Containers.xlsx': 'Containers',
    'cl_tc_CV_Coverage.xlsx': 'Coverage',
    'ci_EVT_date_DATE.xlsx': 'Date',
    'ci_EVT_Event.xlsx': 'Event',
    'Item.xlsx': 'Item',
    'ItemContributors.xlsx': 'ItemContributors',
    'ItemContributorsList.xlsx': 'ItemContributorsList',
    'IC__ItemsCoverage~tog.xlsx': 'ItemCoverage',
    'IF_ItemFormat~tog.xlsx': 'ItemFormat',
    'cl_itm_LANG_ItemLanguages.xlsx': 'ItemLanguages',
    'IS_ItemSource~tog.xlsx': 'ItemSource',
    'cl_ci_ITEM_ItemTitle.xlsx': 'ItemTitle',
    'cl_itm_LANG_Language.xlsx': 'Language',
    'area_LA_LanguageCoverage.xlsx': 'LanguageCoverage',
    'itm_ci_cl_tl_lang_lcn_LanguageCustomNames.xlsx': 'LanguageCustomNames',
    'lang_LM_LanguageMacro.xlsx': 'LanguageMacro',
    'lang_LN_LanguageNames.xlsx': 'LanguageNames',
    'itm_MD_MaterialData.xlsx': 'MaterialData',
    'itm_if_SF_SoundFormat.xlsx': 'SoundFormat',
    'UNESCOAtlas.xlsx': 'UNESCOAtlas',
    'z_Developer.xlsx': 'z_Developer'
}

if __name__ == '__main__':
    options = docopt(__doc__)

    for k, v in filenames_to_tables.items():
        if not os.path.exists('{}/{}'.format(options['<XLSX_DIR>'], k)):
            print(k)
            sys.exit()
    
    os.remove(options['<DATABASE>'])
    
    con = sqlite3.connect(options['<DATABASE>'])
    c = con.cursor()
    
    for filename in (os.listdir(options['<XLSX_DIR>'])):
        if not filename.endswith('.xlsx'):
            continue
        if not filename in filenames_to_tables.keys():
            continue
    
        print(filename)
    
        wb = load_workbook('{}/{}'.format(options['<XLSX_DIR>'], filename))
        ws = wb.active
        headers = ['"{}"'.format(c.value.strip()) for c in next(ws.rows)]
        print('CREATE TABLE {} ({})'.format(
            filenames_to_tables[filename],
            ', '.join(headers)
        ))
        c.execute(
            'CREATE TABLE {} ({})'.format(
                filenames_to_tables[filename],
                ', '.join(headers)
            )
        )
        con.commit()
        for i, row in enumerate(ws.rows):
            if i == 0:
                continue
            c.execute(
                'INSERT INTO {} VALUES({})'.format(
                    filenames_to_tables[filename],
                    ','.join(['?'] * len(row))
                ),
                [str(c.value) for c in row]
            )
            con.commit()

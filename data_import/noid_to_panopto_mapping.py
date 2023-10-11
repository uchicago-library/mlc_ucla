import json, sqlite3

# This script builds the tab-delimited lookup table that Charles uses to
# resolve ARKs /NOIDs to specific resources. In this case, those resources are 
# Panopto URLs. You may need to rebuild the following JSON files for this
# script:
#
# sqlite_to_triples.item_id_arks.json
#
# This is an associative array, where each key is an item identifier and each
# value is the ARK. The following SQL query retrieves that information
# ark_data.db:
# 
# SELECT original_identifier, ark 
# FROM arks 
# WHERE project='http://lib.uchicago.edu/digital_collections/dma/itemids';
#
# sqlite_to_triples.filenames_to_identifiers.json
#
# This information is available from Panopto. This file should be an
# associative array where each key is the audio file's basename (e.g.,
# aae-gangale-1968-24) and each value is the Panopto identifier (e.g.,
# 71c03823-1f71-40dd-81f5-aef40118962f)

if __name__ == '__main__':
    with open('sqlite_to_triples.item_id_arks.json') as f:
        item_id_arks = json.load(f)
    
    with open('sqlite_to_triples.filenames_to_identifiers.json') as f:
        filenames_to_identifiers = json.load(f)

    con = sqlite3.connect('ucla.db')
    cur = con.cursor()

    sql = "SELECT __kp_ItemID, title FROM ItemTitle WHERE type='Primary';"
    cur.execute(sql)
    for r in cur.fetchall():
        try:
            ark_id = item_id_arks[r[0]]
            noid = ark_id.split('/')[1]
            panopto_id = filenames_to_identifiers[r[1]]
        except KeyError:
            continue
        print('{}\thttps://uchicago.hosted.panopto.com/Panopto/Pages/Viewer.aspx?id={}'.format(
            noid,
            panopto_id
        ))

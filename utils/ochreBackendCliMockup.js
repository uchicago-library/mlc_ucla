const _ = require('lodash');
const fs = require('fs');
const path = require('path');
const request = require('sync-request');

const cacheDir = 'cache';
if (!fs.existsSync(cacheDir)) {
    fs.mkdirSync(cacheDir);
}

/**
 * Return every instance of target_key from data, recursively. 
 *
 * @param {Object} data - data to search.
 * @param {str} targetKey - key to retrieve.
 * @returns {Array} an Array of data structures.
 */
function _findKeys(obj, key, results = []) {
    if (_.isNil(obj)) {
        return results; 
    }
    if (_.isObject(obj)) {
        if (_.has(obj, key)) {
            results.push(_.get(obj, key));
        }
        _.forOwn(obj, value => {
            if (_.isObject(value)) {
                _findKeys(value, key, results);
            }
        });
    } else if (_.isArray(obj)) {
        _.forEach(obj, item => {
            _findKeys(item, key, results);
        });
    }
    return results;
}

/**
 * Helper function to get a property from one or more OCHRE documents.
 *
 * @param {Array} documents - OCHRE documents to search
 * @param {str} category - property category
 * @param {str} language - property label language
 * @param {Array} labels - Array of labels to search
 * @returns {Object} - an object where keys are labels and values are a set of values
 */
function _findProperties(documents, language, labels, returnUuid=false) {
    let propertyContent;
    let propertyLabel;
    let propertyLang;
    let contents;
    let results = new Set();
    _findKeys(documents, 'property').forEach(properties => {
        if (!Array.isArray(properties)) {
            properties = [properties];
        }
        properties.forEach(property => {
            let contents = _.get(property, 'label.content');
            if (!Array.isArray(contents)) {
                contents = [contents];
            }
            contents.forEach(content => {
                propertyLang = _.get(content, 'lang');
                if (propertyLang != language) {
                    return;
                }
                propertyLabel = _.get(content, 'string');
                if (typeof propertyLabel === 'object') {
                    propertyLabel = _.get(propertyLabel, 'content');
                }
                if (!labels.has(propertyLabel)) {
                    return;
                }
                if (returnUuid) {
                    propertyContent = _.get(property, 'value.uuid');
                } else {
                    propertyContent = _.get(property, 'value.content');
                }
                results.add(propertyContent);
            });
        });
    });
    return results;
}

/**
 * Get an OCHRE URL from a UUID.
 *
 * @param {str} uuid - an OCHRE UUID.
 * @returns {str} an OCHRE URL.
 */
function getOchreUrl(uuid) {
    return `https://ochre.lib.uchicago.edu/ochre?uuid=${uuid}&format=json`;
}

/**
 * Simple caching for OCHRE requests. **side effect** Saves JSON documents in
 * CACHE_DIR.
 *
 * @param {str} uuid - an OCHRE UUID
 * @returns {Object} OCHRE data.
 */
function getCachedContent(uuid) {
    const url = getOchreUrl(uuid);
    const cachePath = path.join(cacheDir, `${uuid}.json`);
    if (!fs.existsSync(cachePath)) {
        const data = JSON.parse(
            request('GET', url).getBody('utf8')
        );
        fs.writeFileSync(
            cachePath, 
            JSON.stringify(data, null, 4)
        );
    }
    return JSON.parse(fs.readFileSync(cachePath, 'utf8'));
}

/**
 * Get OCHRE data for a specific UUID.
 *
 * @param {str} uuid - an OCHRE UUID
 * @returns {Object}  OCHRE data.
 */
function getOchre(uuid) {
    return getCachedContent(uuid);
}

/**
 * Get the UUID for a document.
 *
 * @param {Object} OCHRE data.
 * @returns {str} UUID.
 */
function getUuid(ochreData) {
    return _.get(ochreData, 'ochre.uuid', '');
}

/**
 * Check whether the document describes an item.
 * 
 * @param {Object} OCHRE data.
 * @returns {bool}
 */
function isItem(ochreData) {
    let results = _findKeys(ochreData, 'concept');
    for (let i = 0; i < results.length; i++) {
        let concepts = results[i];
        if (!Array.isArray(concepts)) {
            concepts = [concepts];
        }
        for (let j = 0; j < concepts.length; j++) {
            if ('n' in concepts[j] && 
                concepts[j].n <= -3 && 
                'content' in concepts[j] &&
                concepts[j].content == 'Open Language Archive') {
                return true;
            }
        }
    }
    return false;
}

/**
 * Check whether the document describes a series.
 * 
 * @param {Object} OCHRE data.
 * @returns {bool}
 */
function isSeries(ochreData) {
    let results = _findKeys(ochreData, 'concept');
    for (let i = 0; i < results.length; i++) {
        let concepts = results[i];
        if (!Array.isArray(concepts)) {
            concepts = [concepts];
        }
        for (let j = 0; j < concepts.length; j++) {
            if ('n' in concepts[j] && 
                concepts[j].n == -2 && 
                'content' in concepts[j] &&
                concepts[j].content == 'Open Language Archive') {
                return true;
            }
        }
    }
    return false;
}
   
/**
 * Check whether the document describes a series.
 * 
 * @param {Object} OCHRE data.
 * @returns {bool}
 */
function isOpenLanguageArchive(ochreData) {
    return getUuid(ochreData) == 'b9f4fde4-649c-491f-a813-2405cea57915';
}

/**
 * Get the title for an item or series.
 *
 * @param {Object} ochreData - OCHRE data to search.
 * @returns {str} a title.
 */
function getTitle(ochreData) {
    let content = ochreData
        .ochre
        .metadata
        .item
        .label
        .content;

    if (!Array.isArray(content)) {
        content = [content];
    }

    return content
        .filter(content => content.languages == 'eng')
        .map(content => {
            return (typeof content.string === 'object' && 'content' in content.string) ? content.string.content : content.string
        }).join(' ');
}

/**
 * Get the identifier for an item or series.
 *
 * @param {Object} ochreData - OCHRE data to search.
 * @returns {num} an identifier
 */
function getIdentifier(ochreData) {
    try {
        return ochreData
            .ochre
            .metadata
            .item
            .abbreviation
            .content
            .string;
    } catch (err) {
        return '';
    }
}

/**
 * Get the description for an item or series.
 *
 * @param {Object} ochreData - OCHRE data to search.
 * @returns {str} a description
 */
function getDescription(ochreData) {
    try {
        return ochreData
            .ochre
            .concept
            .description
            .content
            .string;
    } catch (err) {
        return '';
    }
}

function getLocations(documents) {
    let physicalMediaUuids = _findProperties(
        documents,
        'eng',
        new Set(['Has physical medium ...']),
        true
    );
    let documentsPhysical = Array.from(physicalMediaUuids).map(uuid => getOchre(uuid));
    let locations = _findProperties(
        documentsPhysical,
        'eng',
        new Set(['Production location ...'])
    );
    return Array.from(locations).join(' ');
}

function getDates(documents) {
    let physicalMediaUuids = _findProperties(
        documents,
        'eng',
        new Set(['Has physical medium ...']),
        true
    );
    let documentsPhysical = Array.from(physicalMediaUuids).map(uuid => getOchre(uuid));
    let dates = _findProperties(
        documentsPhysical,
        'eng',
        new Set(["Date notation"])
    );
    return Array.from(dates).join(' ');
}

/**
 * Get a list of child UUIDs for a given UUID.
 *
 * @param {str} uuid - an OCHRE UUID
 * @returns {list} a list of UUIDs.
 */
function getUuidChildren(uuid) {
    //let ochreData = getOchre(uuid);
    return _.compact(_.map(getOchre(uuid).ochre.concept.concept, 'uuid'));
}

/**
 * Get a set of a UUID and its desendants.
 *
 * @param {str} uuid - an OCHRE UUID
 * @param {Set} visited - descendants already visited
 * @param {num} depth - current search depth
 * @param {num} maxDepth - maximum search depth
 * @returns {Set} a set of descendant UUIDs
 */
function getUuidDescendants(uuid, visited=new Set(), depth=0, maxDepth=5) {
    if (depth <= maxDepth && !visited.has(uuid)) {
        getUuidChildren(uuid).forEach(childUuid => {
            visited = new Set([...visited, ...getUuidDescendants(childUuid, visited, depth + 1, maxDepth)]);
        });
        visited.add(uuid)
    }
    return visited;
}

function getUuidPhysicalMedia(uuid) {
    let documents = getUuidDescendants(uuid);
    return _findProperties(
        documents,
        'eng',
        new Set(['Has physical medium ...'])
    );
}

/**
 * Get an OCHRE document and its descendants.
 *
 * @param {str} uuid - an OCHRE UUID
 * @returns {Array} - an array of OCHRE data structures.
 */
function getOchreDocuments(uuid) {
    return Array.from(getUuidDescendants(uuid)).map(descendantUuid => getOchre(descendantUuid));
}


/**
 * Get contributors from one or more OCHRE documents.
 *
 * @param {Array} documents - OCHRE documents to search.
 * @returns {Array} - an Array of names.
 */
function getContributors(documents) {
    return Array.from(
        _findProperties(documents, 'zxx', new Set(['Consultant']))
    ).join(' ');
}


/**
 * Get creators from one or more OCHRE documents.
 *
 * @param {Array} documents - OCHRE documents to search.
 * @returns {Array} - an Array of names.
 */
function getCreators(documents) {
    return Array.from(
        _findProperties(documents, 'zxx', new Set(['Researcher']))
    ).join(' ');
}

/**
 * Get subject languages from one or more OCHRE documents.
 *
 * @param {Array} documents - OCHRE documents to search.
 * @returns {Array} - Array of languages.
 */
function getSubjectLanguages(documents) {
    return Array.from(
        _findProperties(documents, 'eng', new Set(['Subject language ...']))
    ).join(' ');
}

/**
 * Get primary languages from one or more OCHRE documents.
 *
 * @param {Array} documents - OCHRE documents to search.
 * @returns {Array} - Array of languages.
 */
function getPrimaryLanguages(documents) {
    return Array.from(
        _findProperties(documents, 'eng', new Set(['Primary language ...']))
    ).join(' ');
}

if (process.argv.length >= 3) {
    let ochreChild, ochreDoc, ochreDocuments;
   
    let uuid = process.argv[2]; 

    console.log(uuid);
    if (isItem(ochreDoc)) {
        console.log('an item');
    }
    if (isSeries(ochreDoc)) {
        console.log('a series');
    }
    if (isOpenLanguageArchive(ochreDoc)) {
        console.log('the open language archive.');
    }
    console.log('');

    ochreDoc = getOchre(uuid);
    ochreDocuments = getOchreDocuments(uuid);

    if (isItem(ochreDoc)) {
        [
            ['Title',                    getTitle,            ochreDoc],
            ['Alternative Series Title', undefined,           undefined],
            ['Identifier',               getIdentifier,       ochreDoc],
            ['Collection',               undefined,           undefined],
            ['Creators',                 getCreators,         ochreDocuments],
            ['Contributors',             getContributors,     ochreDocuments],
            ['Indigenous Language',      getSubjectLanguages, ochreDocuments],
            ['Language',                 getPrimaryLanguages, ochreDocuments],
            ['Location',                 getLocations,        ochreDocuments],
            ['Date',                     getDates,            ochreDocuments],
            ['Description',              getDescription,      ochreDoc],
        ].forEach(i => {
            console.log(i[0]);
            if (i[1] === undefined) {
                console.log('not available in OCHRE?');
            } else {
                console.log(i[1](i[2]));
            }
            console.log('');
        });
    }

    if (isSeries(ochreDoc)) {
        [
            ['Title',                    getTitle,            ochreDoc],
            ['Alternative Series Title', undefined,           undefined],
            ['Identifier',               getIdentifier,       ochreDoc],
            ['Collection',               undefined,           undefined],
            ['Creators',                 getCreators,         ochreDocuments],
            ['Contributors',             getContributors,     ochreDocuments],
            ['Indigenous Language',      getSubjectLanguages, ochreDocuments],
            ['Language',                 getPrimaryLanguages, ochreDocuments],
            ['Location',                 getLocations,        ochreDocuments],
            ['Date',                     getDates,            ochreDocuments],
            ['Description',              getDescription,      ochreDoc],
        ].forEach(i => {
            console.log(i[0]);
            if (i[1] === undefined) {
                console.log('not available in OCHRE?');
            } else {
                console.log(i[1](i[2]));
            }
            console.log('');
        });
    }

    console.log('Children');
    console.log('');
    getUuidChildren(uuid).forEach(uuidChild => {
        ochreChild = getOchre(uuidChild);
        console.log(getTitle(ochreChild));
        console.log(uuidChild);
        console.log('');
    });
} else {
    console.log('usage:');
    console.log(process.argv[1] + ' uuid');
    console.log('e.g., 9614938c-82b0-4668-a3a5-625f8fa1fad7 (a series)')
    console.log('or    b9f4fde4-649c-491f-a813-2405cea57915 (the entire Open Language Archive)')
}


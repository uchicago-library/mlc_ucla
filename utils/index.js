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
 * Get the title for an item or series.
 *
 * @param {Object} ochreData - OCHRE data to search.
 * @returns {str} a title.
 */
function getTitle(ochreData) {
    return _.get(ochreData, 'ochre.metadata.item.label.content');
    /*
    contents = document['ochre']['metadata']['item']['label']['content']
    if not type(contents) == list:
        contents = [contents]
    strings = []
    for content in contents:
        string = content['string']
        if type(string) == dict and 'content' in string:
            strings.append(string['content'])
        else:
            strings.append(string)
    return ' '.join(strings)
    */
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
    return Array.from(locations);
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
    return Array.from(dates);
}

/**
 * Get a list of child UUIDs for a given UUID.
 *
 * @param {str} uuid - an OCHRE UUID
 * @returns {list} a list of UUIDs.
 */
function getUuidChildren(uuid) {
    const ochreData = getOchre(uuid);
    return _.compact(_.map(ochreData.ochre.concept.concept, 'uuid'));
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
    );
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
    );
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
    );
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
    );
}

let uuids = [
    '02a80238-e7bf-44b3-bb6a-fd69ac072aa0',
    '05d42aa9-24a3-4374-b643-f12a9f9fda83',
    '17a3e4f5-c82b-4ab4-aecf-e74061d0573a',
    '1e85a27b-f87d-4450-9fb8-1c4fa9e2577e',
    '22f22e4d-3bb9-47d1-87d6-ac6be0636f48',
    '28ea3422-3839-48d2-9a9d-c4f8c884df91',
    '2b0d1c76-28a0-4c3d-a81b-fc9b4f18d09e',
    '3789c341-ea40-47c5-9ec1-75914a383780',
    '464f2c94-8d57-46ae-b293-87d9b0a8faf9',
    '4a284297-779e-40dd-9f43-077fabefd8c5',
    '4aaf8bce-dd20-4b1e-adcb-b6d563510d51',
    '4b376b98-531d-4b6c-9111-294724e9327a',
    '4c5784c2-642b-46cb-be58-c010f1edd93c',
    '4e60bcf9-a98a-4e0d-b800-cd370cb41e17',
    '51bba353-1f3b-4e7c-b96c-80da9768e6e8',
    '532d54b1-6bb0-4272-9b20-5a46debd607f',
    '55978918-369c-4616-b979-082eadf90362',
    '68d37b2b-0fd5-4807-9021-69e8c478ca61',
    '6b91a3a7-22ce-4900-ad33-1bb18ce4e946',
    '6fd362fa-6f60-43ed-a7af-510268ca1a1e',
    '708f039a-b162-4863-ab06-a17967ceb3c8',
    '7a7fb175-2aad-40dd-b658-e3ff3a087bde',
    '7b02e742-ffff-4c46-8c5d-2583547ce404',
    '7c1e7f1c-1e2d-4b24-9bbc-088892712340',
    '7dfca2d9-2b09-4957-a6ff-c10aab6d2396',
    '84d39667-7b1b-441c-a43d-ddb46292d7df',
    '878c5152-f169-4bda-abe1-9619c7f95307',
    '8d52d807-ed97-4aa6-8564-6e343408fb56',
    '928b218e-13bc-429a-842b-0ebfd29dc6cd',
    '9614938c-82b0-4668-a3a5-625f8fa1fad7',
    'a7e578f4-63e4-416d-af94-a6bb4f79145e',
    'ad3eaa18-661e-47ea-86fe-78b4e3439f8d',
    'b0adbed7-a1f1-40d5-8789-9430458a3021',
    'b3cac715-db17-4fd7-8e03-ce21a0424f57',
    'b9f4fde4-649c-491f-a813-2405cea57915',
    'd19ee0b3-dbaf-4ade-a1f4-56230aefe5cd',
    'd95e97a3-be2d-4d34-961a-315b12a44753',
    'e5d20bb5-fd31-4408-8d1a-c605d0882d1b',
    'eb515512-4ee8-4065-baf9-4f9c99edefd8',
    'eb541d61-153a-4ee6-ad2a-dd7b1393b123',
    'ed64041a-4d28-465a-b553-e9f66f9230ee',
    'f3d02c86-7649-4fa5-9a55-1fcd4af45ab4',
    'f568f34b-4f28-41c8-b9df-a4ed46f676ba',
    'f63a0959-a4c3-4bba-972f-ab5ab63029f3',
    'f9b3621f-0bc9-4b7d-92b8-b4a265a724a9'
];
uuids = [
    '9614938c-82b0-4668-a3a5-625f8fa1fad7',
];

console.log(getDates(getOchreDocuments(uuids[0])));    

/*
uuids.forEach(uuid => {
    console.log(getPrimaryLanguages(getOchreDocuments(uuid)));
});
*/

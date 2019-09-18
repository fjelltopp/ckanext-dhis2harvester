import logging
from itertools import izip_longest
import requests
import csv
import json
from base64 import b64encode
from slugify import slugify

from ckanext.dhis2harvester.harvesters.harvest_config_utils import parse_config

log = logging.getLogger(__name__)

DHIS2_API_URL = 'https://play.dhis2.org/2.32.0/api/29/'
DHIS2_API_RESOURCE = 'analytics.json'
DHIS2_ORG_RESOURCE = 'organisationUnits'
DHIS2_PARAMS = 'dimension=dx:lOiynlltFdy;sMTMkudvLCD&dimension=pe:LAST_12_MONTHS' \
               '&filter=ou:ImspTQPwCqd;LEVEL-2&displayProperty=NAME'
DHIS2_METADATA = '&skipData=true'
DHIS2_DATA = '&skipMeta=true'
DHIS2_USERNAME = 'admin'
DHIS2_PASSWORD = 'district'
RESOURCE_FILENAME = 'test_dhis2_resource.csv'


def create_dhis2_headers():
    u_and_p = b"%s:%s" % (DHIS2_USERNAME, DHIS2_PASSWORD)
    u_and_p_b64 = b64encode(u_and_p).decode("ascii")
    return {
        "Content-Type": "application/json",
        "Authorization": "Basic %s" % u_and_p_b64
    }


def __grouper(iterable, n, fillvalue=None):
    "Collect data into fixed-length chunks or blocks"
    # grouper('ABCDEFG', 3, 'x') --> ABC DEF Gxx"
    args = [iter(iterable)] * n
    return izip_longest(*args, fillvalue=fillvalue)


def _get_organisation_details(organisation_ids_list):
    param_fields = 'fields=id,name,coordinates'
    result = dict()
    for chunk in __grouper(organisation_ids_list, 500, fillvalue=''):
        ids_str = '[' + ','.join(chunk) + ']'
        param_filters = 'filter=id:in:%s' % str(ids_str)
        r_org = requests.get(
            DHIS2_API_URL + DHIS2_ORG_RESOURCE + '?paging=false&%s&%s' % (
                param_fields,
                param_filters
            ),
            headers=create_dhis2_headers()
        )
        organisation_units = json.loads(r_org.text)['organisationUnits']

        for org in organisation_units:
            id = org['id']
            name = org['name']
            coordinates = org.get('coordinates', '[]')
            loglon = coordinates.strip('[]').split(',')
            if len(loglon) == 2:
                longitude, latitude = loglon
            else:
                longitude, latitude = ('0.0', '0.0')

            result[id] = {
                'name': name,
                'longitude': longitude,
                'latitude': latitude
            }

    return result


def _parse_dhis2_configuration(config):
    log.info('Got DHIS2 config: \n %s' % config)
    global DHIS2_API_URL, DHIS2_USERNAME, DHIS2_PASSWORD

    DHIS2_API_URL = config['url']
    DHIS2_USERNAME = config['username']
    DHIS2_PASSWORD = config['password']


def _parse_resource_config(config):
    log.info('Got config: \n %s' % config)
    global DHIS2_API_RESOURCE, DHIS2_PARAMS, RESOURCE_FILENAME

    DHIS2_API_RESOURCE = config['apiResource']
    DHIS2_PARAMS = config['resourceParams']
    RESOURCE_FILENAME = "%s_%s.csv" % (slugify(config['ckanPackageTitle']), config['ckanResourceName'])


def fetch_resource(resource_config=None):
    _parse_resource_config(resource_config)
    log.info("Fetching DHIS2 data.")
    r_meta = requests.get(
        DHIS2_API_URL + DHIS2_API_RESOURCE + '?' + DHIS2_PARAMS + DHIS2_METADATA,
        headers=create_dhis2_headers()
    )
    r_data = requests.get(
        DHIS2_API_URL + DHIS2_API_RESOURCE + '?' + DHIS2_PARAMS + DHIS2_DATA,
        headers=create_dhis2_headers()
    )
    data_text = r_data.text
    meta_text = r_meta.text
    data = json.loads(data_text)
    meta = json.loads(meta_text)

    dhis2_items = meta['metaData']['items']
    table_dimensions = meta['metaData']['dimensions']
    dhis2_items_map = dict((k, v['name']) for k, v in dhis2_items.iteritems())

    x_dimensions = table_dimensions['dx']
    organisations_list = table_dimensions['ou']
    organisations_details = _get_organisation_details(organisations_list)

    results = dict()
    for row in data['rows']:
        dx = row[0]
        period = row[1]
        org_id = row[2]
        value = row[3]

        d = results.get(org_id, dict())
        d[dx] = value
        d['period'] = period

        results[org_id] = d

    for org_id, result in results.iteritems():
        org_details = organisations_details[org_id]
        result['facility_name'] = org_details['name']
        result['longitude'] = org_details['longitude']
        result['latitude'] = org_details['latitude']
        result['org_id'] = org_id

    log.info("Writing to csv file.")
    with open(RESOURCE_FILENAME, 'wb') as csvfile:
        cvs_writer = csv.writer(csvfile, delimiter=',',
                                quotechar='"', quoting=csv.QUOTE_MINIMAL)
        value_column_names = [dhis2_items_map[dim_id].replace(u' ', u'-') for dim_id in x_dimensions]
        headers = ['latitude', 'longitude'] + value_column_names + ['period', 'facility name', 'DHIS2 location id']
        headers = [x.encode('utf-8') for x in headers]
        cvs_writer.writerow(headers)
        for org_id, result in results.iteritems():
            row = [result['latitude'], result['longitude']]
            row += [result.get(x, "") for x in x_dimensions]
            row += [result['period'], result['facility_name'], result['org_id']]
            row = [x.encode('utf-8') for x in row]
            try:
                cvs_writer.writerow(row)
            except UnicodeEncodeError:
                log.error("Failed to write csv row %s".format(row), exc_info=True)
    log.info("DHIS2 fetch finished successfully.")


def work(config=None):
    log.info("Parsing config.")
    harvester_config = parse_config(config)
    _parse_dhis2_configuration(harvester_config)
    for resource_config in harvester_config['exportResources']:
        fetch_resource(resource_config)
    return harvester_config

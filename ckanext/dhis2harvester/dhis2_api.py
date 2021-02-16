import json
import urlparse

import logging
from base64 import b64encode

import requests
from requests import ConnectionError
from requests.exceptions import MissingSchema

import request_util

log = logging.getLogger(__name__)


class Dhis2Connection(object):
    DEFAULT_API_VERSION = '26'
    PIVOT_TABLES_RESOURCE = 'reportTables.json?' \
                            'fields=id,displayName~rename(name),created,lastUpdated,access,title,description,user&' \
                            'order=name:asc&paging=false'
    PIVOT_TABLES_KEY_NAME = "reportTables"
    PIVOT_TABLES_CSV_RESOURCE = 'analytics.csv?' \
                                'dimension=dx:{data_elements}&' \
                                'dimension=pe:{periods}&' \
                                'dimension=co&' \
                                'dimension=ou:{organisation_units}&' \
                                'displayProperty=NAME&' \
                                'hierarchyMeta=true&' \
                                'outputIdScheme=UID'
    PIVOT_TABLE_KEYS = ["lastUpdated", "created", "id", "name"]
    SECURITY_LOGIN_ACTION = 'dhis-web-commons-security/login.action'
    ORG_UNIT_RESOURCE = "organisationUnits?paging=false&fields=id,name"

    def __init__(self, url, username=None, password=None, auth_token=None, api_version=DEFAULT_API_VERSION):
        self.url = self.__add_trailing_slash(url)
        self.api_version = api_version
        self.api_url = self.__api_url(self.url, self.api_version)
        self.username = username
        self.password = password
        self.auth_token = auth_token

    def __str__(self):
        return "Dhis2Connection(api_url={self.api_url}, username={self.username})".format(self=self)

    def __add_trailing_slash(self, url):
        if not url.endswith('/'):
            url += '/'
        return url

    def __api_url(self, url, version):
        url = self.__add_trailing_slash(url)
        url += 'api/'
        if version:
            url += version + "/"
        return url

    def __create_dhis2_headers(self, headers=None):
        if headers is None:
            headers = {}
        u_and_p = b"%s:%s" % (self.username, self.password)
        u_and_p_b64 = b64encode(u_and_p).decode("ascii")
        headers.update({
            "Content-Type": "application/json",
            "Authorization": "Basic %s" % u_and_p_b64
        })
        return headers

    def __create_auth_cookie(self):
        if not self.auth_token:
            self.get_auth_token()
        return {
            'JSESSIONID': self.auth_token,
            'SESSION': self.auth_token
        }

    def __response_validation(self, msg, r):
        ok = request_util.check_if_response_is_ok(r)
        if not ok:
            raise (Dhis2ConnectionError(msg))
        elif "<html class=\"loginPage\"" in r.text:
            msg_ = "Failed with DHIS2 authentication"
            log.debug(msg_)
            raise (Dhis2ConnectionError(msg))

    def test_connection(self):
        try:
            cookies = self.__create_auth_cookie()
            test_url = urlparse.urljoin(self.api_url, 'organisationUnits')
            r = requests.get(test_url, cookies=cookies)
            self.__response_validation("Failed to authenticate to DHIS2", r)
            return True
        except ConnectionError:
            msg_ = "Failed to connect to DHIS2 with provided credentials."
            log.debug(msg_)
            raise (Dhis2ConnectionError(msg_))
        except MissingSchema as ms:
            log.debug(ms.message)
            raise (Dhis2ConnectionError(ms.message))

    def get_details(self):
        return self.url, self.api_version, self.get_auth_token()

    def get_auth_token(self):
        if not self.auth_token:
            session = requests.session()
            url_ = urlparse.urljoin(self.url, self.SECURITY_LOGIN_ACTION)
            data_ = {"j_username": self.username, "j_password": self.password}
            session.post(url_, data=data_)
            cookie = session.cookies.get_dict()
            if 'JSESSIONID' in cookie:
                self.auth_token = cookie['JSESSIONID']
            elif 'SESSION' in cookie:
                self.auth_token = cookie['SESSION']
            else:
                raise Dhis2ConnectionError("Failed to get DHIS2 auth token")
        return self.auth_token

    def get_pivot_tables(self):
        url_ = urlparse.urljoin(self.api_url, self.PIVOT_TABLES_RESOURCE)
        r = requests.get(url_, cookies=self.__create_auth_cookie())
        self.__response_validation("Failed to get pivot tables information", r)
        try:
            pivot_tables = r.json().get(self.PIVOT_TABLES_KEY_NAME)
        except ValueError:
            raise Dhis2ConnectionError("Failed to decode response for pivot table")
        result = []
        for table in pivot_tables:
            result.append({k: v for k, v in table.iteritems() if k in self.PIVOT_TABLE_KEYS})
        return result

    def _get_pivot_table_meta(self, pivot_table_id):
        url_ = urlparse.urljoin(self.api_url, "{}/{}".format(self.PIVOT_TABLES_KEY_NAME, pivot_table_id))
        r = requests.get(url_, cookies=self.__create_auth_cookie())
        self.__response_validation("Failed to get pivot table information for pivot table {}".format(pivot_table_id), r)
        try:
            pivot_table_meta = r.json()
        except ValueError:
            raise Dhis2ConnectionError("Failed to decode response for pivot table")
        return pivot_table_meta

    def get_pivot_table_columns(self, pivot_table_id):
        pivot_table_meta = self._get_pivot_table_meta(pivot_table_id)
        # categories combos metadata
        cc_url_ = urlparse.urljoin(self.api_url, "metadata?categoryCombos:fields=id,name,categoryOptionCombos")
        coc_url_ = urlparse.urljoin(self.api_url, "metadata?categoryOptionCombos:fields=id,name")
        cc_r = requests.get(cc_url_, cookies=self.__create_auth_cookie())
        coc_r = requests.get(coc_url_, cookies=self.__create_auth_cookie())
        category_combos_meta = cc_r.json()["categoryCombos"]
        category_option_combos_meta = coc_r.json()["categoryOptionCombos"]
        category_option_combos_map = {c['id']: c['name'] for c in category_option_combos_meta}
        category_combos_map = {}
        for category_combo in category_combos_meta:
            c_id = category_combo['id']
            category_options = category_combo['categoryOptionCombos']
            options = {option['id']: category_option_combos_map[option['id']] for option in category_options}
            category_combos_map[c_id] = options
        # data elements metadata
        de_url_ = urlparse.urljoin(self.api_url, "metadata?dataElements:fields=id,name,categoryCombo")
        de_r = requests.get(de_url_, cookies=self.__create_auth_cookie())
        data_elements_meta = {d['id']: {'name': d['name'], 'category_combo': d['categoryCombo']['id']} for d in
                              de_r.json()["dataElements"]}

        def get_data_elements_config(d_id_, data_elements_map=None):
            if data_elements_map is None:
                data_elements_map = {}
            if d_id_ not in data_elements_map:
                d_name_ = data_elements_meta[d_id_]['name']
                data_element_category_options_ = []
                cc_id_ = data_elements_meta[d_id_]['category_combo']
                category_options_ = category_combos_map[cc_id_]
                for co_id, co_name in category_options_.iteritems():
                    data_element_category_options_.append({
                        "id": "-".join([d_id_, co_id]),
                        "name": " / ".join([d_name_, co_name])
                    })
                data_elements_map[d_id_] = data_element_category_options_
            return data_elements_map[d_id_]

        result = []
        for column in pivot_table_meta.get("dataDimensionItems"):
            if column["dataDimensionItemType"] == 'INDICATOR':
                result.append({
                    'id': column['indicator']['id'],
                    'type': 'indicator',
                    'name': 'indicator_{}'.format(column['indicator']['id'])
                })
            elif column["dataDimensionItemType"] == 'DATA_ELEMENT':
                d_id_ = column['dataElement']['id']
                columns = get_data_elements_config(d_id_)
                for c in columns:
                    result.append({
                        'id': c['id'],
                        'type': 'data_element',
                        'name': c['name']
                    })
        return result

    def get_pivot_table_configuration(self, pivot_table_id):
        pivot_table_metadata = self._get_pivot_table_meta(pivot_table_id)
        ou_levels = [x['id'] for x in pivot_table_metadata.get('organisationUnits', [])]
        meta_ou_levels = pivot_table_metadata.get('organisationUnitLevels', [])
        ou_levels += ["LEVEL-{}".format(ou_level) for ou_level in meta_ou_levels]
        meta_periods = pivot_table_metadata.get('periods', [])
        if len(meta_periods) < 1:
            periods = ['LAST_YEAR', 'THIS_YEAR']
        else:
            periods = [x['id'] for x in pivot_table_metadata['periods']]
        display_name = pivot_table_metadata['displayName']
        return {
            "name": display_name,
            "ou_levels": ou_levels,
            "periods": periods
        }

    def get_pivot_table_csv_resource(self, data_elements, ou_levels, periods):
        des = ";".join(data_elements)
        ous = ";".join(ou_levels)
        ps = ";".join(periods)
        return self.PIVOT_TABLES_CSV_RESOURCE.format(data_elements=des, periods=ps, organisation_units=ous)

    def get_organisation_unit_name_id_map(self):
        ou_url_ = urlparse.urljoin(self.api_url, self.ORG_UNIT_RESOURCE)
        ou_r = requests.get(ou_url_, cookies=self.__create_auth_cookie())
        self.__response_validation("Failed to get organisation unit information", ou_r)
        ou_list = json.loads(ou_r.text)['organisationUnits']
        id_name_map = {ou['id']: ou['name'] for ou in ou_list}

        return id_name_map

    def get_api_resource(self, api_resource):
        url_ = urlparse.urljoin(self.api_url, api_resource)
        response = requests.get(url_, cookies=self.__create_auth_cookie())
        return response


class Dhis2ConnectionError(Exception):
    pass

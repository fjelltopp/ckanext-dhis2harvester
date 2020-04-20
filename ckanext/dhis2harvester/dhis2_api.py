import urllib
import urlparse

import logging
from base64 import b64encode

import requests
from requests import ConnectionError

import request_util

log = logging.getLogger(__name__)

class Dhis2Connection(object):

    PIVOT_TABLES_RESOURCE = 'reportTables.json?fields=id,displayName~rename(name),created,lastUpdated,access,title,description,user&order=name:asc&paging=false'
    PIVOT_TABLES_KEY_NAME = "reportTables"
    PIVOT_TABLE_KEYS = ["lastUpdated", "created", "id", "name"]

    def __init__(self, url, username, password):
        self.url = self.__update_url_str(url)
        self.username = username
        self.password = password

    def __update_url_str(self, url):
        if not url.endswith('/'):
            url += '/'
        if not url.endswith('api/'):
            url += 'api/'
        return url

    def __create_dhis2_headers(self, headers={}):
        u_and_p = b"%s:%s" % (self.username, self.password)
        u_and_p_b64 = b64encode(u_and_p).decode("ascii")
        headers.update({
            "Content-Type": "application/json",
            "Authorization": "Basic %s" % u_and_p_b64
        })
        return headers

    def __response_validation(self, msg, r):
        ok = request_util.check_if_response_is_ok(r)
        if not ok:
            raise (Dhis2ConnectionError(msg))

    def test_connection(self):
        try:
            r = requests.get(self.url, headers=self.__create_dhis2_headers())
            self.__response_validation("Failed to get valid response", r)
            return True
        except ConnectionError:
            msg_ = "Failed to connect to DHIS2 with provided credentials."
            log.debug(msg_)
            raise (Dhis2ConnectionError(msg_))

    def get_pivot_tables(self):
        url_ = urlparse.urljoin(self.url, self.PIVOT_TABLES_RESOURCE)
        r = requests.get(url_, headers=self.__create_dhis2_headers())
        self.__response_validation("Failed to get pivot tables information", r)
        pivot_tables = r.json().get(self.PIVOT_TABLES_KEY_NAME)
        result = []
        for table in pivot_tables:
            result.append({k: v for k, v in table.iteritems() if k in self.PIVOT_TABLE_KEYS})
        return result





class Dhis2ConnectionError(Exception):
    pass

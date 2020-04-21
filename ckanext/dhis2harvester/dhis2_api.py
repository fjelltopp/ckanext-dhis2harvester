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
    SECURITY_LOGIN_ACTION = 'dhis-web-commons-security/login.action'

    def __init__(self, url, username=None, password=None, auth_token=None):
        self.url = self.__add_trailing_slash(url)
        self.api_url = self.__api_url(self.url)
        self.username = username
        self.password = password
        self.auth_token = auth_token

    def __add_trailing_slash(self, url):
        if not url.endswith('/'):
            url += '/'
        return url

    def __api_url(self, url, version=None):
        url = self.__add_trailing_slash(url)
        if version:
            url += version + "/"
        url += 'api/'
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
            'JSESSIONID': self.auth_token
        }

    def __response_validation(self, msg, r):
        ok = request_util.check_if_response_is_ok(r)
        if not ok:
            raise (Dhis2ConnectionError(msg))

    def test_connection(self):
        try:
            headers = self.__create_dhis2_headers()
            r = requests.get(self.api_url, headers=headers)
            self.__response_validation("Failed to get valid response", r)
            return True
        except ConnectionError:
            msg_ = "Failed to connect to DHIS2 with provided credentials."
            log.debug(msg_)
            raise (Dhis2ConnectionError(msg_))

    def get_auth_token(self):
        if not self.auth_token:
            session = requests.session()
            url_ = urlparse.urljoin(self.url, self.SECURITY_LOGIN_ACTION)
            data_ = {"j_username": self.username, "j_password": self.password}
            session.post(url_, data=data_)
            cookie = session.cookies.get_dict()
            if 'JSESSIONID' not in cookie:
                raise Dhis2ConnectionError("Failed to get DHIS2 auth token")
            self.auth_token = cookie['JSESSIONID']
        return self.auth_token

    def get_pivot_tables(self):
        url_ = urlparse.urljoin(self.api_url, self.PIVOT_TABLES_RESOURCE)
        # r = requests.get(url_, headers=self.__create_dhis2_headers())
        r = requests.get(url_, cookies=self.__create_auth_cookie())
        self.__response_validation("Failed to get pivot tables information", r)
        pivot_tables = r.json().get(self.PIVOT_TABLES_KEY_NAME)
        result = []
        for table in pivot_tables:
            result.append({k: v for k, v in table.iteritems() if k in self.PIVOT_TABLE_KEYS})
        return result


class Dhis2ConnectionError(Exception):
    pass

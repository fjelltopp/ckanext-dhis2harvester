import logging
from flask import Blueprint, request, Response, jsonify
from dhis2_api import Dhis2Connection, Dhis2ConnectionError
import ckan.lib.helpers as h

log = logging.getLogger(__name__)

dhis2_data = Blueprint(
    u'dhis2data',
    __name__,
    url_prefix='/dhis2_data'
)

def pivot_tables():
    dhis2_conn = __create_dhis2_conn()
    try:
        dhis2_conn.test_connection()
    except Dhis2ConnectionError:
        return {'message': 'Failed to connect to DHIS2 with provided credentials'}, 400
    # get pivot tables info
    pivot_tables = dhis2_conn.get_pivot_tables()
    return jsonify(pivot_tables), 200


def __create_dhis2_conn():
    r_body = request.json
    # get dhis2 credentials
    dhis2_c = r_body.get('dhis2_connection')
    dhis2_url = dhis2_c.get(u'url')
    dhis2_cred = dhis2_c.get(u'credentials')
    dhis2_username = dhis2_cred.get(u'username')
    dhis2_password = dhis2_cred.get(u'password')
    # get dhis2 connection
    dhis2_conn = Dhis2Connection(dhis2_url, dhis2_username, dhis2_password)
    return dhis2_conn


def test_connection():
    dhis2_conn = __create_dhis2_conn()
    try:
        dhis2_conn.test_connection()
    except Dhis2ConnectionError:
        return __response('Failed to connect to DHIS2 with provided credentials', 400)
    return __response('Connection to DHIS2 successful', 200)


def __response(msg, status):
    return jsonify({'message': msg}), status


def hello():
    return "{'message': 'hello'}", 200

dhis2_data.add_url_rule(
    u'/pivot_tables',
    view_func=pivot_tables,
    methods=['POST']
)

dhis2_data.add_url_rule(
    u'/test_connection',
    view_func=test_connection,
    methods=['POST']
)

dhis2_data.add_url_rule(
    u'/hello',
    view_func=hello,
    methods=['GET']
)

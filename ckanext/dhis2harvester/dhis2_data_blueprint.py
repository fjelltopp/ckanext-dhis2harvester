import logging
from flask import Blueprint, request, Response, jsonify
from dhis2_api import Dhis2Connection, Dhis2ConnectionError
import ckan.lib.helpers as h

log = logging.getLogger(__name__)

dhis2_data = Blueprint(
    u'dhis2_data',
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
    return __response(result=pivot_tables, status=200)


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
        return __response(error='Failed to connect to DHIS2 with provided credentials', status=400)
    return __response(status=200)


def __response(help="", result=None, error=None, status=200):
    if result and error:
        raise ValueError("Expecting error only when no result.")
    body_ = {
        'help': help
    }
    if not error:
        body_['success'] = True
        if result:
            body_['result'] = result
    else:
        body_['success'] = False
        if error:
            body_['error'] = error
    return jsonify(body_), status


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

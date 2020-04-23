import logging
from flask import Blueprint, request, Response, jsonify, redirect, url_for
import ckan.lib.helpers as h
import ckan.plugins.toolkit as t
from collections import defaultdict
from dhis2_api import Dhis2Connection, Dhis2ConnectionError

log = logging.getLogger(__name__)

ui_blueprint = Blueprint(
    u'dhis2_harvester',
    __name__,
    url_prefix='/dhis2_harvester'
)


def _validate_required_fields(required_fields, errors=None):
    if errors is None:
        errors = defaultdict(list)
    for field in required_fields:
        if not request.form.get(field['name']):
            errors[field['name']].append(
                '{} is a required field'.format(field['label'])
            )
    return errors


def _validate_dhis2_connection(dhis2_conn, errors=None):
    if errors is None:
        errors = defaultdict(list)
    try:
        dhis2_conn.test_connection()
    except Dhis2ConnectionError:
        error_message = 'Failed to connect to DHIS2, please check credentials'
        errors['dhis2_password'] = [error_message]
        errors['dhis2_username'] = [error_message]
        errors['dhis2_api_url'] = [error_message]
    return errors


def __get_dhis_conn():
    dhis2_url = request.form.get('dhis2_api_url')
    dhis2_username = request.form.get('dhis2_username')
    dhis2_password = request.form.get('dhis2_password')
    dhis2_conn = Dhis2Connection(dhis2_url, dhis2_username, dhis2_password)
    return dhis2_conn


def pivot_tables_new():
    if request.method == 'POST':
        # Define DHIS2 connection details
        data = request.form.to_dict()
        form_stage = data['action']
        stage_number = int(form_stage.split('_')[-1])
        if stage_number > 1:
            dhis2_conn_ = __get_dhis_conn()
        elif stage_number > 2:
            pass
        if "back" in form_stage:
            to_form_stage = form_stage.split('.')[-1]
            data['action'] = to_form_stage
            return t.render(
                'source/pivot_table_new.html',
                {'data': data, 'errors': {}}
            )
        elif form_stage == 'pivot_table_new_1':
            required_fields = [
                {'label': 'DHIS2 Password', 'name': 'dhis2_password'},
                {'label': 'DHIS2 Username', 'name': 'dhis2_username'},
                {'label': 'DHIS2 API Endpoint URL', 'name': 'dhis2_api_url'}
            ]
            errors = _validate_required_fields(required_fields)
            if errors:
                data['action'] = 'pivot_table_new_1'
                return t.render(
                    'source/pivot_table_new.html',
                    {'data': data, 'errors': errors}
                )
            dhis2_conn_ = __get_dhis_conn()
            errors = _validate_dhis2_connection(dhis2_conn_)
            if errors:
                data['action'] = 'pivot_table_new_1'
                return t.render(
                    'source/pivot_table_new.html',
                    {'data': data, 'errors': errors}
                )
            pivot_tables = dhis2_conn_.get_pivot_tables()
            data['pivot_tables'] = pivot_tables
            data['action'] = "pivot_table_new_2"
            return t.render(
                'source/pivot_table_new.html',
                {'data': data, 'errors': {}}
            )
        elif form_stage == 'pivot_table_new_2':
            data['action'] = "pivot_table_new_3"
            return t.render(
                'source/pivot_table_new.html',
                {'data': data, 'errors': {}}
            )
        elif form_stage == 'pivot_table_new_3':
            data['action'] = "pivot_table_new_4"
            return t.render(
                'source/pivot_table_new.html',
                {'data': data, 'errors': {}}
            )
        elif form_stage == 'pivot_table_new_4':
            data['action'] = "pivot_table_new_4"
            return t.render(
                'source/pivot_table_new.html',
                {'data': data, 'errors': {}}
            )
    else:
        return t.render(
            'source/pivot_table_new.html',
            {'data': {'action': 'pivot_table_new_1'}, 'errors': {}}
        )


ui_blueprint.add_url_rule(
    u'/pivot_tables/new',
    view_func=pivot_tables_new,
    methods=['GET', 'POST']
)

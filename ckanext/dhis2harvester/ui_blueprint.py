import logging
from flask import Blueprint, request, Response, jsonify, redirect, url_for
from dhis2_api import Dhis2Connection, Dhis2ConnectionError
import ckan.lib.helpers as h
import ckan.plugins.toolkit as t
import json
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


def _validate_dhis2_connection(errors=None):
    if errors is None:
        errors = defaultdict(list)
    dhis2_url = request.form.get('dhis2_api_url')
    dhis2_username = request.form.get('dhis2_username')
    dhis2_password = request.form.get('dhis2_password')
    dhis2_conn = Dhis2Connection(dhis2_url, dhis2_username, dhis2_password)
    try:
        dhis2_conn.test_connection()
    except Dhis2ConnectionError:
        error_message = 'Failed to connect to DHIS2, please check credentials'
        errors['dhis2_password'] = [error_message]
        errors['dhis2_username'] = [error_message]
        errors['dhis2_api_url'] = [error_message]
    return errors


def pivot_tables_new():
    if request.method == 'POST':
        # Validate that all required fields are supplied
        required_fields = [
            {'label': 'DHIS2 Password', 'name': 'dhis2_password'},
            {'label': 'DHIS2 Username', 'name': 'dhis2_username'},
            {'label': 'DHIS2 API Endpoint URL', 'name': 'dhis2_api_url'}
        ]
        errors = _validate_required_fields(required_fields)
        if errors:
            return t.render(
                'source/pivot_table_new.html',
                {'data': request.form, 'errors': errors}
            )
        # Validate that we can connect to DHIS2
        errors = _validate_dhis2_connection()
        if errors:
            return t.render(
                'source/pivot_table_new.html',
                {'data': request.form, 'errors': errors}
            )
        # If validation passes, redirect to next step.
        return redirect(url_for(
            'dhis2_harvester.pivot_tables_choose'
        ))
    else:
        # If a simple GET request is made, render an empty form
        return t.render(
            'source/pivot_table_new.html',
            {'data': {}, 'errors': {}}
        )


def pivot_tables_choose():
    log.warning(request.method)
    return t.render(
        'source/pivot_table_choose.html',
        {'data': {}, 'errors': {}}
    )


ui_blueprint.add_url_rule(
    u'/pivot_tables/new',
    view_func=pivot_tables_new,
    methods=['GET', 'POST']
)

ui_blueprint.add_url_rule(
    u'/pivot_tables/choose',
    view_func=pivot_tables_choose,
    methods=['GET', 'POST']
)

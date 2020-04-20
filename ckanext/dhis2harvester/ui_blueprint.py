import logging
from flask import Blueprint, request, Response, jsonify, redirect, url_for
from dhis2_api import Dhis2Connection, Dhis2ConnectionError
import ckan.lib.helpers as h
import ckan.plugins.toolkit as t
import json
from collections import defaultdict

log = logging.getLogger(__name__)

ui_blueprint = Blueprint(
    u'dhis2_harvester',
    __name__,
    url_prefix='/dhis2_harvester'
)


def hello():
    return "{'message': 'hello'}", 200


def new_pivot_tables_1(methods=['GET', 'POST']):

    if request.method == 'POST':
        # Validate that all required fields are supplied
        errors = defaultdict(list)
        required_fields = [
            {'label': 'DHIS2 Password', 'name': 'dhis2_password'},
            {'label': 'DHIS2 Username', 'name': 'dhis2_username'},
            {'label': 'DHIS2 API Endpoint URL', 'name': 'dhis2_api_url'}
        ]
        for field in required_fields:
            if not request.form.get(field['name']):
                errors[field['name']].append(
                    '{} is a required field'.format(field['label'])
                )
        if errors:
            return t.render(
                'source/pivot_table_new.html',
                {'data': request.form, 'errors': errors}
            )
        # TODO: Validate that we can connect to DHIS2
        # If validation passes, redirect to next step.
        return redirect(url_for(
            'dhis2_harvester.new_pivot_tables_2'
        ))

    else:
        return t.render(
            'source/pivot_table_new.html',
            {'data': {}, 'errors': {}}
        )


def new_pivot_tables_2(methods=['GET', 'POST']):
    log.warning(request.method)
    return t.render(
        'source/pivot_table_choose.html',
        {'data': {}, 'errors': {}}
    )


ui_blueprint.add_url_rule(
    u'/pivot_tables/new',
    view_func=new_pivot_tables_1,
    methods=['GET', 'POST']
)

ui_blueprint.add_url_rule(
    u'/pivot_tables/choose',
    view_func=new_pivot_tables_2,
    methods=['GET', 'POST']
)

ui_blueprint.add_url_rule(
    u'/hello',
    view_func=hello,
    methods=['GET']
)

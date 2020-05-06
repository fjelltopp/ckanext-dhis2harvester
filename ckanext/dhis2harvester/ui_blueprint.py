import json
import os

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


def pivot_tables_new():
    if request.method == 'POST':
        # Define DHIS2 connection details
        data, dhis2_conn_, form_stage = __data_initialization()

        if "back" in form_stage:
            return __go_back(data, form_stage)
        elif form_stage == 'pivot_table_new_1':
            return __dhis2_connection_stage(data)
        elif form_stage == 'pivot_table_new_2':
            return __pivot_table_select_stage(data, dhis2_conn_)
        elif form_stage == 'pivot_table_new_3':
            return __configure_table_columns_stage(data)
        elif form_stage == 'pivot_table_new_4':
            return __summary_stage(data)
    else:
        return t.render(
            'source/pivot_table_new.html',
            {'data': {'action': 'pivot_table_new_1'}, 'errors': {}}
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


def __summary_stage(data):
    #### Create complete configuration for DHIS2 Pivot tables:
    log.debug(data)
    dhis2_api_url = data['dhis2_api_url']
    resource_name = 'Pivot Table Export'
    dataset_name = 'Pivot Table Export'
    pt_id = data['pivot_table_id']
    column_config = defaultdict(dict)
    for k in data:
        split = k.split('_', 1)
        if len(split) > 1:
            prefix_ = split[0]
            id = split[1]
            if prefix_ == 'col':
                column_config[id]['col'] = data[k]
            elif prefix_ == 'age':
                column_config[id]['age'] = data[k]
            elif prefix_ == 'gender':
                column_config[id]['gender'] = data[k]
    harvester_config = {
        'dhis2_api_url': dhis2_api_url,
        'pivot_tables': [
            {
                'pivot_table_id': pt_id,
                'resource_name': resource_name,
                'dataset_name': dataset_name,
                'column_config': column_config
            }
        ]
    }

    data['action'] = "pivot_table_new_4"
    return t.render(
        'source/pivot_table_new.html',
        {'data': data, 'errors': {}}
    )


def __configure_table_columns_stage(data):
    # read col_ age_ gender_ inputs
    log.debug(data)
    data['action'] = "pivot_table_new_4"
    return t.render(
        'source/pivot_table_new.html',
        {'data': data, 'errors': {}}
    )


def __pivot_table_select_stage(data, dhis2_conn_):
    log.debug("Pivot table select stage submit data: " + str(data))
    data['action'] = "pivot_table_new_3"
    return t.render(
        'source/pivot_table_new.html',
        {'data': data, 'errors': {}}
    )


def __dhis2_connection_stage(data):
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
    try:
        pivot_tables = dhis2_conn_.get_pivot_tables()
    except Dhis2ConnectionError as e:
        errors = {'dhis2_api_url': ["Failed to fetch pivot table data from this DHIS2 instance."]}
        data['action'] = 'pivot_table_new_1'
        return t.render(
            'source/pivot_table_new.html',
            {'data': data, 'errors': errors}
        )
    pivot_tables_options = [{'value': pivot_table['id'], 'text': pivot_table['name']} for pivot_table in pivot_tables]
    data['pivot_tables'] = pivot_tables_options
    data['action'] = "pivot_table_new_2"
    return t.render(
        'source/pivot_table_new.html',
        {'data': data, 'errors': {}}
    )


def __go_back(data, form_stage):
    to_form_stage = form_stage.split('.')[-1]
    data['action'] = to_form_stage
    return t.render(
        'source/pivot_table_new.html',
        {'data': data, 'errors': {}}
    )


def __data_initialization():
    data = request.form.to_dict()
    form_stage = data.get('action', 'pivot_table_new_1')
    dhis2_conn_ = __get_dhis_conn()
    try:
        dhis2_conn_.test_connection()
    except Dhis2ConnectionError:
        dhis2_conn_ = None
    if not dhis2_conn_:
        return data, dhis2_conn_, form_stage

    # get column config template
    dir_path = os.path.dirname(os.path.realpath(__file__))
    with open(os.path.join(dir_path, 'config/column_configs_template.json'), 'r') as f:
        column_config_template_ = json.loads(f.read())
        log.debug("Read JSON column config: " + str(column_config_template_))
        data['column_config'] = column_config_template_
        target_types_ = [{'text': type_d['name'], 'value': type_id}
                         for type_id, type_d in column_config_template_.iteritems()]
        data['target_types'] = target_types_
    pivot_tables_ = dhis2_conn_.get_pivot_tables()
    pivot_tables_options = [{'value': pt['id'], 'text': pt['name']} for pt in pivot_tables_]
    p_id_to_name_ = {pt['id']: pt['name'] for pt in pivot_tables_}
    data['pivot_tables'] = pivot_tables_options
    pivot_table_ids = request.form.getlist('pivot_table_id')
    pivot_table_types = request.form.getlist('pivot_table_target_type')
    if pivot_table_ids and pivot_table_types:
        # selected_pivot_tables
        selected_pivot_tables = [{'id': x[0], 'type': x[1], 'text': p_id_to_name_[x[0]]} for x in zip(pivot_table_ids, pivot_table_types)]
        data['selected_pivot_tables'] = selected_pivot_tables
        log.debug("Selected pivot tables: " + str(selected_pivot_tables))

        # pivot table columns
        pivot_table_columns_ = {}
        for pt_id in pivot_table_ids:
            columns_ = dhis2_conn_.get_pivot_table_columns(pt_id)
            pt_columns_ = [{'value': c['id'], 'text': c['name']} for c in columns_]
            pivot_table_columns_[pt_id] = pt_columns_
        data['pivot_table_columns'] = pivot_table_columns_
        log.debug("Pivot table columns: " + str(pivot_table_columns_))
    return data, dhis2_conn_, form_stage


ui_blueprint.add_url_rule(
    u'/pivot_tables/new',
    view_func=pivot_tables_new,
    methods=['GET', 'POST']
)

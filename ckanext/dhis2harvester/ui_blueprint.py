import json
from six import StringIO
import logging
import requests
import pandas as pd
from flask import Blueprint, request, abort
from ckan.common import _, g
import ckan.lib.helpers as h
import ckan.plugins.toolkit as t
import ckanext.harvest.helpers as harvest_helpers
import ckanext.harvest.utils as harvest_utils
from ckan.logic import ValidationError
from collections import defaultdict

from ckanext.dhis2harvester.dhis2_api import Dhis2Connection, Dhis2ConnectionError
from ckanext.dhis2harvester.harvesters import operations

log = logging.getLogger(__name__)

ui_blueprint = Blueprint(
    u'dhis2_harvester',
    __name__,
    url_prefix='/dhis2_harvester'
)

METADATA_SEPARATOR = ';'


def pivot_tables_new():
    if request.method == 'POST':
        return __ui_state_machine()
    else:
        data = {'action': 'pivot_table_new_1'}
        return __render_pivot_table_template(data, {})


def pivot_tables_edit(harvest_source_id):
    harvest_source = harvest_helpers.get_harvest_source(harvest_source_id)
    __set_harvest_globals(harvest_source)
    if request.method == 'POST':
        return __ui_state_machine(harvest_source)
    else:
        harvest_config = json.loads(harvest_source['config'])
        (dhis2_url, dhis2_api_version, dhis2_auth_token) = \
            __get_dhis2_connection_details_from_harvest_source(harvest_config)

        data = {
            'action': 'pivot_table_new_1',
            'column_values': harvest_config['column_values'],
            'selected_pivot_tables': harvest_config['selected_pivot_tables'],
            'area_id_map_url': harvest_config['area_id_map_url'],
            'period_conversion_type': harvest_config.get('period_conversion_type'),
            'geo_location': harvest_config.get('geo_location'),
            'dhis2_url': dhis2_url,
            'dhis2_api_version': dhis2_api_version,
            'dhis2_auth_token': dhis2_auth_token,
            'title': harvest_source['title'],
            'description': harvest_source['notes'],
            'name': harvest_source['name'],
            'owner_org': harvest_source['owner_org']
        }
        __get_pt_configs(data)

        log.debug("Editing harvest source: " + harvest_source_id)
        return __render_pivot_table_template(data, {}, edit_configuration=True, harvest_source=harvest_source)


def __set_harvest_globals(harvest_source):
    g.owner_org = h.get_organization(harvest_source['owner_org'])


def __get_dhis2_connection_details_from_harvest_source(harvest_config):
    dhis2_conn = __get_dhis_conn(harvest_config)
    url, api_version, auth_token = dhis2_conn.get_details()
    try:
        dhis2_conn.test_connection()
    except Dhis2ConnectionError:
        log.debug("Outdated auth token for: {}".format(dhis2_conn))
        return url, api_version, ''
    return url, api_version, auth_token


def pivot_tables_refresh(harvest_source_id):
    harvest_source = harvest_helpers.get_harvest_source(harvest_source_id)
    __set_harvest_globals(harvest_source)
    harvester_name = harvest_source['name']
    source_config = json.loads(harvest_source['config'])
    data = request.form.to_dict()
    # Both view and submit are POST requests due to ckan-harvest flow
    # if data is empty display the form
    if data:
        dhis2_conn_ = __get_dhis_conn(request.form)
        errors = _validate_dhis2_connection(dhis2_conn_)
        if errors:
            _data = {'owner_org': h.get_organization(harvest_source['owner_org'])}
            return t.render(
                'source/pivot_table_refresh.html',
                {'data': _data, 'harvest_source': harvest_source, 'errors': errors}
            )
        source_config.update({
            'dhis2_url': data['dhis2_url'],
            'dhis2_api_version': data['dhis2_api_version'],
            'dhis2_auth_token': dhis2_conn_.get_auth_token()
        })
        harvest_source['config'] = json.dumps(source_config)
        try:
            t.get_action("harvest_source_update")({}, harvest_source)
        except ValidationError as e:
            log.error("An error occurred: {}".format(str(e.error_dict)))
            raise e
        try:
            harvest_utils.create_job(harvest_source_id)
        except ValidationError as e:
            log.error("An error occurred: {}".format(str(e)))
            raise e
        _flash_source_refresh_success()
        return h.redirect_to('harvest_admin', id=harvester_name)
    else:
        data = {}
        (dhis2_url, dhis2_api_version, dhis2_auth_token) = __get_dhis2_connection_details_from_harvest_source(
            source_config)
        if dhis2_auth_token:
            try:
                harvest_utils.create_job(harvest_source_id)
                _flash_source_refresh_success()
                return h.redirect_to('harvest_admin', id=harvester_name)
            except ValidationError as e:
                log.error("An error occurred: {}".format(str(e)))
        data['dhis2_url'] = dhis2_url
        data['dhis2_api_version'] = dhis2_api_version
        data['dhis2_auth_token'] = dhis2_auth_token
        data['owner_org'] = h.get_organization(harvest_source['owner_org'])
        return t.render(
            'source/pivot_table_refresh.html',
            {'data': data, 'harvest_source': harvest_source, 'errors': {}}
        )


def _flash_source_refresh_success():
    h.flash_success(_("Import of data from DHIS will start soon. Click on import to bring in the most recent program data."))


def __ui_state_machine(harvest_source=None):
    edit_configuration = harvest_source is not None
    data = {}
    kwargs = {
        "edit_configuration": edit_configuration,
        "harvest_source": harvest_source
    }
    try:
        data, dhis2_conn_, form_stage = __data_initialization(edit_configuration=edit_configuration)
    except Dhis2ConnectionError as e:
        h.flash_error('Failed to connect DHIS2: {}'.format(e.message))
        return __dhis2_connection_stage(data, **kwargs)

    if "back" in form_stage:
        return __go_back(data, form_stage, **kwargs)
    elif form_stage == 'pivot_table_new_1':
        return __dhis2_connection_stage(data, **kwargs)
    elif form_stage == 'pivot_table_new_2':
        return __pivot_table_select_stage(data, **kwargs)
    elif form_stage == 'pivot_table_new_3':
        return __configure_table_columns_stage(data, **kwargs)
    elif form_stage == 'pivot_table_new_4':
        return __summary_stage(data, harvest_source=harvest_source)
    elif form_stage == 'pivot_table_new_save':
        return __save_or_update_harvest_source(data, harvest_source=harvest_source)
    else:
        abort(400, "Unrecognised action")


def _validate_required_fields(required_fields, errors=None):
    if errors is None:
        errors = defaultdict(list)
    for field in required_fields:
        if not request.form.get(field['name']):
            errors[field['name']].append(
                '{} is a required field'.format(field['label'])
            )
    return errors


def _validate_area_map_resource_id(field_name, errors=None):
    if errors is None:
        errors = defaultdict(list)
    if not request.form.get(field_name):
        return errors
    r_id = request.form.get(field_name)
    try:
        t.get_action('resource_show')({}, {"id": r_id})
    except Exception as e:
        log.debug("Failed to get resource {}", e)
        errors[field_name].append(
            "Couldn't get the resource. Please verify resource id is correct."
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
        errors['dhis2_url'] = [error_message]
    return errors


def __get_dhis_conn(data_dict):
    dhis2_kwargs = {}
    dhis2_url = data_dict.get('dhis2_url')
    dhis2_kwargs['api_version'] = data_dict.get('dhis2_api_version')
    _overwrite_auth_token = data_dict.get('overwrite-auth-token')
    _auth_token = data_dict.get('dhis2_auth_token')
    if not _auth_token or _overwrite_auth_token:
        dhis2_kwargs['username'] = data_dict.get('dhis2_username')
        dhis2_kwargs['password'] = data_dict.get('dhis2_password')
    else:
        dhis2_kwargs['auth_token'] = data_dict.get('dhis2_auth_token')
    dhis2_conn = Dhis2Connection(dhis2_url, **dhis2_kwargs)
    return dhis2_conn


def __summary_stage(data, errors=None, harvest_source=None):
    kwargs = {
        "harvest_source": harvest_source
    }
    if not errors:
        errors = {}
    data['action'] = "pivot_table_new_4"
    return __render_pivot_table_template(data, errors, **kwargs)


def __save_harvest_source(data):
    data_dict, harvester_name = __prepare_harvester_details(data)
    try:
        t.get_action("harvest_source_create")({}, data_dict)
    except ValidationError as e:
        log.error("An error occurred: {}".format(str(e.error_dict)))
        raise e
    log.info("Harvest source {} created".format(harvester_name))

    return h.redirect_to('harvest_admin', id=harvester_name)


def __update_harvest_source(data):
    data_dict, harvester_name = __prepare_harvester_details(data)
    try:
        t.get_action("harvest_source_update")({}, data_dict)
    except ValidationError as e:
        log.error("An error occurred: {}".format(str(e.error_dict)))
        raise e
    return h.redirect_to('harvest_admin', id=harvester_name)


def __save_or_update_harvest_source(data, harvest_source=None):
    area_id_map_url = data.get('area_id_map_url')
    if area_id_map_url:
        current_user = g.userobj
        api_key = current_user.apikey
        try:
            headers = {'Authorization': api_key}
            area_csv = requests.get(area_id_map_url, headers=headers, timeout=30)
            if area_csv.status_code != 200:
                raise ValueError("Error while getting response, code {}. Are you sure the file is public?".format(
                    area_csv.status_code))
            else:
                data['area_id_map_owner'] = current_user.name
        except Exception as e:
            errors = {"area_id_map_url": [_("Failed to download the area id map csv file."), e.message]}
            return __summary_stage(data, errors, harvest_source=harvest_source)
        try:
            csv_stream = StringIO(area_csv.text)
            pd.read_csv(csv_stream)
        except Exception:
            errors = {"area_id_map_url": [_("Incorrect csv file format.")]}
            return __summary_stage(data, errors, harvest_source=harvest_source)

    try:
        if harvest_source:
            return __update_harvest_source(data)
        else:
            return __save_harvest_source(data)
    except Exception as e:
        log.exception(e.message)
        h.flash_error('Error while saving the harvest source: {}'.format(e.message))
        return __summary_stage(data, harvest_source=harvest_source)


def __prepare_harvester_details(data):
    source_config = {
        'column_values': data['column_values'],
        'selected_pivot_tables': data['selected_pivot_tables'],
        'dhis2_url': data['dhis2_url'],
        'dhis2_api_version': data['dhis2_api_version'],
        'dhis2_auth_token': data['dhis2_auth_token'],
        'area_id_map_url': data.get('area_id_map_url'),
        'area_id_map_owner': data.get('area_id_map_owner'),
        'period_conversion_type': data.get('period_conversion_type'),
        'geo_location': data.get('geo_location'),
    }
    harvester_name = data['name']
    active_ = data.get('state', 'active') == 'active'
    data_dict = {
        "name": harvester_name,
        "url": data['dhis2_url'],
        "source_type": 'dhis2-pivot-tables',
        "title": data['title'],
        "notes": data['notes'],
        "active": active_,
        "state": data.get('state', 'active'),
        "owner_org": data['owner_org'],
        "frequency": 'MANUAL',
        "config": json.dumps(source_config)
    }
    return data_dict, harvester_name


def __configure_table_columns_stage(data, edit_configuration=False, harvest_source=None):
    kwargs = {
        "edit_configuration": edit_configuration,
        "harvest_source": harvest_source
    }
    data['action'] = "pivot_table_new_4"
    return __render_pivot_table_template(data, {}, **kwargs)


def __pivot_table_select_stage(data, edit_configuration=False, harvest_source=None):
    kwargs = {
        "edit_configuration": edit_configuration,
        "harvest_source": harvest_source
    }
    errors = _validate_area_map_resource_id('area_map_resource_id')
    if errors:
        return __render_pivot_table_template(data, errors, **kwargs)
    data['action'] = "pivot_table_new_3"
    errors = {}
    return __render_pivot_table_template(data, errors, **kwargs)


def __render_pivot_table_template(data, errors, **kwargs):
    params_ = {'data': data, 'errors': errors}
    params_.update(kwargs)
    return t.render(
        'source/pivot_table_new.html',
        params_
    )


def __dhis2_connection_stage(data, edit_configuration=False, harvest_source=None):
    kwargs = {
        "edit_configuration": edit_configuration,
        "harvest_source": harvest_source
    }
    if not data['dhis2_auth_token']:
        required_fields = [
            {'label': 'DHIS2 Password', 'name': 'dhis2_password'},
            {'label': 'DHIS2 Username', 'name': 'dhis2_username'},
            {'label': 'DHIS2 API Endpoint URL', 'name': 'dhis2_url'}
        ]
        errors = _validate_required_fields(required_fields)
        if errors:
            data['action'] = 'pivot_table_new_1'
            return __render_pivot_table_template(data, errors, **kwargs)
    dhis2_conn_ = __get_dhis_conn(request.form)
    errors = _validate_dhis2_connection(dhis2_conn_)
    if errors:
        data['action'] = 'pivot_table_new_1'
        return __render_pivot_table_template(data, errors, **kwargs)
    data['dhis2_username'] = ''
    data['dhis2_password'] = ''
    data['dhis2_auth_token'] = dhis2_conn_.get_auth_token()

    try:
        pivot_tables = dhis2_conn_.get_pivot_tables()
    except Dhis2ConnectionError:
        errors = {'dhis2_url': ["Failed to fetch pivot table data from this DHIS2 instance."]}
        data['action'] = 'pivot_table_new_1'
        return __render_pivot_table_template(data, errors, **kwargs)
    pivot_tables_options = [{'value': pivot_table['id'], 'text': pivot_table['name']} for pivot_table in pivot_tables]
    data['pivot_tables'] = pivot_tables_options
    data['action'] = "pivot_table_new_2"
    return __render_pivot_table_template(data, {}, **kwargs)


def __go_back(data, form_stage, edit_configuration=False, harvest_source=None):
    kwargs = {
        "edit_configuration": edit_configuration,
        "harvest_source": harvest_source
    }
    to_form_stage = form_stage.split('.')[-1]
    data['action'] = to_form_stage
    return __render_pivot_table_template(data, {}, **kwargs)


def __data_initialization(edit_configuration=False):
    data = request.form.to_dict()
    form_stage = data.get('action', 'pivot_table_new_1')

    data['selected_pivot_tables'] = json.loads(data.get('selected_pivot_tables', '{}'))
    data['column_values'] = json.loads(data.get('column_values', '{}'))
    __get_pt_configs(data)

    dhis2_conn_ = __get_dhis_conn(data)
    try:
        dhis2_conn_.test_connection()
    except Dhis2ConnectionError:
        dhis2_conn_ = None
    if not dhis2_conn_:
        return data, dhis2_conn_, form_stage
    data['dhis2_username'] = ''
    data['dhis2_password'] = ''
    data['dhis2_auth_token'] = dhis2_conn_.get_auth_token()

    pivot_tables_ = dhis2_conn_.get_pivot_tables()
    pivot_tables_options = [{'value': pt['id'], 'text': pt['name']} for pt in pivot_tables_]
    p_id_to_name_ = {pt['id']: pt['name'] for pt in pivot_tables_}
    data['pivot_tables'] = pivot_tables_options
    pivot_table_ids = request.form.getlist('pivot_table_id')
    pivot_table_types = request.form.getlist('pivot_table_target_type')
    if pivot_table_ids and pivot_table_types:
        # selected_pivot_tables
        selected_pivot_tables = [{'id': x[0], 'type': x[1], 'text': p_id_to_name_[x[0]]} for x in
                                 zip(pivot_table_ids, pivot_table_types)]
        data['selected_pivot_tables'] = selected_pivot_tables
        log.debug("Selected pivot tables: " + str(selected_pivot_tables))
    elif not pivot_table_ids:
        pivot_table_ids = [x['id'] for x in data['selected_pivot_tables']]

    # pivot table columns
    pivot_table_columns_ = {}
    pivot_table_with_indicators_ = {}
    for pt_id in pivot_table_ids:
        columns_ = dhis2_conn_.get_pivot_table_columns(pt_id)
        pivot_table_with_indicators_[pt_id] = any([c['type'] == 'indicator' for c in columns_])
        data_el_only_ = [c for c in columns_ if c['type'] == 'data_element']
        pt_columns_ = [{'value': de['id'], 'text': de['name']} for de in data_el_only_]
        pivot_table_columns_[pt_id] = pt_columns_
    data['pivot_table_columns'] = pivot_table_columns_
    data['pivot_table_with_indicators'] = pivot_table_with_indicators_
    log.debug("Pivot table columns: " + str(pivot_table_columns_))

    # selected column values
    column_values = []
    for pt in data['selected_pivot_tables']:
        pt_id = pt['id']
        pt_column_values_ = {
            'id': pt_id,
        }

        def __new_column():
            return {
                'enabled': False,
                'operation': operations.ADD
            }

        columns_ = defaultdict(__new_column)
        for k in data:
            if k.startswith("target_column{_}{id}".format(_=METADATA_SEPARATOR, id=pt_id)):
                c_id_ = k.split(METADATA_SEPARATOR)[-1]
                target_column_ = data[k]
                columns_[c_id_]['target_column'] = target_column_
            elif k.startswith("category{_}{id}".format(_=METADATA_SEPARATOR, id=pt_id)):
                tc_, c_id_ = k.split(METADATA_SEPARATOR)[-2:]
                tc_value_ = data[k]
                if 'categories' not in columns_[c_id_]:
                    columns_[c_id_]['categories'] = {}
                columns_[c_id_]['categories'][tc_] = tc_value_
            elif k.startswith("column_enabled{_}{id}".format(_=METADATA_SEPARATOR, id=pt_id)):
                c_id_ = k.split(METADATA_SEPARATOR)[-1]
                columns_[c_id_]['enabled'] = True
            elif k.startswith("negative{_}{id}".format(_=METADATA_SEPARATOR, id=pt_id)):
                c_id_ = k.split(METADATA_SEPARATOR)[-1]
                columns_[c_id_]['operation'] = operations.SUBTRACT

        columns_list_ = []
        for c_id, c_details in columns_.iteritems():
            c_details['id'] = c_id
            columns_list_.append(c_details)

        if edit_configuration and not columns_list_:
            old_column_values = {cv['id']: cv['columns'] for cv in data['column_values']}
            if pt_id in old_column_values:
                pt_column_values_['columns'] = old_column_values[pt_id]
            else:
                pt_column_values_['columns'] = []
        else:
            pt_column_values_['columns'] = columns_list_
        column_values.append(pt_column_values_)
    data['column_values'] = column_values
    log.debug("Column values: " + str(column_values))

    return data, dhis2_conn_, form_stage


def __get_pt_configs(data):
    # get column config template
    from config.column_configs_template import TARGET_TYPES
    data['column_config'] = TARGET_TYPES
    target_types_ = [{'text': type_d['name'], 'value': type_id}
                     for type_id, type_d in TARGET_TYPES.iteritems()]
    data['target_types'] = target_types_


ui_blueprint.add_url_rule(
    u'/pivot_tables',
    view_func=pivot_tables_new,
    methods=['GET', 'POST']
)

ui_blueprint.add_url_rule(
    u'/pivot_tables/<harvest_source_id>',
    view_func=pivot_tables_edit,
    methods=['GET', 'POST']
)

ui_blueprint.add_url_rule(
    u'/pivot_tables/refresh/<harvest_source_id>',
    view_func=pivot_tables_refresh,
    methods=['POST']
)


@ui_blueprint.app_template_filter()
def json_dumps(json_obj):
    if not json_obj:
        return '{}'
    return json.dumps(json_obj)

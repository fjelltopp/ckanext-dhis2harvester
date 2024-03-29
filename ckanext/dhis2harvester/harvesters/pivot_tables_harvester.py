import logging
import requests
import six
from ckan.lib import uploader

from ckanext.harvest.harvesters import HarvesterBase
from ckanext.harvest.model import (HarvestObject,
                                   HarvestGatherError, HarvestObjectError)
import ckanext.dhis2harvester.dhis2_api as dhis2_api
import ckanext.dhis2harvester.harvesters.operations as operations
import ckanext.dhis2harvester.dhis2_periods as dhis2_periods
from ckanext.dhis2harvester.config.column_configs_template import TARGET_TYPES as PT_TARGET_TYPES
from ckan.logic import NotFound
from ckan import model
from ckan.plugins import toolkit as t
from werkzeug.datastructures import FileStorage as FlaskFileStorage
from slugify import slugify
import pandas as pd
import uuid
import json

import sys

from six import StringIO
log = logging.getLogger(__name__)


class PivotTablesHarvester(HarvesterBase):
    _save_gather_error = HarvestGatherError.create
    _save_object_error = HarvestObjectError.create

    def info(self):
        return {
            'name': 'dhis2-pivot-tables',
            'title': 'DHIS2 Pivot Tables Harvester',
            'description': 'Harvests pivot tables data from DHIS2',
        }

    def _area_id_map_harvest_object_data(self, area_id_map_url, area_id_map_owner):
        if not area_id_map_url or not area_id_map_owner:
            return
        area_map_owner = area_id_map_owner
        user = model.User.get(area_map_owner)
        api_key = user.apikey
        headers = {'Authorization': api_key}
        area_csv = requests.get(area_id_map_url, headers=headers, timeout=5)
        if area_csv.status_code != 200:
            raise ValueError("Error while getting response, code {}".format(area_csv.status_code))
        return area_csv.text

    def gather_stage(self, harvest_job):
        """
        The gather stage will receive a HarvestJob object and will be
        responsible for:
            - gathering all the necessary objects to fetch on a later.
              stage (e.g. for a CSW server, perform a GetRecords request)
            - creating the necessary HarvestObjects in the database, specifying
              the guid and a reference to its job. The HarvestObjects need a
              reference date with the last modified date for the resource, this
              may need to be set in a different stage depending on the type of
              source.
            - creating and storing any suitable HarvestGatherErrors that may
              occur.
            - returning a list with all the ids of the created HarvestObjects.
            - to abort the harvest, create a HarvestGatherError and raise an
              exception. Any created HarvestObjects will be deleted.

        :param harvest_job: HarvestJob object
        :returns: A list of HarvestObject ids
        """
        log.debug('Gather stage for harvest job: %r', harvest_job.id)
        if not harvest_job:
            log.error('No harvest job received')
            return None
        if harvest_job.source.config is None:
            self._save_gather_error('Unable to get source config for: {}'.format(harvest_job.source), harvest_job)
            return False

        obj_ids = []

        config = json.loads(harvest_job.source.config)
        dhis2_connection = self._get_dhis2_connection(config)
        organisation = t.get_action('harvest_source_show')({}, {'id': harvest_job.source_id})["organization"]
        country_name = organisation['name']

        try:
            dhis2_connection.test_connection()
        except dhis2_api.Dhis2ConnectionError as e:
            self._save_gather_error('Unable to get connection to dhis2: {}: {}'.format(dhis2_connection, e),
                                    harvest_job)
            return None
        area_id_map_url = config['area_id_map_url']
        area_id_map_owner = config['area_id_map_owner']
        title_ = six.text_type(harvest_job.source.title)
        output_dataset_name_prefix = '{} Output'.format(title_)
        period_conversion_type = config.get('period_conversion_type')
        for pt in config['column_values']:
            pt_id = pt['id']
            pt_type = {x['id']: x for x in config['selected_pivot_tables']}[pt_id]['type']
            pt_target_type = PT_TARGET_TYPES[pt_type]
            pt_config = dhis2_connection.get_pivot_table_configuration(pt_id)
            data_elements = [c['id'].split('-')[0] for c in pt['columns'] if '-' in c['id']]
            indicators = [c['id'] for c in pt['columns'] if '-' not in c['id']]
            csv_resource_name = dhis2_connection.get_pivot_table_csv_resource(
                data_elements, pt_config['ou_levels'], pt_config['periods'])
            csv_indicator_resource_name = dhis2_connection.get_pivot_table_csv_indicators_resource(
                indicators, pt_config['ou_levels'], pt_config['periods'])
            output_dataset_name = "{} {}".format(output_dataset_name_prefix, pt_target_type['shortName'])
            harvest_object_data = {
                'dhis2_url': config['dhis2_url'],
                'dhis2_api_version': config['dhis2_api_version'],
                'dhis2_auth_token': dhis2_connection.get_auth_token(),
                'dhis2_api_full_resource': csv_resource_name,
                'dhis2_api_full_indicator_resource': csv_indicator_resource_name,
                'output_dataset_name': output_dataset_name,
                'output_resource_name': '{} {} {}'.format(
                    country_name,
                    pt_target_type['shortName'],
                    pt_config['name']
                ),
                'pivot_table_id': pt_id,
                'pivot_table_column_config': pt['columns'],
                'output_tags': pt_target_type.get("tags", []),
                'pt_type': pt_type,
                'output_columns': pt_target_type.get("columns", []),
                'period_conversion_type': period_conversion_type,
                'geo_location': config.get('geo_location')
            }
            if area_id_map_url:
                try:
                    area_csv_str = self._area_id_map_harvest_object_data(area_id_map_url, area_id_map_owner)
                except Exception as e:
                    self._save_gather_error('Failed to process area id csv resource: {}, {}'
                                            .format(area_id_map_url, e), harvest_job)
                    return None
                harvest_object_data['area_id_map_csv_str'] = area_csv_str

            obj = HarvestObject(guid="pivot_table",
                                job=harvest_job,
                                content=json.dumps(harvest_object_data))
            obj.save()
            obj_ids.append(obj.id)
        return obj_ids

    def _get_dhis2_connection(self, config):
        dhis2_url = config['dhis2_url']
        dhis2_api_version = config['dhis2_api_version']
        dhis2_auth_token = config['dhis2_auth_token']
        return dhis2_api.Dhis2Connection(dhis2_url, api_version=dhis2_api_version, auth_token=dhis2_auth_token)

    def fetch_stage(self, harvest_object):
        """
        The fetch stage will receive a HarvestObject object and will be
        responsible for:
            - getting the contents of the remote object (e.g. for a CSW server,
              perform a GetRecordById request).
            - saving the content in the provided HarvestObject.
            - creating and storing any suitable HarvestObjectErrors that may
              occur.
            - returning True if everything is ok (ie the object should now be
              imported), "unchanged" if the object didn't need harvesting after
              all (ie no error, but don't continue to import stage) or False if
              there were errors.

        :param harvest_object: HarvestObject object
        :returns: True if successful, 'unchanged' if nothing to import after
                  all, False if not successful
        """
        log.debug('Fetch stage for harvest object: %r', harvest_object.id)

        if not harvest_object:
            log.error('No harvest object received')
            return False

        if harvest_object.content is None:
            self._save_object_error('Empty content for object {}'.format(harvest_object.id), harvest_object, 'Fetch')
            return False

        content = json.loads(harvest_object.content)

        if 'csv' in content:
            # csv stream already present skip to import stage
            return True

        pivot_table_id = content.get("pivot_table_id", "Unknown")

        dhis2_connection = self._get_dhis2_connection(content)
        try:
            dhis2_connection.test_connection()
        except dhis2_api.Dhis2ConnectionError as e:
            self._save_object_error_error(
                'Unable to get connection to dhis2: {}: {}'.format(dhis2_connection, e.message),
                harvest_object, 'Fetch')
            return None
        dhis2_api_full_resource = content.get('dhis2_api_full_resource')
        dhis2_api_full_indicator_resource = content.get('dhis2_api_full_indicator_resource')
        pivot_table_column_config = content['pivot_table_column_config']
        try:
            if dhis2_api_full_resource is not None:
                pt_csv = dhis2_connection.get_api_resource(dhis2_api_full_resource)
                csv_stream = StringIO(pt_csv.text)
                pt_df = pd.read_csv(csv_stream, sep=",", encoding='utf-8')
            else:
                pt_df = pd.DataFrame()
        except dhis2_api.Dhis2ConnectionError as e:
            self._save_object_error_error('Unable to get dhis2 data elements: {}: {}: {}'
                                          .format(dhis2_api_full_resource, dhis2_connection, e.message),
                                          harvest_object, 'Fetch')
            return None
        except Exception as e:
            log.exception("Failed to parse data element resources for pivot table.")
            self._save_object_error_error('Unable to get dhis2 data elements: {}: {}: {}'
                                          .format(dhis2_api_full_resource, dhis2_connection, e.message),
                                          harvest_object, 'Fetch')
            return None

        try:
            if dhis2_api_full_indicator_resource is not None:
                pt_indicator_csv = dhis2_connection.get_api_resource(dhis2_api_full_indicator_resource)
                csv_indicator_stream = StringIO(pt_indicator_csv.text)
                pt_indicator_df = pd.read_csv(csv_indicator_stream, sep=",", encoding='utf-8')
            else:
                pt_indicator_df = pd.DataFrame()
        except dhis2_api.Dhis2ConnectionError as e:
            self._save_object_error_error('Unable to get dhis2 data: {}: {}: {}'
                                          .format(dhis2_api_full_resource, dhis2_connection, e.message),
                                          harvest_object, 'Fetch')
            return None
        except Exception as e:
            log.exception("Failed to parse indicator resources for pivot table.")
            self._save_object_error_error('Unable to get dhis2 data elements: {}: {}: {}'
                                          .format(dhis2_api_full_resource, dhis2_connection, e.message),
                                          harvest_object, 'Fetch')
            return None
        try:
            _category_column = 'Category option combo'
            _data_element_column = 'Data'
            # indicators have no category compinations, using 'indicator' as cc value
            pt_indicator_df[_category_column] = 'indicator'
            pt_df = pd.concat([pt_df, pt_indicator_df])
            try:
                ou_id_name_map = dhis2_connection.get_organisation_unit_name_id_map()
            except dhis2_api.Dhis2ConnectionError as e:
                self._save_object_error('Unable to get dhis2 org unit data: {}: {}'.format(dhis2_connection, e.message),
                                        harvest_object, 'Fetch')
                return None
            _org_unit_col = 'Organisation unit'
            _area_name_col = 'area_name'
            _area_id_col = 'area_id'
            pt_df[_area_name_col] = pt_df[_org_unit_col].map(ou_id_name_map)
            pt_df[_area_id_col] = pt_df[_org_unit_col]

            _pt_type = content['pt_type']
            _period_convert_type = content.get('period_conversion_type')
            _period_col = 'Period'
            _output_period_col = dhis2_periods.period_column_name(_pt_type)
            pt_df[_period_col] = pt_df[_period_col].map(dhis2_periods.period_convert_function(_period_convert_type))
            if dhis2_periods.should_map_into_calendar_quarter(_pt_type):
                pt_df[_output_period_col] = \
                    pt_df[_period_col].map(dhis2_periods.calendar_quarter_from_dhis2_period_string)
            elif dhis2_periods.should_map_into_year(_pt_type):
                pt_df[_output_period_col] = \
                    pt_df[_period_col].map(dhis2_periods.year_from_dhis2_period_string)
            else:
                pt_df[_output_period_col] = pt_df[_period_col]

            categories_map = {}
            disabled_categories = []
            for cc in pivot_table_column_config:
                if not cc.get('enabled', False):
                    disabled_categories.append(cc['id'])
                target_column_ = cc['target_column']
                if not isinstance(target_column_, list):
                    target_column_ = [target_column_]
                # making indicators mapping compatible with "de-cc" concatinations
                if '-' in cc['id']:
                    category_key = cc['id']
                else:
                    category_key = f"{cc['id']}-indicator"
                categories_map[category_key] = {
                    "target_column": target_column_,
                    "categories": cc['categories'],
                    "operation": cc.get('operation', operations.ADD)
                }

            pt_df['de_cat'] = pt_df[_data_element_column] + "-" + pt_df[_category_column]
            # drop disabled categories
            pt_df = pt_df[~pt_df['de_cat'].isin(disabled_categories)]
            # drop disabled indicators (no category column)
            pt_df = pt_df[~pt_df[_data_element_column].isin(disabled_categories)]
            # map categories
            _cat_cols = set()
            _data_cols = set()
            _index_to_drop = []
            for i, row in pt_df.iterrows():
                de_cat = row['de_cat']
                try:
                    c = categories_map[de_cat]
                except KeyError:
                    _index_to_drop.append(i)
                    continue
                _factor = operations.aggregation_factor_for_operation(c["operation"])
                for tc in c['target_column']:
                    _data_cols.add(tc)
                    pt_df.loc[i, tc] = _factor * row['Value']
                for cat, cat_val in six.iteritems(c['categories']):
                    _cat_cols.add(cat)
                    pt_df.loc[i, cat] = cat_val
            pt_df = pt_df.drop(_index_to_drop)
            if pt_df.empty:
                self._save_object_error(
                    'Failed to process DHIS2 pivot table: {} @ {}. No data matching column configuration.'
                    .format(pivot_table_id, dhis2_connection),
                    harvest_object, 'Fetch')
                return None
            # map area ids
            if 'area_id_map_csv_str' in content:
                area_id_map_csv_str = content['area_id_map_csv_str']
                area_csv_stream = StringIO(area_id_map_csv_str)
                area_map_df = pd.read_csv(area_csv_stream)
                if 'map_id' in list(area_map_df):
                    mapping_column_name = 'map_id'
                elif 'dhis2_id' in list(area_map_df):
                    mapping_column_name = 'dhis2_id'
                else:
                    self._save_object_error('Invalid format of area id map: {} @ {}'
                                            .format(pivot_table_id, dhis2_connection),
                                            harvest_object, 'Fetch')
                    return None

                pt_df['area_id'] = pt_df['area_id'].replace(area_map_df.set_index(mapping_column_name)['area_id'])
            # aggregate by area_id, categories
            aggregation_config = {data_col: "sum" for data_col in _data_cols}

            def concat_area_names(area_names_series):
                return ','.join([name for name in area_names_series.unique()])
            aggregation_config[_area_name_col] = lambda x: concat_area_names(x)

            pt_df = (pt_df.groupby([_area_id_col, _output_period_col] + list(_cat_cols))
                     .agg(aggregation_config)
                     .reset_index()
                     )
            # create final columns output
            pt_df = pt_df[[_area_id_col, _area_name_col, _output_period_col] + list(_cat_cols) + list(_data_cols)]
            pt_df.sort_values(by=[_area_id_col, _output_period_col]).reset_index(drop=True)
            add_missing_columns_from_target_table_config(pt_df, content['output_columns'])
        except Exception:
            exc_type, value, traceback = sys.exc_info()
            self._save_object_error('Failed to process DHIS2 pivot table: {} @ {}, {}:{}'
                                    .format(pivot_table_id, dhis2_connection, exc_type, value),
                                    harvest_object, 'Fetch')
            return None

        # save csv output for import stage
        content['csv'] = pt_df.to_csv(index=False, float_format='%.f', encoding='utf-8')
        harvest_object.content = json.dumps(content)
        return True

    def import_stage(self, harvest_object):
        """
        The import stage will receive a HarvestObject object and will be
        responsible for:
            - performing any necessary action with the fetched object (e.g.
              create, update or delete a CKAN package).
              Note: if this stage creates or updates a package, a reference
              to the package should be added to the HarvestObject.
            - setting the HarvestObject.package (if there is one)
            - setting the HarvestObject.current for this harvest:
               - True if successfully created/updated
               - False if successfully deleted
            - setting HarvestObject.current to False for previous harvest
              objects of this harvest source if the action was successful.
            - creating and storing any suitable HarvestObjectErrors that may
              occur.
            - creating the HarvestObject - Package relation (if necessary)
            - returning True if the action was done, "unchanged" if the object
              didn't need harvesting after all or False if there were errors.

        NB You can run this stage repeatedly using 'paster harvest import'.

        :param harvest_object: HarvestObject object
        :returns: True if the action was done, "unchanged" if the object didn't
                  need harvesting after all or False if there were errors.
        """

        log.debug('Import stage for harvest object: %r', harvest_object.id)

        if not harvest_object:
            log.error('No harvest object received')
            return False

        if harvest_object.content is None:
            self._save_object_error('Empty content for object {}'.format(harvest_object.id), harvest_object, 'Fetch')
            return False

        context = {'model': model, 'session': model.Session,
                   'user': self._get_user_name()}

        source_package = t.get_action('package_show')(
            context,
            {"id": harvest_object.harvest_source_id}
        )
        org = source_package["organization"]

        content = json.loads(harvest_object.content)
        dataset_name = content['output_dataset_name']
        geo_location = content['geo_location']
        resource_name = content['output_resource_name']
        csv_string = content['csv']

        package_data = {
            "name": slugify(dataset_name),
            "title": six.text_type(dataset_name),
            "type": "dataset-2",
            "tags": [{"name": tag} for tag in content.get('output_tags', [])],
            "state": "active",
            "maintainer": "Autogenerated dataset",
            "maintainer_email": "adr@fjelltopp.org",
            "owner_org": org["id"],
            "geo-location": geo_location,
            "extras": [
                {"key": "harvest_source_id",
                 "value": harvest_object.job.source.id}]
        }

        try:
            existing_package = t.get_action('package_show')(context, {"id": package_data["name"]})
            existing_package.update(package_data)
            new_package = t.get_action('package_update')(context, existing_package)
        except NotFound:
            log.info("Creating new package")
            context = {'model': model, 'session': model.Session,
                       'user': self._get_user_name()}
            package_data["id"] = str(uuid.uuid4())
            new_package = t.get_action('package_create')(context, package_data)

        csv_stream = six.BytesIO(six.text_type(csv_string).encode(encoding='UTF-8'))
        csv_filename = "{}.csv".format(slugify(resource_name.replace('/', '').replace(':', '-')))
        resource = {
            "name": resource_name,
            "description": "Data pulled from DHIS2",
            "url_type": "upload",
            "upload": FlaskFileStorage(
                stream=csv_stream,
                content_type="text/csv",
                filename=csv_filename
            ),
            "package_id": new_package["id"]
        }
        found = False
        for existing_resource in new_package["resources"]:
            if existing_resource["name"] == resource["name"]:
                existing_resource = t.get_action('resource_show')(
                    context,
                    {"id": existing_resource["id"]}
                )

                existing_resource.update(resource)
                t.get_action('resource_update')(
                    context,
                    existing_resource
                )
                found = True
        if not found:
            t.get_action('resource_create')(
                context,
                resource
            )

        harvest_object.package_id = new_package['id']
        harvest_object.current = True
        harvest_object.add()

        harvest_object.Session.execute('SET CONSTRAINTS harvest_object_package_id_fkey DEFERRED')
        harvest_object.Session.flush()
        harvest_object.Session.commit()

        return True


class ResourceTypeError(Exception):
    pass


def get_csv_resource_source(resource_id, context):
    resource = t.get_action('resource_show')(
        context,
        {"id": resource_id}
    )
    upload = uploader.get_resource_uploader(resource)
    if not isinstance(upload, uploader.ResourceUpload):
        raise ResourceTypeError
    source = upload.get_path(resource[u'id'])
    return source


def add_missing_columns_from_target_table_config(df, expected_columns):
    for column in expected_columns:
        if column not in list(df):
            df[column] = ''
    return df

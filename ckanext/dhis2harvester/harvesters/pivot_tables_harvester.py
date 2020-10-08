import logging
import requests
from ckan.lib import uploader

from ckanext.harvest.harvesters import HarvesterBase
from ckanext.harvest.model import (HarvestSource, HarvestJob, HarvestObject,
                                   HarvestGatherError, HarvestObjectError)
import ckanext.dhis2harvester.dhis2_api as dhis2_api
import ckan.plugins.toolkit as t
from ckan.logic import NotFound
from ckan import model
from ckan.plugins import toolkit as t
from werkzeug.datastructures import FileStorage as FlaskFileStorage
from slugify import slugify
from datetime import datetime
import pandas as pd
import uuid
import json

import sys

if sys.version_info[0] < 3:
    from StringIO import StringIO
else:
    from io import StringIO

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

    def validate_config(self, config):
        '''

        [optional]

        Harvesters can provide this method to validate the configuration
        entered in the form. It should return a single string, which will be
        stored in the database.  Exceptions raised will be shown in the form's
        error messages.

        :param harvest_object_id: Config string coming from the form
        :returns: A string with the validated configuration options
        '''
        return config

    def get_original_url(self, harvest_object_id):
        '''

        [optional]

        This optional but very recommended method allows harvesters to return
        the URL to the original remote document, given a Harvest Object id.
        Note that getting the harvest object you have access to its guid as
        well as the object source, which has the URL.
        This URL will be used on error reports to help publishers link to the
        original document that has the errors. If this method is not provided
        or no URL is returned, only a link to the local copy of the remote
        document will be shown.

        Examples:
            * For a CKAN record: http://{ckan-instance}/api/rest/{guid}
            * For a WAF record: http://{waf-root}/{file-name}
            * For a CSW record: http://{csw-server}/?Request=GetElementById&Id={guid}&...

        :param harvest_object_id: HarvestObject id
        :returns: A string with the URL to the original document
        '''

    def gather_stage(self, harvest_job):
        '''
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
        '''
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
            self._save_gather_error('Unable to get connection to dhis2: {}: {}'.format(dhis2_connection, e.message),
                                    harvest_job)
            return None
        area_id_map_url = config['area_id_map_url']
        today = datetime.today()
        date_stamp_human = today.strftime("%Y %b %d")
        date_stamp = today.strftime("%Y/%m/%d")
        title_ = harvest_job.source.title.encode('utf-8')
        output_dataset_name_ = '{} Output {}'.format(title_, date_stamp_human)
        if area_id_map_url:
            try:
                area_map_owner = config['area_id_map_owner']
                user = model.User.get(area_map_owner)
                api_key = user.apikey
                headers = {'Authorization': api_key}
                area_csv = requests.get(area_id_map_url, headers=headers)
                if area_csv.status_code != 200:
                    raise ValueError("Error while getting response, code {}".format(area_csv.status_code))
            except Exception as e:
                self._save_gather_error('Failed to process area id csv resource: {}, {}'
                                        .format(area_id_map_url, e.message), harvest_job)
                return None
            harvest_object_data = {
                'output_dataset_name': output_dataset_name_,
                'output_resource_name': 'Area ID Crosswalk Table',
                'csv': area_csv.text
            }
            obj = HarvestObject(guid="pivot_table",
                                job=harvest_job,
                                content=json.dumps(harvest_object_data))
            obj.save()
            obj_ids.append(obj.id)
        for pt in config['column_values']:
            pt_id = pt['id']
            pt_type = {x['id']: x for x in config['selected_pivot_tables']}[pt_id]['type']
            pt_config = dhis2_connection.get_pivot_table_configuration(pt_id)
            data_elements = [c['id'].split('-')[0] for c in pt['columns']]
            csv_resource_name = dhis2_connection.get_pivot_table_csv_resource(
                data_elements, pt_config['ou_levels'], pt_config['periods'])
            harvest_object_data = {
                'dhis2_url': config['dhis2_url'],
                'dhis2_api_version': config['dhis2_api_version'],
                'dhis2_auth_token': dhis2_connection.get_auth_token(),
                'dhis2_api_full_resource': csv_resource_name,
                'output_dataset_name': output_dataset_name_,
                'output_resource_name': '{} {} {} DHIS2'.format(date_stamp, country_name, pt_type),
                'pivot_table_id': pt_id,
                'pivot_table_column_config': pt['columns']
            }
            if area_id_map_url:
                harvest_object_data['area_id_map_csv_str'] = area_csv.text

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
        '''
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
        '''
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
        dhis2_api_full_resource = content['dhis2_api_full_resource']
        pivot_table_column_config = content['pivot_table_column_config']
        try:
            pt_csv = dhis2_connection.get_api_resource(dhis2_api_full_resource)
        except dhis2_api.Dhis2ConnectionError as e:
            self._save_object_error_error('Unable to get dhis2 data: {}: {}: {}'
                                          .format(dhis2_api_full_resource, dhis2_connection, e.message),
                                          harvest_object, 'Fetch')
            return None
        csv_stream = StringIO(pt_csv.text)
        try:
            pt_df = pd.read_csv(csv_stream, sep=",", encoding='utf-8')

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

            _period_col = 'Period'
            _year_col = 'year'
            pt_df[_year_col] = pt_df[_period_col]

            categories_map = {}
            disabled_categories = []
            for cc in pivot_table_column_config:
                if not cc.get('enabled', False):
                    disabled_categories.append(cc['id'])
                target_column_ = cc['target_column']
                if not isinstance(target_column_, list):
                    target_column_ = [target_column_]
                categories_map[cc['id']] = {
                    "target_column": target_column_,
                    "categories": cc['categories']
                }
            _category_column = 'Category option combo'
            _data_element_column = 'Data'

            pt_df['de_cat'] = pt_df[_data_element_column] + "-" + pt_df[_category_column]
            # drop disabled categories
            pt_df = pt_df[~pt_df['de_cat'].isin(disabled_categories)]
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
                for tc in c['target_column']:
                    _data_cols.add(tc)
                    pt_df.loc[i, tc] = row['Value']
                for cat, cat_val in c['categories'].iteritems():
                    _cat_cols.add(cat)
                    pt_df.loc[i, cat] = cat_val
            pt_df = pt_df.drop(_index_to_drop)
            if pt_df.empty:
                self._save_object_error('Failed to process DHIS2 pivot table: {} @ {}. No data matching column configuration.'
                                        .format(pivot_table_id, dhis2_connection),
                                        harvest_object, 'Fetch')
                return None
            # create final columns output
            pt_df = pt_df[[_area_id_col, _area_name_col, _year_col] + list(_cat_cols) + list(_data_cols)]
            # group by orgs and periods and categories
            pt_df = pt_df.groupby([_area_id_col, _area_name_col, _year_col] + list(_cat_cols)).sum().reset_index()
            # sort by area names
            pt_df.sort_values(by=[_area_name_col, _year_col]).reset_index(drop=True)
            # trim period strings
            pt_df[_year_col] = pt_df[_year_col].astype(str).str[:4]
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
        except Exception as e:
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
        '''
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
        '''

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
        resource_name = content['output_resource_name']
        csv_string = content['csv']

        package_data = {
            "name": slugify(dataset_name),
            "title": dataset_name,
            "type": "dataset",
            "tags": [{"name": "DHIS2 Raw Data"}],
            "state": "active",
            "owner_org": org["id"],
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


        csv_stream = StringIO(csv_string.encode('ascii', 'replace'))
        csv_filename = "{}.csv".format(slugify(resource_name.replace('/', '')))
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

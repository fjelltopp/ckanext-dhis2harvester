import copy

import requests
from ckanext.harvest.harvesters import HarvesterBase
from ckanext.harvest.model import HarvestObject
from ckan.plugins import toolkit
from ckan.logic import NotFound
from ckan import model
from requests.auth import HTTPBasicAuth
from werkzeug.datastructures import FileStorage as FlaskFileStorage
from slugify import slugify
import uuid
import json
import logging
from ckanext.dhis2harvester.harvesters import dhis2
from ckanext.dhis2harvester.harvesters.harvest_config_utils import parse_config

log = logging.getLogger(__name__)


class DHIS2Harvester(HarvesterBase):
    '''
    A Test Harvester
    '''

    def info(self):
        '''
        Harvesting implementations must provide this method, which will return
        a dictionary containing different descriptors of the harvester. The
        returned dictionary should contain:

        * name: machine-readable name. This will be the value stored in the
        database, and the one used by ckanext-harvest to call the appropiate
        harvester.
        * title: human-readable name. This will appear in the form's select box
        in the WUI.
        * description: a small description of what the harvester does. This
        will appear on the form as a guidance to the user.

        A complete example may be::

        {
            'name': 'csw',
            'title': 'CSW Server',
            'description': 'A server that implements OGC's Catalog Service
                            for the Web (CSW) standard'
        }

        :returns: A dictionary with the harvester descriptors
        '''
        return {
            'name': 'dhis2harvester',
            'title': 'DHIS2 harvester',
            'description': 'Harvests data from DHIS2',
            # 'form_config_interface': 'Text'
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
        log.debug("Starting config validation")
        config_dict = json.loads(config)
        msg_template = "Couldn't find '{0}' in harvester source config."
        for config_item in ["username", "password", "resourcesToExport"]:
            if config_item not in config_dict:
                raise ValueError(msg_template.format(config_item))
        log.info("Received config string: " + config)
        try:
            r = requests.get(config_dict["url"] + "organisationUnits", auth=HTTPBasicAuth(config_dict['username'], config_dict['password']))
        except requests.ConnectionError:
            raise ValueError("Cannot connect to provided URL. Please double check.")
        if r.status_code == 401:
            raise ValueError("Bad credentials. Status code: " + repr(r.status_code))
        if r.status_code == 404:
            raise ValueError("Are you sure it's valid DHIS2 API URL?. Status code: " + repr(r.status_code))
        elif r.status_code != 200:
            raise ValueError("Cannot connect to provided URL. Please double check. Status code: " + repr(r.status_code))

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
        return ''

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
        log.info("Gather for DHIS2")
        source_config = json.loads(harvest_job.source.config)

        dhis2_data = {
            "data": [{"a": 3, "b": 4}, {"a": 1, "b": 2}]
        }

        obj = HarvestObject(guid="test",
                            job=harvest_job,
                            content=json.dumps(dhis2_data))
        obj.save()

        # get DHIS2 data
        dhis2.work(source_config)
        return [obj.id]

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
        log.info("DHIS2 harvester fetch stage")
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
        log.info("DHIS2 harvester import stage")

        context = {'model': model, 'session': model.Session,
                   'user': self._get_user_name()}

        source_package = toolkit.get_action('package_show')(
            context,
            {"id": harvest_object.harvest_source_id}
        )
        config = parse_config(json.loads(harvest_object.source.config))
        org = source_package["organization"]
        log.info("Config: " + harvest_object.source.config)

        for resource_config in config['exportResources']:
            ckan_resource_name = resource_config['ckanResourceName']
            if 'ckanPackageTitle' in resource_config:
                ckan_package_title = resource_config['ckanPackageTitle']
            else:
                ckan_package_title = ckan_resource_name + "DHIS2"
            ckan_package_name = slugify(ckan_package_title)

            package = {
                "name": ckan_package_name,
                "title": ckan_package_title,
                "type": "dataset",
                "owner_org": org["id"],
                "extras": [
                    {"key": "harvest_source_id",
                     "value": harvest_object.job.source.id}]
            }

            try:
                existing_package = toolkit.get_action('package_show')(context,
                                                                      {
                                                                          "id": package["name"]
                                                                      })
                # TODO : if the package is in a deleted state we should activate it
                existing_package.update(package)
                new_package = toolkit.get_action('package_update')(context,
                                                                   existing_package)
            except NotFound:
                log.info("Creating new package")
                context = {'model': model, 'session': model.Session,
                           'user': self._get_user_name()}
                package["id"] = str(uuid.uuid4())
                new_package = toolkit.get_action('package_create')(context,
                                                                   package)
            resource_filename = "%s_%s.csv" % (ckan_package_name, ckan_resource_name)
            with open(resource_filename, 'rb') as csvfile:
                resource = {
                    "name": ckan_resource_name,
                    "description": "Data pulled from DHIS2",
                    "url_type": "upload",
                    "upload": FlaskFileStorage(
                        stream=csvfile,
                        filename=resource_filename
                        ),
                    "package_id": new_package["id"]
                    }
                found = False
                for old_resource in new_package["resources"]:
                    if old_resource["name"] == resource["name"]:
                        existing_resource = toolkit.get_action('resource_show')(
                            context,
                            {"id": old_resource["id"]}
                        )

                        existing_resource.update(resource)
                        toolkit.get_action('resource_update')(
                            context,
                            existing_resource
                        )
                        found = True
                if not found:
                    toolkit.get_action('resource_create')(
                        context,
                        resource
                    )

                harvest_object.package_id = new_package['id']
                harvest_object.current = True
                harvest_object.save()

        return True

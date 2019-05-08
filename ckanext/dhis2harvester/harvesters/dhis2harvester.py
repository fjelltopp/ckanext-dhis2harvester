from ckan.plugins.core import SingletonPlugin, implements
from ckanext.harvest.harvesters import HarvesterBase
from ckanext.harvest.model import HarvestObject
from ckan.plugins import toolkit
from ckan.logic import NotFound
from ckan import model
from werkzeug.datastructures import FileStorage as FlaskFileStorage
from StringIO import StringIO
import uuid

import json

import logging

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
        log.info("VALIDATE CONFIG")
        log.info(config)
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
        config = harvest_job.source.config
        remote_dhis2_base_url = harvest_job.source.url.rstrip('/')


        # get DHIS2 data

        dhis2_data = {
            "data": [{"a": 3, "b": 4}, {"a": 1, "b": 2}]
        }
        
        obj = HarvestObject(guid="test",
                            job=harvest_job,
                            content=json.dumps(dhis2_data))
        obj.save()
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
        log.info("DHIS2 harvester stage")

        context = {'model': model, 'session': model.Session,
                   'user': self._get_user_name()}
        
        source_package = toolkit.get_action('package_show')(context,
                                                            {
                                                                "id": harvest_object.harvest_source_id
                                                            })

        org = source_package["organization"]

        package = {
            "name": org["name"] + "_dhis2",
            "title": org["title"] + " DHIS2",
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
        except NotFound as e:
            log.info("Creating new package")
            context = {'model': model, 'session': model.Session,
                       'user': self._get_user_name()}
            package["id"] = str(uuid.uuid4()) 
            new_package = toolkit.get_action('package_create')(context,
                                                               package)

        res_file = StringIO()

        res_file.write("a,b\n1,2\n,3,4")
        res_file.seek(0)

        resource = {
            "name": "DHIS2 Test",
            "description": "Data pulled from DHIS2",
            "url_type": "upload",
            "upload": FlaskFileStorage(
                stream=res_file,
                filename="dhis2.csv"
                ),
            "package_id": new_package["id"]
            }
        found = False
        for old_resource in new_package["resources"]:
            if old_resource["name"] == resource["name"]:
                existing_resource = toolkit.get_action('resource_show')(context,
                                                                        {
                                                                            "id": old_resource["id"]
                                                                        })

                existing_resource.update(resource)
                new_resource = toolkit.get_action('resource_update')(context,
                                                                     existing_resource)
                found = True
        if not found:
            
            new_resource = toolkit.get_action('resource_create')(context,
                                                                 resource)
        
        harvest_object.package_id = new_package['id']
        harvest_object.current = True
        harvest_object.save()

        return True

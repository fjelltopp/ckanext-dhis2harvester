import ckan.plugins as p
import logging
import licenses
import ckan.model.license as core_licenses
import ckan.model.package as package
import ckan.plugins.toolkit as toolkit
from dhis2_data_blueprint import dhis2_data
log = logging.getLogger(__name__)


def add_licenses():
    package.Package._license_register = core_licenses.LicenseRegister()
    package.Package._license_register.licenses = [
        core_licenses.License(
            licenses.LicenseCreativeCommonsIntergovernmentalOrgs()),
        core_licenses.License(
            core_licenses.LicenseNotSpecified())
        ]


class DHIS2HarvesterPlugin(p.SingletonPlugin):
    """
    This plugin implements the configurations needed for AIDS data exchange

    """

    p.implements(p.IConfigurer)
    p.implements(p.IFacets, inherit=True)
    p.implements(p.interfaces.IBlueprint)

    # IConfigurer
    def update_config(self, config):
        '''
        This method allows to access and modify the CKAN configuration object
        '''
        add_licenses()
        log.info("DHIS2 Plugin is enabled")
        toolkit.add_template_directory(config, 'templates')
        p.toolkit.add_public_directory(config, 'public')

    def get_blueprint(self):
        return dhis2_data
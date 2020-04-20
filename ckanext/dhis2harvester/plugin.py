import ckan.plugins as p
import logging
import licenses
import ckan.model.license as core_licenses
import ckan.model.package as package
import ckan.plugins.toolkit as toolkit
from dhis2_data_blueprint import dhis2_data
from ui_blueprint import ui_blueprint

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
    p.implements(p.ITemplateHelpers)

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
        return [ui_blueprint, dhis2_data]

    def get_helpers(self):
        return {
            'organization_select_options': organization_select_options
        }


def organization_select_options(action):
    orgs = toolkit.h.organizations_available(action)
    log.warning(orgs)

    def create_option(org):
        return {
            'text': org['title'],
            'value': org['id']
        }

    return map(create_option, orgs)

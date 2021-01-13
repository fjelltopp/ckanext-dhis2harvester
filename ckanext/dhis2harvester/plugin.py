import ckan.plugins as p
import logging
import licenses
import ckan.model.license as core_licenses
import ckan.model.package as package
import ckan.plugins.toolkit as toolkit
from ui_blueprint import ui_blueprint
from ckan.lib.plugins import DefaultTranslation

log = logging.getLogger(__name__)


def add_licenses():
    package.Package._license_register = core_licenses.LicenseRegister()
    package.Package._license_register.licenses = [
        core_licenses.License(
            licenses.LicenseCreativeCommonsIntergovernmentalOrgs()),
        core_licenses.License(
            core_licenses.LicenseNotSpecified())
        ]


class DHIS2HarvesterPlugin(p.SingletonPlugin, DefaultTranslation):
    """
    This plugin implements the configurations needed for AIDS data exchange

    """

    p.implements(p.IConfigurer)
    p.implements(p.IFacets, inherit=True)
    p.implements(p.interfaces.IBlueprint)
    p.implements(p.ITemplateHelpers)
    p.implements(p.ITranslation)

    # IConfigurer
    def update_config(self, config):
        '''
        This method allows to access and modify the CKAN configuration object
        '''
        add_licenses()
        log.info("DHIS2 Plugin is enabled")
        toolkit.add_template_directory(config, 'templates')
        toolkit.add_public_directory(config, 'public')
        toolkit.add_resource('fanstatic', 'dhis2harvester')

    def get_blueprint(self):
        return [ui_blueprint]

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

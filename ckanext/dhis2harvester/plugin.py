import ckan.plugins as p
import logging
import ckan.model.license as core_licenses
import ckan.model.package as package
import ckan.plugins.toolkit as toolkit
from ckan.lib.plugins import DefaultTranslation
from ckanext.dhis2harvester import licenses
from ckanext.dhis2harvester.template_helpers import organization_select_options, iteritems
from ckanext.dhis2harvester.ui_blueprint import ui_blueprint

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
        toolkit.add_resource('assets', 'ckanext-dhis2harvester')

    # ITranslation
    def i18n_domain(self):
        return 'ckanext-dhis2harvester'

    def get_blueprint(self):
        return [ui_blueprint]

    def get_helpers(self):
        return {
            'organization_select_options': organization_select_options,
            'iteritems': iteritems
        }



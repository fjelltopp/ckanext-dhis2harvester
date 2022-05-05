import six

from ckan.plugins import toolkit


def iteritems(dictionary):
    return six.iteritems(dictionary)


def organization_select_options(action):
    orgs = toolkit.h.organizations_available(action)

    def create_option(org):
        return {
            'text': org['title'],
            'value': org['id']
        }

    return list(map(create_option, orgs))

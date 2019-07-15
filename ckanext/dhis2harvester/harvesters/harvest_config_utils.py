
def parse_config(config):
    harvester_config = {
        'url': config.get('url'),
        'username': config['username'],
        'password': config['password'],
    }
    resourcesToExport = []
    resourcesFromEditor = config['resourcesToExport']
    for i, resource in enumerate(resourcesFromEditor):
        json_resource_el = {}
        json_resource_el['apiResource'] = config['apiResource']

        resourceParamStr = ''
        # Adding data elements ids
        resourceParamStr += "dimension=dx:"
        dataElementsIds = resource['dataElementsIds']
        for j, el in enumerate(dataElementsIds):
            if j != 0:
                resourceParamStr += ""
            resourceParamStr += el['id']

        # Adding period, org unit and constants
        resourceParamStr += "&dimension=pe:" + resource['period']
        resourceParamStr += "&dimension=ou:" + resource['orgUnitLevel'] + "" + resource['orgUnitId']
        resourceParamStr += "&displayProperty=NAME"

        json_resource_el['resourceParams'] = resourceParamStr
        json_resource_el['ckanResourceName'] = resource['ckanResourceName']
        json_resource_el['ckanPackageTitle'] = resource['ckanPackageTitle']

        resourcesToExport.append(json_resource_el)

    harvester_config['exportResources'] = resourcesToExport
    return harvester_config


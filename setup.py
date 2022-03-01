from setuptools import setup, find_packages

version = '0.0'

setup(
    name='ckanext-dhis2harvester',
    version=version,
    description="Harvester Package for DHIS2",
    long_description="""""",
    classifiers=[],  # Get strings from http://pypi.python.org/pypi?%3Aaction=list_classifiers
    keywords='',
    author='Fjelltopp',
    author_email='',
    url='http://ckan.org',
    license='GPL Affero v3.0',
    packages=find_packages(exclude=['ez_setup', 'examples', 'tests']),
    namespace_packages=['ckanext'],
    include_package_data=True,
    zip_safe=False,
    install_requires=[],
    entry_points="""
    [ckan.plugins]
    dhis2harvester_plugin=ckanext.dhis2harvester.plugin:DHIS2HarvesterPlugin
    dhis2_pivot_tables_harvester=ckanext.dhis2harvester.harvesters.pivot_tables_harvester:PivotTablesHarvester
    [babel.extractors]
    ckan = ckan.lib.extract:extract_ckan
    """,
    message_extractors={
        'ckanext': [
            ('**.py', 'python', None),
            ('**.js', 'javascript', None),
            ('**/templates/**.html', 'ckan', None),
        ]
    }
)

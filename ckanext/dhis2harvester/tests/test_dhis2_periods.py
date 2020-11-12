import pytest

import ckanext.dhis2harvester.dhis2_periods as dhis2_periods


@pytest.mark.parametrize('dhis2_period_string, expected', [
    ('2018', 'CY2018Q4'),
    ('2020', 'CY2020Q4'),
    (2020, 'CY2020Q4'),
    (2019, 'CY2019Q4'),
    ('2020Q4', 'CY2020Q4'),
    ('2019Q3', 'CY2019Q3'),
    ('2018Q2', 'CY2018Q2'),
    ('2017Q1', 'CY2017Q1'),
    ('202003', 'CY2020Q1'),
    ('202006', 'CY2020Q2'),
    ('202009', 'CY2020Q3'),
    ('202012', 'CY2020Q4'),
], ids=[
    "year string to last quarter of the year",
    "year string to last quarter of the year",
    "int year string to last quarter of the year",
    "int year string to last quarter of the year",
    "quarter string to calendar quarter",
    "quarter string to calendar quarter",
    "quarter string to calendar quarter",
    "quarter string to calendar quarter",
    "March month to Q1 of the year",
    "June month to Q1 of the year",
    "September month to Q1 of the year",
    "December month to Q1 of the year"
])
def test_calendar_quarter_from_dhis2_period_string(dhis2_period_string, expected):
    result = dhis2_periods.calendar_quarter_from_dhis2_period_string(dhis2_period_string)
    assert result == expected


@pytest.mark.parametrize('dhis2_period_string, expected', [
    ('2018', '2018'),
    ('2020', '2020'),
    (2020, '2020'),
    (2019, '2019'),
    ('2020Q4', '2020'),
    ('2019Q3', '2019'),
    ('2018Q2', '2018'),
    ('2017Q1', '2017'),
    ('201810', '2018'),
    ('201901', '2019'),
])
def test_year_from_dhis2_period_string(dhis2_period_string, expected):
    result = dhis2_periods.year_from_dhis2_period_string(dhis2_period_string)
    assert result == expected


@pytest.mark.parametrize('dhis2_period_string', [
    'Fjelltopp',
    'Jan2020',
    '012020',
    012020
])
def test_year_from_dhis2_period_string_errors_on_bad_input(dhis2_period_string):
    with pytest.raises(ValueError):
        dhis2_periods.year_from_dhis2_period_string(dhis2_period_string)


@pytest.mark.parametrize('dhis2_period_string', [
    'Fjelltopp',
    'Jan2020',
    '202002',
    '202011',
    '202010',
    202010,
    '032020',
    032020,
], ids=[
    'only date text supported',
    'only strictly specified date formatting supported',
    'only last months of quarter suported',
    'only last months of quarter suported',
    'only last months of quarter suported',
    'only last months of quarter suported',
    'only YYYYMM not MMYYYY',
    'only YYYYMM not MMYYYY',
])
def test_calendar_quarter_from_dhis2_period_string_errors_on_bad_input(dhis2_period_string):
    with pytest.raises(ValueError):
        dhis2_periods.calendar_quarter_from_dhis2_period_string(dhis2_period_string)


@pytest.mark.parametrize('pivot_table_type, expected', [
    ('naomi-art', True),
    ('naomi-anc', False),
    ('naomi-population', False),
    ('hiv-testing', False),
])
def test_should_translate_year_into_last_quarter(pivot_table_type, expected):
    result = dhis2_periods.should_map_into_calendar_quarter(pivot_table_type)
    assert result == expected


@pytest.mark.parametrize('pivot_table_type, expected', [
    ('naomi-art', False),
    ('naomi-anc', True),
    ('naomi-population', True),
    ('hiv-testing', True),
])
def test_should_map_into_year(pivot_table_type, expected):
    result = dhis2_periods.should_map_into_year(pivot_table_type)
    assert result == expected


@pytest.mark.parametrize('pivot_table_type, expected', [
    ('naomi-art', 'calendar_quarter'),
    ('naomi-anc', 'year'),
    ('naomi-population', 'year'),
    ('hiv-testing', 'year'),
])
def test_period_column_name(pivot_table_type, expected):
    result = dhis2_periods.period_column_name(pivot_table_type)
    assert result == expected

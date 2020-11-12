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
    ('2017Q1', 'CY2017Q1')
])
def test_calendar_quarter_from_dhis2_period_string(dhis2_period_string, expected):
    result = dhis2_periods.calendar_quarter_from_dhis2_period_string(dhis2_period_string)
    assert result == expected


@pytest.mark.parametrize('dhis2_period_string', [
    'Fjelltopp',
    'Jan2020',
    '012020',
    '202010',
    012020,
    202010,
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
    ('naomi-art', 'calendar_quarter'),
    ('naomi-anc', 'year'),
    ('naomi-population', 'year'),
    ('hiv-testing', 'year'),
])
def test_period_column_name(pivot_table_type, expected):
    result = dhis2_periods.period_column_name(pivot_table_type)
    assert result == expected

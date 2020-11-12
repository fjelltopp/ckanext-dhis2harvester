import re
from ckanext.dhis2harvester.config.column_configs_template import TARGET_TYPES as PT_TARGET_TYPES

DEFAULT_PERIOD_TYPE = 'year'


def calendar_quarter_from_dhis2_period_string(dhis2_period_string):
    dhis2_period_string = _stringify(dhis2_period_string)
    is_year, is_period = _validate_input(dhis2_period_string)
    if is_year:
        return "CY{}Q4".format(dhis2_period_string)
    elif is_period:
        return "CY{}".format(dhis2_period_string)


def _validate_input(dhis2_period_string):
    period_re = "^[1-2]\d\d\dQ[1-4]$"
    year_re = "^[1-2]\d\d\d$"
    year_m = re.search(year_re, dhis2_period_string)
    period_m = re.search(period_re, dhis2_period_string)
    if not year_m and not period_m:
        raise ValueError("Unsupported dhis2_period_string: {}".format(dhis2_period_string))
    return year_m, period_m


def _stringify(dhis2_period_string):
    try:
        dhis2_period_string = str(dhis2_period_string)
    except TypeError:
        raise ValueError("Unsupported type of period string: {}".format(type(dhis2_period_string)))
    return dhis2_period_string


def should_map_into_calendar_quarter(pivot_table_type):
    pt_config = PT_TARGET_TYPES[pivot_table_type]
    if pt_config.get("periodType", DEFAULT_PERIOD_TYPE) == "calendar_quarter":
        return True
    return False


def period_column_name(pivot_table_type):
    pt_config = PT_TARGET_TYPES[pivot_table_type]
    return pt_config.get("periodType", DEFAULT_PERIOD_TYPE)

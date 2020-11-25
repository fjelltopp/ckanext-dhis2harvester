import re
from ckanext.dhis2harvester.config.column_configs_template import TARGET_TYPES as PT_TARGET_TYPES, PERIOD_QUARTER, \
    DEFAULT_PERIOD_TYPE, PERIOD_YEAR


def calendar_quarter_from_dhis2_period_string(dhis2_period_string):
    dhis2_period_string = _stringify(dhis2_period_string)
    is_year, is_quarter, is_month = _validate_input(dhis2_period_string)
    if is_year:
        return "CY{}Q4".format(dhis2_period_string)
    elif is_quarter:
        return "CY{}".format(dhis2_period_string)
    elif is_month:
        year_re = r"^[1-2]\d\d\d"
        year_m = re.search(year_re, dhis2_period_string)
        month_re = r"[0-1]\d$"
        month_m = re.search(month_re, dhis2_period_string)
        month = month_m.group(0)
        try:
            quarter = {
                '03': 'Q1',
                '06': 'Q2',
                '09': 'Q3',
                '12': 'Q4'
            }[month]
        except KeyError:
            raise ValueError("Unsupported month period string {}\n"
                             "Needs to be last month of the quarter only: 03, 06, 09, 12.".format(dhis2_period_string))
        return "CY{}{}".format(year_m.group(0), quarter)
    else:
        raise ValueError("Unsupported period string {}".format(dhis2_period_string))


def year_from_dhis2_period_string(dhis2_period_string):
    dhis2_period_string = _stringify(dhis2_period_string)
    is_year, is_quarter, is_month = _validate_input(dhis2_period_string)
    if is_year:
        return dhis2_period_string
    elif is_quarter:
        year_re = r"^[1-2]\d\d\d"
        year_m = re.search(year_re, dhis2_period_string)
        return year_m.group(0)
    elif is_month:
        year_re = r"^[1-2]\d\d\d"
        year_m = re.search(year_re, dhis2_period_string)
        return year_m.group(0)
    else:
        raise ValueError("Unsupported period string {}".format(dhis2_period_string))


def _validate_input(dhis2_period_string):
    quarter_re = r"^[1-2]\d\d\dQ[1-4]$"
    year_re = r"^[1-2]\d\d\d$"
    month_re = r"^[1-2]\d\d\d[0-1]\d$"
    year_m = re.search(year_re, dhis2_period_string)
    quarter_m = re.search(quarter_re, dhis2_period_string)
    month_m = re.search(month_re, dhis2_period_string)
    if not year_m and not quarter_m and not month_m:
        raise ValueError("Unsupported dhis2_period_string: {}".format(dhis2_period_string))
    return year_m, quarter_m, month_m


def _stringify(dhis2_period_string):
    try:
        dhis2_period_string = str(dhis2_period_string)
    except TypeError:
        raise ValueError("Unsupported type of period string: {}".format(type(dhis2_period_string)))
    return dhis2_period_string


def should_map_into_calendar_quarter(pivot_table_type):
    pt_config = PT_TARGET_TYPES[pivot_table_type]
    if pt_config.get("periodType", DEFAULT_PERIOD_TYPE) == PERIOD_QUARTER:
        return True
    return False


def should_map_into_year(pivot_table_type):
    pt_config = PT_TARGET_TYPES[pivot_table_type]
    if pt_config.get("periodType", DEFAULT_PERIOD_TYPE) == PERIOD_YEAR:
        return True
    return False


def period_column_name(pivot_table_type):
    pt_config = PT_TARGET_TYPES[pivot_table_type]
    return pt_config.get("periodType", DEFAULT_PERIOD_TYPE)

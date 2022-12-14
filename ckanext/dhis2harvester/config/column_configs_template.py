from collections import OrderedDict

PERIOD_QUARTER = "calendar_quarter"
PERIOD_YEAR = "year"
DEFAULT_PERIOD_TYPE = PERIOD_YEAR

TARGET_TYPES = OrderedDict([
    ("naomi-anc", {
        "name": "Naomi ANC Input",
        "shortName": "ANC",
        "columns": [
            "anc_clients",
            "anc_known_pos",
            "anc_already_art",
            "anc_tested",
            "anc_tested_pos",
            "anc_known_neg",
            "births_facility"
        ],
        "categories": {
            "age_group": [
                "Y015_049"
            ]
        },
        "tags": [
            "dhis2",
            "anc"
        ],
        "periodType": PERIOD_YEAR
    }),
    ("naomi-art", {
        "name": "Naomi ART Input",
        "shortName": "ART",
        "columns": [
            "art_current",
            "art_new",
            "vl_tested_12mos",
            "vl_suppressed_12mos"
        ],
        "categories": {
            "sex": [
                "male",
                "female",
                "both"
            ],
            "age_group": [
                "Y000_014",
                "Y015_999"
            ]
        },
        "tags": [
            "dhis2",
            "art"
        ],
        "periodType": PERIOD_QUARTER
    }),
    ("naomi-population", {
        "name": "Naomi Population Input",
        "shortName": "Population",
        "columns": [
            "total_pop"
        ],
        "categories": {
            "sex": [
                "male",
                "female",
                "both"
            ],
            "age_group": [
                "Y000_014",
                "Y015_999"
            ]
        },
        "tags": [
            "dhis2",
            "population"
        ],
        "periodType": PERIOD_YEAR
    }),
    ("hiv-testing", {
        "name": "HIV Testing Input",
        "shortName": "HIV Testing",
        "columns": [
            "hts_tested",
            "hts_tested_pos"
        ],
        "categories": {
            "sex": [
                "both"
            ],
            "age_group": [
                "Y015_999"
            ]
        },
        "tags": [
            "dhis2",
            "hiv-testing"
        ],
        "periodType": PERIOD_YEAR
    }),
    ("other", {
        "name": "Other"
    })
])

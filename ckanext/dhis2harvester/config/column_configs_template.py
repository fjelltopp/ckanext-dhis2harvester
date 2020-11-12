from collections import OrderedDict

TARGET_TYPES = OrderedDict([
    ("naomi-anc", {
        "name": "Naomi ANC Input",
        "shortName": "ANC",
        "columns": [
            "anc_clients",
            "anc_known_pos",
            "anc_already_art",
            "anc_tested",
            "anc_test_pos"
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
        "periodType": "year"
    }),
    ("naomi-art", {
        "name": "Naomi ART Input",
        "shortName": "ART",
        "columns": [
            "art_current",
            "art_new"
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
        "periodType": "calendar_quarter"
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
        "periodType": "year"
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
        "periodType": "year"
    }),
    ("other", {
        "name": "Other"
    })
])

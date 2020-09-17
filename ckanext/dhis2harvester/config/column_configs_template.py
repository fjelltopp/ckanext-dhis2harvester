from collections import OrderedDict

TARGET_TYPES = OrderedDict([
    ("naomi-anc", {
        "name": "Naomi ANC Input",
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
        }
    }),
    ("naomi-art", {
        "name": "Naomi ART Input",
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
        }
    }),
    ("naomi-population", {
        "name": "Naomi Population Input",
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
        }
    }),
    ("hiv-testing", {
        "name": "HIV Testing Input",
        "columns": [
            "hts_tested"
            "hts_tested_pos"
        ],
        "categories": {
            "sex": [
                "both"
            ],
            "age_group": [
                "Y015_999"
            ]
        }
    }),
    ("other", {
        "name": "Other"
    })
])

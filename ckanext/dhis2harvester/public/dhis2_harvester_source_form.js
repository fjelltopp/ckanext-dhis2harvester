schema_json = {
  "type": "object",
  "title": "",
  "headerTemplate": " ",
  "required": [
    "url",
    "username",
    "password"
  ],
  "properties": {
    "url": {
      "$id": "#/properties/username",
      "type": "string",
      "format": "url",
      "title": "DHIS2 API URL",
      "description": "URL to DHIS2 api endpoint e.g. https://play.dhis2.org/api/26/",
      "pattern": "^(.*)$"
    },
    "username": {
      "$id": "#/properties/username",
      "type": "string",
      "title": "DHIS2 username",
      "description": "DHIS2 username e.g. admin",
      "pattern": "^(.*)$"
    },
    "password": {
      "$id": "#/properties/password",
      "type": "string",
      "format": "password",
      "title": "DHIS2 password",
      "description": "DHIS2 user password e.g. district",
      "pattern": "^(.*)$"
    },
    "resourcesToExport": {
      "type": "array",
      "format": "tabs",
      "title": "Resources to export",
      "default": {},
      "items": {
        "type": "object",
        "title": "Resource",
        "properties": {
          "ckanResourceName": {
            "$id": "#/properties/ckanResourceName",
            "type": "string",
            "title": "ADR resource name",
            "description": "Name of CKAN resource containing exported csv data e.g. my_DHIS2_resource",
            "pattern": "^(.*)$"
          },
          "ckanPackageTitle": {
            "$id": "#/properties/ckanPackageTitle",
            "type": "string",
            "title": "ADR package title",
            "description": "Name of CKAN package containing exported resource e.g. My Dataset Title",
            "pattern": "^(.*)$"
          },
          "period": {
            "$id": "#/properties/period",
            "type": "string",
            "title": "DHIS2 Period to export",
            "description": "DHIS2 period, can be provided as an DHIS2 alias e.g. LAST_YEAR, LAST_12_MONTHS",
            "pattern": "^(.*)$"
          },
          "orgUnitLevel": {
            "$id": "#/properties/orgUnitLevel",
            "type": "string",
            "title": "DHIS2 Organisation unit level",
            "description": "DHIS2 organisation level to export e.g. LEVEL-5",
            "pattern": "^(.*)$"
          },
          "orgUnitId": {
            "$id": "#/properties/orgUnitId",
            "type": "string",
            "title": "DHIS2 Organisation unit Id",
            "default": "ImspTQPwCqd",
            "description": "Parent organisation unit id to fetch org unit level from.",
            "pattern": "^(.*)$"
          },
          "dataElementsIds": {
            "type": "array",
            "format": "table",
            "title": "DHIS2 Data Elements IDs",
            "description": "DHIS2 data element ids, e.g. sMTMkudvLC",
            "default": {"id": " "},
            "items": {
              "type": "object",
              "title": "DHIS2 ID",
              "properties": {
                "id": {
                  "type": "string",
                }
              }
            }
          }
        }
      }
    }
  }
};

// Initialize the editor with a JSON schema
let configEditor = new JSONEditor(document.getElementById('editor_holder'),{
  schema: schema_json,
  theme: 'bootstrap3',
  disable_collapse: true,
  required_by_default: true,
  disable_edit_json: true,
  disable_properties: true,
  disable_array_reorder: true,
  disable_array_delete_all_rows: true,
  prompt_before_delete: false,
});

// coupling configEditor form with native harvester source text area #field-config
// only value of #field-config is persistent
let config_field = document.getElementById('field-config');
let config_str = config_field.value;
if (config_str) {
  configEditor.setValue(JSON.parse(config_str));
}
configEditor.on('change',function() {
  let config_editor_json = configEditor.getValue();
  config_field.value = JSON.stringify(config_editor_json, null, 4);
});

// coupling DHIS2 url in configEditor with native havester source #field-url
// URL is persistence with #field-url
let fieldURL = document.getElementById('field-url');
configEditor.watch('root.url',function() {
  fieldURL.value = configEditor.getEditor('root.url').getValue();
});
fieldURL.onchange = function() {
  configEditor.getEditor('root.url').setValue(fieldURL.value)
};

// native config text area serves as persistence storage for config.
// It's hidden by default. It can be accessed by advanced users.
let advanceConfigBox = document.getElementsByClassName('dhis2-harvester-json-config')[0];
let showAdvancedConfig = document.getElementById('btn-show-advanced-config');
let hideAdvancedConfig = document.getElementById('btn-hide-advanced-config');
showAdvancedConfig.onclick = function() {
  advanceConfigBox.classList.toggle('hidden');
  showAdvancedConfig.classList.toggle('hidden');
  hideAdvancedConfig.classList.toggle('hidden');
};
hideAdvancedConfig.onclick = function() {
  advanceConfigBox.classList.toggle('hidden');
  showAdvancedConfig.classList.toggle('hidden');
  hideAdvancedConfig.classList.toggle('hidden');
};

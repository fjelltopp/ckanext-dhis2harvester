schema_json = {
  "type": "object",
  "title": "DHIS2 Harvest Source Config Schema",
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
      "title": "DHIS2 URL",
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
      "items": {
        "type": "object",
        "title": "Resource",
        "properties": {
          "dataElementsIds": {
            "type": "array",
            "format": "table",
            "title": "DHIS2 Data Elements IDs",
            "description": "DHIS2 data element ids, e.g. sMTMkudvLC",
            "items": {
              "type": "object",
              "title": "DHIS2 ID",
              "properties": {
                "id": {
                  "type": "string",
                }
              }
            }
          },
          "period": {
            "$id": "#/properties/period",
            "type": "string",
            "title": "Period to export",
            "description": "DHIS2 period, can be provided as an DHIS2 alias e.g. LAST_YEAR, LAST_12_MONTHS",
            "pattern": "^(.*)$"
          },
          "orgUnitLevel": {
            "$id": "#/properties/orgUnitLevel",
            "type": "string",
            "title": "Organisation unit level",
            "description": "DHIS2 organisation level to export e.g. LEVEL-5",
            "pattern": "^(.*)$"
          },
          "orgUnitId": {
            "$id": "#/properties/orgUnitId",
            "type": "string",
            "title": "Organisation unit Id",
            "default": "ImspTQPwCqd",
            "description": "Parent organisation unit id to fetch org unit level from.",
            "pattern": "^(.*)$"
          },
          "ckanResourceName": {
            "$id": "#/properties/ckanResourceName",
            "type": "string",
            "title": "CKAN resource name",
            "description": "Name of CKAN resource containing exported csv data e.g. my_DHIS2_resource",
            "pattern": "^(.*)$"
          },
          "ckanPackageTitle": {
            "$id": "#/properties/ckanPackageTitle",
            "type": "string",
            "title": "CKAN package title",
            "description": "Name of CKAN package containing exported resource e.g. My Dataset Title",
            "pattern": "^(.*)$"
          }
        }
      }
    }
  }
};

// Initialize the editor with a JSON schema
var configEditor = new JSONEditor(document.getElementById('editor_holder'),{
  schema: schema_json,
  theme: 'bootstrap3',
  disable_collapse: true,
  required_by_default: true,
  disable_edit_json: true,
  disable_properties: true,
  disable_array_reorder: true,
  prompt_before_delete: false,
});

var config_str = document.getElementById('field-config').value;
if (config_str) {
  configEditor.setValue(JSON.parse(document.getElementById('field-config').value));
}

configEditor.on('change',function() {
  var config_editor_json = configEditor.getValue();
  document.getElementById('field-config').value = JSON.stringify(config_editor_json, null, 4);
});
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

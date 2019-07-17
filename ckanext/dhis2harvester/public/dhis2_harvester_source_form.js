schema_json = {
  "type": "object",
  "title": "DHIS2 Harvest Source Config Schema",
  "required": [
    "username",
    "password"
  ],
  "properties": {
    "username": {
      "$id": "#/properties/username",
      "type": "string",
      "title": "DHIS2 username",
      "default": "admin",
      "pattern": "^(.*)$"
    },
    "password": {
      "$id": "#/properties/password",
      "type": "string",
      "title": "DHIS2 password",
      "default": "district",
      "pattern": "^(.*)$"
    },
    "resourcesToExport": {
      "type": "array",
      "format": "grid",
      "title": "Resources to export",
      "items": {
        "type": "object",
        "title": "Resource",
        "properties": {
          "dataElementsIds": {
            "type": "array",
            "format": "table",
            "title": "DHIS2 Data Elements IDs",
            "items": {
              "type": "object",
              "title": "DHIS2 ID",
              "properties": {
                "id": {
                  "type": "string",
                  "description": "Single DHIS2 data element id, e.g. sMTMkudvLC"
                }
              }
            }
          },
          "period": {
            "$id": "#/properties/period",
            "type": "string",
            "title": "Period to export",
            "default": "LAST_12_MONTHS",
            "pattern": "^(.*)$"
          },
          "orgUnitLevel": {
            "$id": "#/properties/orgUnitLevel",
            "type": "string",
            "title": "Organisation unit level",
            "default": "LEVEL-2",
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
            "default": "my_DHIS2_resource",
            "pattern": "^(.*)$"
          },
          "ckanPackageTitle": {
            "$id": "#/properties/ckanPackageTitle",
            "type": "string",
            "title": "CKAN package title",
            "default": "My Dataset Title",
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
  theme: 'bootstrap2',
  disable_collapse: true,
  required_by_default: true,
  disable_edit_json: true,
  disable_properties: true,
  disable_array_reorder: true,
  prompt_before_delete: false,
});

var config_str = document.getElementById('field-config').value;
if (config_str) {
  configEditor.startval = JSON.parse(document.getElementById('field-config').value);
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

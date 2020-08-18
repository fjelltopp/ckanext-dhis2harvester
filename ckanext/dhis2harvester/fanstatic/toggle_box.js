// Enable JavaScript's strict mode. Strict mode catches some common
// programming errors and throws exceptions, prevents some unsafe actions from
// being taken, and disables some confusing and bad JavaScript features.
"use strict";

this.ckan.module('toggle_box', function ($) {
  return {
    options:{
    },
    initialize: function () {
      $.proxyAll(this, /_on/);
      this.el.on('click', this._onClick);
    },
    _onClick: function (event) {
      event.preventDefault();

      var iconBox = this.el.find('i');
      var toggleBox = this.el.closest('.toggle-box');
      var contentBox = toggleBox.find('.content');
      var headerBox = toggleBox.find('.header');
      var otherContent = toggleBox.find('.toggle-content');
      var checkboxContent = toggleBox.find('.toggle-checkbox');

      contentBox.slideToggle(400);
      iconBox.toggleClass('fa-toggle-on fa-toggle-off')
      otherContent.toggleClass('hidden');
      checkboxContent.prop("checked", !checkboxContent.prop("checked"));
      toggleBox.toggleClass('toggled');
    }
  };
});

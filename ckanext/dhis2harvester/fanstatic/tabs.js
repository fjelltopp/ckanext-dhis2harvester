// Enable JavaScript's strict mode. Strict mode catches some common
// programming errors and throws exceptions, prevents some unsafe actions from
// being taken, and disables some confusing and bad JavaScript features.
"use strict";

this.ckan.module('tabs', function ($) {
  return {
    options:{
      tabClass: ".tab"
    },
    initialize: function () {
      $.proxyAll(this, /_on/);
      console.log(this.el);
      this.el.find('li').on('click', this._onClick);
    },
    _onClick: function (event) {
      event.preventDefault();
      var targetTab = $(event.currentTarget);
      var activeTab = $(this.el.find("li.active"));
      var targetPage = $(this.options.tabClass + "[tab_page=" + targetTab.attr('target_page') + "]");
      var activePage = $(this.options.tabClass + "[tab_page=" + activeTab.attr('target_page') + "]");

      targetPage.toggleClass('hidden');
      activePage.toggleClass('hidden');
      targetTab.toggleClass('active');
      activeTab.toggleClass('active');
    }
  };
});

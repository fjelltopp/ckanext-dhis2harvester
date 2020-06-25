// Enable JavaScript's strict mode. Strict mode catches some common
// programming errors and throws exceptions, prevents some unsafe actions from
// being taken, and disables some confusing and bad JavaScript features.
"use strict";

this.ckan.module('throbber', function ($) {
  return {
    initialize: function () {
      $.proxyAll(this, /_on/);
      let jqueryElement = this.el;
      jqueryElement.hide();
      $('[type=submit]').on('click', function(){
        jqueryElement.show();
      });
    },
  };
});

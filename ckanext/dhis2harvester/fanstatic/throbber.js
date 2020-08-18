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

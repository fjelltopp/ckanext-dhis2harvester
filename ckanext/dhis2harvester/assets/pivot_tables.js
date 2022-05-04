// Enable JavaScript's strict mode. Strict mode catches some common
// programming errors and throws exceptions, prevents some unsafe actions from
// being taken, and disables some confusing and bad JavaScript features.
"use strict";

this.ckan.module('pivot_table_add', function ($) {
  return {
    options:{
      source: null,
      target: null,
      delete: null
    },
    initialize: function () {
      $.proxyAll(this, /_on/);
      this.el.on('click', this._onClick);
    },
    _onClick: function (event) {
      event.preventDefault();
      $('.pivot-tables [data-module]').each(function(index){
        $(this).select2('destroy');
      });
      $(this.options.target).append($(this.options.source).first().clone().hide());
      $('.pivot-tables [data-module]').each(function(index){
        var id = $(this).attr('id');
        $(this).attr('id', id+index);
        ckan.module.initializeElement(this);
      });
      var original_id = $(this.options.source).first().find('[data-module=autocomplete]').attr('id');
      $(this.options.target).find(".pivot-table:last").slideDown(400);
      if( $(this.options.source).length > 1 ){
        $(this.options.delete).attr("disabled", false);
      }else{
        $(this.options.delete).attr("disabled", true);
      }
      return false;
    }
  };
});

this.ckan.module('pivot_table_delete', function ($) {
  return {
    options:{
      source: null,
      delete: null
    },
    initialize: function () {
      $.proxyAll(this, /_on/);
      this.el.on('click', this._onClick);
    },
    _onClick: function (event) {
      event.preventDefault();
      var source = this.options.source;
      var del = this.options.delete;
      var element = this.el;
      element.closest('.pivot-table').slideUp(400, function(){
        element.closest('.pivot-table').remove();
        if( $(source).length > 1 ){
          $(del).attr("disabled", false);
        }else{
          $(del).attr("disabled", true);
        }

      });
      return false;
    }
  };
});

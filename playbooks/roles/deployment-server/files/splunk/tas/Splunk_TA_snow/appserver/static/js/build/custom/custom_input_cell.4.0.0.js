define([
    'jquery',
    'underscore',
    'backbone',
    "splunkjs/mvc",
    "contrib/text!./templates/missingAccountConfiguration.html"
], function(
    $,
    _,
    Backbone,
    mvc,
    missingAccountConfiguration
) {
    'use strict';

    /**
     * Custom Row Cell
     * @constructor
     * @param {Object} globalConfig - Global configuration.
     * @param {string} serviceName - Input service name.
     * @param {element} el - The element of the custom cell.
     * @param {string} field - The cell field name.
     * @param {model} model - Splunk backbone model for the stanza.
     */
    let CustomInputCell = Backbone.View.extend({
        constructor: function(globalConfig, serviceName, el, field, model) {
            this.setElement(el);

            this.field = field;
            this.model = model;
            this.serviceName = serviceName;
            this.globalConfig = globalConfig;
        },

        render: function() {
            let model = this.model.entry.content;
            let html = '';
            let entity = this.globalConfig.pages.inputs.services[0].entity;
            let label = "";
            let fieldIndex = ""
            for (fieldIndex in entity) {
                if (entity[fieldIndex].field === this.field) {
                    label = entity[fieldIndex].label;
                    break;
                }
            }
            
            if (this.model.entry.content.get(this.field) === undefined || this.model.entry.content.get(this.field).trim() === "") {
                /* Add warning icon when account is not configured in data input to handle upgrade scenario */
                html = _.template(missingAccountConfiguration)({label:label});
                this.$el.html(html);
                return this;
			} else {
				html = this.model.entry.content.get(this.field);
				this.$el.html(html);
				return this;
			}
        }
    });


    return CustomInputCell;
});
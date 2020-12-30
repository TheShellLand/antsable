define([
    "jquery",
    "underscore",
    "backbone",
	"contrib/text!./templates/missingAccountAuthConfig.html"
], function(
    $,
    _,
    Backbone,
	missingAccountAuthConfig
) {
    "use strict";
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
            let html = "";
            // Check for missing configuration in account
            if (this.model.entry.content.get("auth_type") === undefined || this.model.entry.content.get("auth_type") === "") {
                html = this.missingAccountAuthConfigTemplate({title:"Authentication configuration is incomplete for account.", account:""});;
            } else if (this.model.entry.content.get("auth_type") === "basic") {
				html = "Basic Authentication";
			} else if (this.model.entry.content.get("auth_type") === "oauth") {
				html = "OAuth 2.0 Authentication"
			}
            this.$el.html(html);
            return this;
        },
		// Load template for missing configuration
		missingAccountAuthConfigTemplate: _.template(missingAccountAuthConfig)
    });

    return CustomInputCell;
});

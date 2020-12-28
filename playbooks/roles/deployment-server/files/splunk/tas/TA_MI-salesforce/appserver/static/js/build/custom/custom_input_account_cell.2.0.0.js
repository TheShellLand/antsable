
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
			let account = this.model.entry.content.get("account")
			// Check for any missing configuration to highlight in inputs table
			if (account === undefined || account.trim() === "") {
                html = this.missingAccountAuthConfigTemplate({title:"Account configuration is incomplete.", account:""});
            } else if (account !== undefined && this.model.entry.content.get("invalid") !== undefined && this.model.entry.content.get("invalid").trim() === "true") {
				html = this.missingAccountAuthConfigTemplate({title:"Authentication configuration is incomplete for account.",account:account});
			} else {
				if (account !== undefined) {
					html = `${account}`;
				}
			}
			this.$el.html(html);
			return this;
        },
		// Load template for missing configuration
		missingAccountAuthConfigTemplate: _.template(missingAccountAuthConfig)
		
    });


    return CustomInputCell;
});

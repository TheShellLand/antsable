define([
    "jquery",
    "underscore",
    "backbone",
    "splunkjs/mvc","splunk.util"], function($, _, Backbone, mvc, splunkUtils)  {
    
    // Update CSRF token value from the cookie with JQuery ajaxPrefilter for CSRF validation
    // Below block of code is required while using jQuery in the account hook with UCC and OAuth as OAuth uses service.post() which requires CSRF validation with POST.
    var HEADER_NAME = 'X-Splunk-Form-Key';
    var FORM_KEY = splunkUtils.getFormKey();
    if (!FORM_KEY) {
        return;
    }
    if ($) {
        $.ajaxPrefilter(function(options, originalOptions, jqXHR) {
            if (options['type'] && options['type'].toUpperCase() == 'GET') return;
            FORM_KEY = splunkUtils.getFormKey();
            jqXHR.setRequestHeader(HEADER_NAME, FORM_KEY);
        });
    }
    
    class Hook {
        /**
         * Form hook
         * @constructor
         * @param {Object} globalConfig - Global configuration.
         * @param {object} serviceName - Service name
         * @param {object} model - Backbone model for form, not Splunk model
         * @param {object} util - {
                    displayErrorMsg,
                    addErrorToComponent
                    removeErrorFromComponent
                }.
         */
        constructor(globalConfig, serviceName, model, util) {
            this.globalConfig = globalConfig;
            this.serviceName = serviceName;
            this.model = model;
            this.util = util;
        }
        /*
         * This method will be called on create
         */
        onCreate() {
             //No implementation required as of now
        }

        /*
         * Put your render logic here. This function will be called on create or edit.
         */
        onRender() {
			this.model.on("change:custom_endpoint", this._endpointChange, this);
			// Clear passwords on render
			this.model.set("client_secret", '');
			this.model.set("password", '');
			this.model.set("token", '');
			$(`[data-name="client_secret"]`).find("input").val("");
			$(`[data-name="password"]`).find("input").val("");
			$(`[data-name="token"]`).find("input").val("");

			// Currently the for basic authentication on load is showing placeholder "Required(Optional) changing it to "Required"
			$(`[data-name="username"]`).find("input").prop("placeholder", "Required");
			$(`[data-name="password"]`).find("input").prop("placeholder", "Required");
			// Add placeholder for oAuth fields
			$(`[data-name="client_secret"]`).find("input").prop("placeholder", "Required");
			$(`[data-name="client_id"]`).find("input").prop("placeholder", "Required");

			// Setting endpoint url values on render
			if (this.model.get("endpoint") === "login.salesforce.com" ||
			 this.model.get("endpoint") === "test.salesforce.com") {
				this.model.set("custom_endpoint", this.model.get("endpoint"));
			} else if (this.model.get("endpoint") !== undefined) {
				this.model.set("custom_endpoint", "other");
				this._endpointChange();
			}

        }
        /*
            Put form validation logic here.
            Return true if validation pass, false otherwise.
            Call displayErrorMsg when validation failed.
			This object from the parent is passed manually as we need to call the save method manually.
        */
        onSave() {
            $('input').removeClass('validation-error');
			var account_name = this.model.get("name");
			if (account_name === undefined || account_name.trim().length === 0) {
				var validate_message = "Field Account Name is required";
				$(`[data-name="name"]`).find("input").addClass("validation-error");
                this.util.displayErrorMsg(validate_message);
                return false;
			}
			if (this.model.get("custom_endpoint") === undefined || this.model.get("custom_endpoint") === "") {
				var validate_message = "Field Salesforce Environment is required";
				$("#account-custom_endpoint").addClass("validation-error");
                this.util.displayErrorMsg(validate_message);
                return false;
			}
			if (this.model.get("custom_endpoint") === "other" &&
			(this.model.get("endpoint") === undefined || this.model.get("endpoint").trim().length === 0)) {
				var validate_message = "Field Endpoint URL is required";
				$(`[data-name="endpoint"]`).find("input").addClass("validation-error");
                this.util.displayErrorMsg(validate_message);
                return false;
			}
			if (this.model.get("custom_endpoint") === "login.salesforce.com" ||
			 this.model.get("custom_endpoint") === "test.salesforce.com"){
				this.model.set("endpoint", this.model.get("custom_endpoint"));
			}
			return true;
        }

		/*
         * This function will be executed after successful save of the model
         */
        onSaveSuccess() {
            //No implementation required as of now
        }

        /*
         * This function will be executed after error in save of the model
         */
        onSaveFail() {
            //No implementation required as of now
        }

		/*
         * This function will be executed on change of endpoint.
         */
		_endpointChange() {
			if (this.model.get("custom_endpoint") === "other") {
				$(`[data-name="endpoint"]`).parents(`.form-horizontal.endpoint`).show();
				$(`[data-name="endpoint"]`).find("input").prop("placeholder", "Required");
			} else {
				$(`[data-name="endpoint"]`).parents(`.form-horizontal.endpoint`).hide();
				$(`[data-name="endpoint"]`).find("input").prop("required", "");
				$(`[data-name="endpoint"]`).find("input").val("");
			}
		}
    }
    return Hook;
});

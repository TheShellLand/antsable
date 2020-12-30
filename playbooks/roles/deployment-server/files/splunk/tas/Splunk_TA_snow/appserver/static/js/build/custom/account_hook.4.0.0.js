define([], function() {
    class Hook {
        /**
         * Form hook
         * @constructor
         * @param {Object} globalConfig - Global configuration.
         * @param {object} serviceName - Service name
         * @param {object} model - Backbone model for form, not Splunk model
         * @param {object} util - {
                    displayErrorMsg,
                    addErrorToComponent,
                    removeErrorFromComponent
                }.
         */
        constructor(globalConfig, serviceName, model, util) {
            this.globalConfig = globalConfig;
            this.serviceName = serviceName;
            this.model = model;
            this.util = util;
			/*Password should be re-entered everytime on edit */
            this.model.set("password", "");
        
        }
        /*
            Put logic here to execute javascript on Create UI.
        */
        onCreate() {
		}
        /*
            Put logic here to execute javascript when UI gets rendered.
        */
        onRender() {
			/*Set placeholder "Required" for mandatory fields */
            var required_fields = ["name", "url", "username", "password"];
            required_fields.map(this.setRequiredPlaceholder);		
        
        }
        /* 
            Put form validation logic here.
            Return ture if validation pass, false otherwise.
            Call displayErrorMsg when validtion failed.
        */
        onSave() {

            return true;
        }
        /*
            Put logic here to execute javascript to be called after save success.
        */
        onSaveSuccess() {
        }
        /*
            Put logic here to execute javascript to be called on save failed.
        */
        onSaveFail() {
        }
        /*
            Put logic here to execute javascript after loading edit UI.
        */
        onEditLoad() {
        }

        setRequiredPlaceholder(field) {
            $('[data-name="' +field+ '"]').find("input").prop("placeholder", "Required");

        }
    }
    return Hook;
});

define([
    'jquery',
    'underscore',
    'splunkjs/mvc',
    "contrib/text!./templates/accountHelpText.html",
    "contrib/text!./templates/onChangeWarningMessage.html",
    "contrib/text!./templates/sinceWhenWarningMessage.html"
], function($,
	_,
    mvc,
    accountHelpText,
    onChangeWarningMessage,
    sinceWhenWarningMessage) {

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
			this.inputs = [];
            this.is_new_input = true;
        }
        /*
			Put logic here to execute javascript on UI creation.
        */
        onCreate() {
        }
        /*
			Put logic here to execute javascript when UI gets rendered.
        */
        onRender() {
            /* Get window url to add redirect to Configuration page in account field help text */
            var account_config_url = window.location.href.replace("inputs", "configuration");
            
            
            /* Get values on load of input dialogue to fetch previous values */
            this.input_name = this.model.get("name");
            this.oldAccount = this.model.get("account");
            this.oldSinceWhen = this.model.get("since_when");


             /* On edit data input page set "Use existing data input" to Yes and disable edit of "Start date" */
             if(!this.isEmpty(this.input_name)){
				$('div[class$="reuse_checkpoint"]').css("display", "inline");
				this.model.set("reuse_checkpoint", "yes");
				$('[data-name="since_when"]').find("input").attr("readOnly", "true");
				$('[data-name="duration"]').find("input").prop("placeholder", "Required");
				/* If checkpoint field exists on load, display error messages on change of Account */
				this._nameChange(this.oldAccount);
                this.is_new_input = false;
			}
			else{
                $('[data-name="name"]').find("input").prop("placeholder", "Required");
            }

            /* On load of Inputs page add help text under fields */
			$(`[data-name="since_when"]`).append(sinceWhenWarningMessage);
            $(`[data-name="account"]`).after(_.template(accountHelpText)({account_config_url:account_config_url}));
            
           
			/* Call change methods on field value change */
            this.model.on("change:account", function(){ this._valueChange("account", this.oldAccount); }, this);
            this.model.on("change:name", function(){ this._nameChange(this.oldAccount); }, this);
            this.model.on("change:reuse_checkpoint", function(){ this._reuseCheckpointChange(this.oldSinceWhen, this.oldAccount); }, this);
            this.model.on("change:since_when", function(){ this._sinceWhenChange(this.oldSinceWhen); }, this);
            this.model.on("change:table", function(){ this._tableChange(); }, this);

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
			Put logic here to execute javascript after save success.
        */
        onSaveSuccess() {
            window.location.reload();

        }
        /*
			Put logic here to execute javascript after save fail.
        */
        onSaveFail() {
        }

        _nameChange(oldAccountValue) {
			/* When checkpoint file is found for the entered input name, show error messages on changing Account field. */
			if(!this.isEmpty(this.model.get("name"))){
				$("input[type=submit]").prop('disabled', 'true')
                var name = this.model.get("name");
                var timefield = this.model.get("timefield");
                var data = {"input_name": name + "." + timefield};
				var that = this;
				var service = mvc.createService();
				/* Check if checkpoint for the entered Input Name exists of not. */
				service.get("/services/splunk_ta_snow_input_checkpoint", data, (err, response) => {
					var checkpoint_exist = response.data.entry[0].content.checkpoint_exist;
					if(checkpoint_exist){
						/* When checkpoint file is found, set "Start date" to readOnly and reset the field value. */
						$('div[class$="reuse_checkpoint"]').css("display", "block");
						$('[data-name="since_when"]').find("input").attr("readOnly", "true");

						that.model.set("reuse_checkpoint", "yes");
                        this.is_new_input = false;

						/* Show error messages if the Account has been changed when checkpoint file is found. */
						if(that.model.get("account") != oldAccountValue){
							that._valueChange("account", oldAccountValue);
						}

					}
					else{
						/* Hide component as checkpoint file doesn't exists. */
						$('div[class$="reuse_checkpoint"]').css("display", "none");
						$('[data-name="since_when"]').find("input").removeAttr("readOnly");
                        this.is_new_input = true;
						this._hideErrorMessage();
					}
				});
				$("input[type=submit]").removeAttr('disabled')
            }

        }

        _reuseCheckpointChange(oldSinceWhen, oldAccount){
            var reuse_checkpoint = this.model.get("reuse_checkpoint");
            if(reuse_checkpoint == "yes"){
                /* Set "Start date" field to readOnly and show error messages on Account field value change */
                $('[data-name="since_when"]').find("input").attr("readOnly", "true");
                $("#snow-since_when").removeClass("validation-error");
                $("#SinceWhenTooltip").css("display", "none");

                /* Show error messages on Account field value change */
                this._valueChange("account", oldAccount);
            }
            else{
                /* Enable edit of "Start date" field and hide error messages on Account field value change */
                $('[data-name="since_when"]').find("input").removeAttr("readOnly");
                this._hideErrorMessage();
            }
            this.model.set("since_when", oldSinceWhen);
        }
            

        _valueChange(fieldName, oldValue){
            /* When checkpoint file is found, if the old value of the field is different from the new value of field then display error message and hide default help text */
            var newValue = this.model.get(`${fieldName}`);
            var reuse_checkpoint = this.model.get("reuse_checkpoint");

            if($(`#${fieldName}Tooltip`)){
                $(`#${fieldName}Tooltip`).remove();
            }

            /* Display warning message if value of a field is changed for an existing input */
            if(!this.isEmpty(this.model.get("name")) && !this.isEmpty(newValue) && oldValue != newValue && reuse_checkpoint == "yes" && this.is_new_input !== true){
                $(`[data-name="${fieldName}"]`).after(_.template(onChangeWarningMessage)({fieldName:fieldName}));
                $(`#${fieldName}DefaultTooltip`).css("display", "none");
            }
            else{
                $(`#${fieldName}DefaultTooltip`).css("display", "block");
                $(`#${fieldName}Tooltip`).css("display", "none");
            }
        }

        _sinceWhenChange(oldSinceWhen){
            var currentSinceWhen = this.model.get("since_when")
            /* If the since_when value is changed and the mode is edit then high light the field with red border and display warning message. */
            if(!this.isEmpty(this.model.get("name")) && oldSinceWhen !== currentSinceWhen && this.is_new_input !== true){
                $("#snow-since_when").addClass("validation-error");
                $("#SinceWhenTooltip").css("display", "block");
            }
            else{
                $("#snow-since_when").removeClass("validation-error");
                $("#SinceWhenTooltip").css("display", "none");
            }
        }

        _tableChange(){
            var currentTable = this.model.get("table")
            var tableSysCreatedOn = ["syslog", "sys_audit", "sysevent", "syslog_transaction"]

            /*If table value is 'syslog', 'sysevent', 'sys_audit', 'syslog_transaction', set timefield to 'sys_created_on'. If table value is 'em_event', set timefield to 'time_of_event'. */    
            if(tableSysCreatedOn.includes(currentTable)){
                this.model.set("timefield", "sys_created_on")
            }
            else if(currentTable == "em_event"){
                this.model.set("timefield", "time_of_event")
            }
            else{
                this.model.set("timefield", "sys_updated_on")
            }        
        }

        _hideErrorMessage(){
            /* Hide error messages and show the default help text */
            $("#accountTooltip").css("display", "none");
            $("#accountDefaultTooltip").css("display", "block");
        }

        isEmpty(value){
            /* Returns true if value is not set else false */
            return value === undefined || value.trim().length === 0
        }
		
    }
    return Hook;
});
define([
    "jquery",
	"underscore",
	"splunkjs/mvc",
	"contrib/text!./templates/onChangeWarningMessage.html",
	"contrib/text!./templates/accountHelpText.html",
	"contrib/text!./templates/accountConfMissingErrorMessage.html",
	"contrib/text!./templates/missingAccountAuthConfig.html"
], function(
	$,
	_,
	mvc,
	onChangeWarningMessage,
	accountHelpText,
	accountConfMissingErrorMessage,
	missingAccountAuthConfig
	)  {
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
            // Keep value of invalid flag, account, start date, object which can be used to check for any change in value
			this.actualInvalidFlag = this.model.get("invalid");
            this.oldStartdate = this.model.get("start_date");
			this.oldObject = this.model.get("object");
			this.oldAccount = this.model.get("account");

			// In the upgrade scenario, when monitoring interval is not defined, set it to Daily
			if (this.model.get("monitoring_interval") === undefined || this.model.get("monitoring_interval") === ""){
				this.model.set("monitoring_interval", "Daily")
			}
			this.oldMonitoringInterval = this.model.get("monitoring_interval");
			// Add warning message for start-date
			$(`[data-name="start_date"]`).append(_.template(onChangeWarningMessage)({fieldId:"startDate", field:"Query Start Date"}));
			$("#startDateTooltip").css("display","none");
			// Add warning message for object
			$(`[data-name="object"]`).append(_.template(onChangeWarningMessage)({fieldId:"object", field:"Object"}));
			$("#objectTooltip").css("display","none");
			// Add warning message for monitoring_interval
			$(`[data-name="monitoring_interval"]`).after(_.template(onChangeWarningMessage)({fieldId:"monitoringInterval", field:"Monitor Interval"}));
			$("#monitoringIntervalTooltip").css("display","none");

			// Get value of input name as this can be used to check if the mode is edit
			this.input_name = this.model.get("name");
			// Display existing checkpoint option in edit mode
			if(this.input_name !== undefined && this.input_name !== "") {
				$(".use_existing_checkpoint").show();;
			}
			// Add help text for account field
			var account_config_url = window.location.href.replace("inputs", "configuration");
			$(`[data-name="account"]`).after(_.template(accountHelpText)({account_config_url:account_config_url}));
            // Display error message in case of invalid account
			if (this.model.get("invalid") !== undefined && this.model.get("invalid") === "true") {
				$("#accountDefaultTooltip").hide();
				let accountWarning = _.template(accountConfMissingErrorMessage)({account_config_url:account_config_url, account:this.model.get("account")});
				$(`[data-name="account"]`).after(accountWarning);
			}
            // Set default value of use existing checkpoint option
			this.model.set("use_existing_checkpoint","yes");
			$("#"+this.serviceName+"-start_date").prop("readOnly", "true")
			// Bind onchange methods for various fields
			this.model.on("change:object", this._objectChange, this);
			this.model.on("change:account", this._accountChange, this);
			this.model.on("change:name", this._nameChange, this);
			this.model.on("change:use_existing_checkpoint", this._checkpointChange, this);
			this.model.on("change:start_date", this._startDateChange, this);
			this.model.on("change:monitoring_interval", this._monitoringIntervalChange, this);
			var that = this;
			// Set the proper value of model on click of cancel
			$(".cancel-btn, .close").click(function(){
				event.preventDefault();
				if ((that.oldAccount === undefined || that.oldAccount === "") && !that._isSpecialCharFound(that.model.get("name"))) {
					$(".row-"+that.model.get("name")+" > .col-account").html(_.template(missingAccountAuthConfig)({title:"Account configuration is incomplete.", account:""}));
				}
				if (that.actualInvalidFlag === "true" && !that._isSpecialCharFound(that.model.get("name"))) {
					$(".row-"+that.model.get("name")+" > .col-account").html(_.template(missingAccountAuthConfig)({title:"Authentication configuration is incomplete for account.", account:that.oldAccount}));
					that.model.set("invalid",that.actualInvalidFlag);
				}
			});
        }
        /*
         * Put logic that you want to execute before save.
         */

        onSave() {
			let isValid = true;
			// Validation for mandatory fields
			if (this.serviceName == "sfdc_object") {
				let fields = ["name","interval","index","account","object","object_fields","order_by"];
				let fieldDict = {"name":"Name","interval":"Interval","index":"Index","account":"Salesforce Account","object":"Object","object_fields":"Object Fields","order_by":"order_by"};
				_.each(fields, field => {
					if (isValid) {
						var field_value = this.model.get(field);
						if (field == "name" && this._isSpecialCharFound(field_value)){
							var validate_message = "Special characters are not allowed in " + fieldDict[field];
							this.util.displayErrorMsg(validate_message);
							$(`#${this.serviceName}-${field}`).addClass("validation-error");
							isValid = false;
						}
						if (field_value === undefined || field_value.trim().length === 0) {
							var validate_message = "Field "+ fieldDict[field] +" is required";
							this.util.displayErrorMsg(validate_message);
							$(`#${this.serviceName}-${field}`).addClass("validation-error");
							isValid = false;
						}
					}
				});
			} else {
				let fields = ["name","interval","index","account"];
				let fieldDict = {"name":"Name","interval":"Interval","index":"Index","account":"Salesforce Account"};
				let isValid = true;
				_.each(fields, field => {
					if (isValid) {
						var field_value = this.model.get(field);
						if (field == "name" && this._isSpecialCharFound(field_value)){
							var validate_message = "Special characters are not allowed in " + fieldDict[field];
							this.util.displayErrorMsg(validate_message);
							$(`#${this.serviceName}-${field}`).addClass("validation-error");
							isValid = false;
						}
						if (field_value === undefined || field_value.trim().length === 0) {
							var validate_message = "Field "+ fieldDict[field] +" is required";
							this.util.displayErrorMsg(validate_message);
							$(`#${this.serviceName}-${field}`).addClass("validation-error");
							isValid = false;
						}
					}
				});
			}
			if (!isValid) {
				return isValid; 
			}

			$(".row-"+this.model.get("name")+" > .col-account").html(this.model.get("account"));

			this.model.set("invalid","");
			return true;
        }

		/*
         * This function will be executed after successful save of the model
         */
        onSaveSuccess() {
			
        }

        /*
         * This function will be executed after error in save of the model
         */
        onSaveFail() {
            //No implementation required as of now
        }

		_isSpecialCharFound(s) {
			let specRegex = /[~`!@#$%\^&*()+=\-\[\]\\';,/{}|\\":<>\?]/g;
			return specRegex.test(s);
		}

		_accountChange() {
			if (this.model.get("account") !== undefined && this.model.get("account") !== "") {
				$("input[type=submit]").prop("disabled", "true");
				var data ={"account_name": this.model.get("account")};
				var that = this;
				var service = mvc.createService();
				// Internal handler call to get the access token and other values
				service.get("/services/Splunk_TA_salesforce_rh_check_account_configuration", data, (err, response) => {
					if (!err && response.data.entry[0].content.isValid === "false") {
						var account_config_url = window.location.href.replace("inputs", "configuration");
						if ($("#accountTooltip")) {
							$("#accountTooltip").remove();
						}
						$("#accountDefaultTooltip").hide();
						var accountName = that.model.get("account");
						let accountWarning = _.template(accountConfMissingErrorMessage)({account_config_url:account_config_url, account:accountName});
						$(`[data-name="account"]`).after(accountWarning);
						this.model.set("account","");
					} else if ((this.input_name !== undefined && this.input_name !== "") && (this.oldAccount !== undefined && this.oldAccount !== "") && this.oldAccount != this.model.get("account") && this.model.get("use_existing_checkpoint") === "yes") {
						if($("#accountTooltip")){
							$("#accountTooltip").remove();
						}
						$("#accountDefaultTooltip").show();
						$(`[data-name="account"]`).after(_.template(onChangeWarningMessage)({fieldId:"account",field:"Salesforce Account"}));
						$("#"+this.serviceName+"-account").addClass("validation-error");
					} else {
						if ($("#accountTooltip")) {
							$("#accountTooltip").hide();
							$("#accountDefaultTooltip").show();
							$("#"+this.serviceName+"-account").removeClass("validation-error");
						}
					}
					$("input[type=submit]").removeAttr("disabled")
				});
			}
		}
		_nameChange() {
			if (this.model.get("name") !== undefined && this.model.get("name") !== "") {
				$("input[type=submit]").prop("disabled", "true");
				var data = {
							"input_name": this.model.get("name"),
							"service_name": this.serviceName
						};
				var that = this;
				var service = mvc.createService();
				// Internal handler call to get the access token and other values
				service.get("/services/Splunk_TA_salesforce_rh_check_input_checkpoint", data, (err, response) => {
					if (!err && response.data.entry[0].content.isExist === "true") {
						$(".use_existing_checkpoint").show();
						$("#"+this.serviceName+"-start_date").prop("readOnly", "true");
						this.model.set("start_date", "");
					} else {
						this.model.set("use_existing_checkpoint","yes");
						$(".use_existing_checkpoint").hide();
						$("#"+this.serviceName+"-start_date").removeAttr("readOnly");
					}
					$("input[type=submit]").removeAttr("disabled");
				});
			}
		}
		// function for on change value of query start date
		_startDateChange() {
			var currentStartDate = this.model.get("start_date")
			// If the start date value is changed and the mode is edit then high light the field with red border and display warning message.
			if (this.input_name !== undefined && this.input_name !== "" && (this.oldStartDate !== undefined || this.oldStartDate !== "") && this.oldStartdate !== currentStartDate) {
				$("#"+this.serviceName+"-start_date").addClass("validation-error");
				$("#startDateTooltip").show();

			} else {
				$("#"+this.serviceName+"-start_date").removeClass("validation-error");
				$("#startDateTooltip").hide();
			}
		}

		// function for on change value of monitoring_interval
		_monitoringIntervalChange() {
			var currentMonitoringInterval = this.model.get("monitoring_interval")
			// If the monitoring interval is changed and the mode is edit then high light the field with red border and display warning message.
			if (this.input_name !== undefined && this.input_name !== "" && (currentMonitoringInterval !== undefined && currentMonitoringInterval !== "") && this.oldMonitoringInterval !== currentMonitoringInterval) {
				$("#"+this.serviceName+"-monitoring_interval").addClass("validation-error");
				$("#monitoringIntervalTooltip").show();

			} else {
				$("#"+this.serviceName+"-monitoring_interval").removeClass("validation-error");
				$("#monitoringIntervalTooltip").hide();
			}
		}

		_objectChange() {
			var currentObject = this.model.get("object")
			// If the start date value is changed and the mode is edit then high light the field with red border and display warning message.
			if (this.input_name !== undefined && this.input_name !== "" && this.oldObject !== currentObject) {
				$("#"+this.serviceName+"-object").addClass("validation-error");
				$("#objectTooltip").show();
			} else {
				$("#"+this.serviceName+"-object").removeClass("validation-error");
				$("#objectTooltip").hide();
			}
		}

		_checkpointChange() {
			if (this.model.get("use_existing_checkpoint") === "no") {
				if ((this.oldAccount !== undefined && this.oldAccount !== "") && this.oldAccount != this.model.get("account")){
					if ($("#accountTooltip")) {
							$("#accountTooltip").hide();
							$("#accountDefaultTooltip").show();
							$("#"+this.serviceName+"-account").removeClass("validation-error");
						}
				}
				$("#"+this.serviceName+"-start_date").removeAttr("readOnly");
				if (this.model.get("start_date") !== undefined && this.model.get("start_date")!=="") {
					this.model.set("start_date", "");
				}
			} else {
				if ((this.oldAccount !== undefined && this.oldAccount !== "") && this.model.get("account") !== undefined && this.model.get("account") !== "" && this.oldAccount != this.model.get("account")){
					if($("#accountTooltip")){
							$("#accountTooltip").remove();
						}
						$("#accountDefaultTooltip").show();
						$(`[data-name="account"]`).after(_.template(onChangeWarningMessage)({fieldId:"account",field:"Salesforce Account"}));
				}
				$("#"+this.serviceName+"-start_date").prop("readOnly", "true")
				this.model.set("start_date", this.oldStartdate);
			}
		}
	}
    return Hook;
});

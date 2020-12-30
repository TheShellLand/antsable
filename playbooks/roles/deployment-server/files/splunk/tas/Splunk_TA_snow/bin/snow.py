import import_declare_test
from future import standard_library
standard_library.install_aliases()
import sys
import json
from datetime import (datetime, timedelta)
import time
import re
import os
import urllib.parse

from solnlib.packages.splunklib import modularinput as smi
from solnlib import conf_manager
import logging
import os.path as op
import queue
import traceback
from solnlib import orphan_process_monitor as opm

import framework.utils as utils
import framework.log as log
import framework.data_loader as dl
import framework.configure as conf
import snow_job_factory as jf

from snow_config import SnowConfMonitor
from splunk import rest

utils.remove_http_proxy_env_vars()

_LOGGER = log.Logs().get_logger("main")

APP_NAME = op.basename(op.dirname(op.dirname(op.abspath(__file__))))
SESSION_KEY = "session_key"
SERVER_URI = "server_uri"
SPLUNK_HOME = os.environ['SPLUNK_HOME']

def _get_datetime(when=None, input_name=None):
    if not when:
       return "now"

    when = re.sub(r"\s+", " ", when)
    try:
       datetime.strptime(when, "%Y-%m-%d %H:%M:%S")
    except ValueError:
        _LOGGER.warn("Got unexpected value {} of field 'since_when'. Enter the 'since_when' field in "
                     "YYYY-DD-MM hh:mm:ss format for input {}. You can either change it in inputs.conf file or edit "
                     "'Start date' on Inputs page. Using default timestamp of one year ago for now."
                     .format(when, input_name))
        when = "now"

    return when

def _check_duration(duration, input_name):
    if not duration:
        _LOGGER.error("Field 'duration' is required for input '{}'".format(input_name))
        return False

    try:
        int(duration)
    except ValueError:
        _LOGGER.error("Got unexpected value {} of 'duration' field for input '{}'. Duration should be an integer. You can either change it in inputs.conf file or edit 'Collection interval' on Inputs page.".format(duration, input_name))
        return False
    
    return True

def _check_filter_data(filter_data, input_name):
    filter_data_list = filter_data.split("&")
    try:
        for filter_data_value in filter_data_list:
            filter_key, filter_value = filter_data_value.split("=")
            if " " in filter_key or not filter_value:
                raise Exception
    except:
        _LOGGER.error("Got unexpected value {} of 'filter_data' field for input '{}'. Enter filter parameters in key1=value1&key2=value2 format. You can either change it in inputs.conf file or edit 'Filter parameters' on Inputs page.".format(filter_data, input_name))
        return False

    return True

def _create_warning_msg(snow_dict, name):
    warning_msg = ""
    if len(snow_dict) > 0:
        warning_msg += "Remove {0} from '{1}' stanza of {2}/etc/apps/{3}/local/service_now.conf as parameter(s) " \
                       "no longer used. ".format(", ".join(snow_dict), name, SPLUNK_HOME, APP_NAME)

    return warning_msg

def _setup_signal_handler(data_loader):
    """
    Setup signal handlers
    @data_loader: data_loader.DataLoader instance
    """

    def _handle_exit(signum, frame):
        _LOGGER.info("Snow TA is going to exit...")
        data_loader.tear_down()

    utils.handle_tear_down_signals(_handle_exit)


class SNOW(smi.Script):

    def __init__(self):
        super(SNOW, self).__init__()

    def get_scheme(self):
        scheme = smi.Scheme('Splunk Add-on for ServiceNow')
        scheme.description = 'Enable ServiceNow database table inputs'
        scheme.use_external_validation = True
        scheme.streaming_mode_xml = True
        scheme.use_single_instance = True

        scheme.add_argument(
            smi.Argument(
                'name',
                title='Name',
                description='Name',
                required_on_create=True
            )
        )
        
        scheme.add_argument(
            smi.Argument(
                'account',
                required_on_create=True,
            )
        )
        
        scheme.add_argument(
            smi.Argument(
                'duration',
                required_on_create=True,
            )
        )
        
        scheme.add_argument(
            smi.Argument(
                'table',
                required_on_create=True,
            )
        )
        
        scheme.add_argument(
            smi.Argument(
                'exclude',
                required_on_create=False,
            )
        )
        
        scheme.add_argument(
            smi.Argument(
                'timefield',
                required_on_create=False,
            )
        )
        
        scheme.add_argument(
            smi.Argument(
                'reuse_checkpoint',
                required_on_create=False,
            )
        )
        
        scheme.add_argument(
            smi.Argument(
                'since_when',
                required_on_create=False,
            )
        )
        
        scheme.add_argument(
            smi.Argument(
                'id_field',
                required_on_create=True,
            )
        )
        
        scheme.add_argument(
            smi.Argument(
                'filter_data',
                required_on_create=False,
            )
        )

        
        return scheme

    def validate_input(self, definition):
        config_metadata = definition.metadata
        config = definition.parameters

        # Check if 'duration' is an integer
        duration = config.get("duration")
        if not _check_duration(duration, config_metadata['name']):
            raise Exception("Collection interval should be an integer for input '{}', but got {}"
                        .format(config_metadata['name'], duration))

        # Check if 'since_when' conforms to the format mentioned
        if config.get("since_when"):
            when = config["since_when"]
            try:
                when_time = re.sub(r"\s+", " ", when)
                when_time = datetime.strptime(when, "%Y-%m-%d %H:%M:%S")
            except ValueError:
                _LOGGER.error("Got unexpected value {} of 'since_when' field for input '{}'. Enter the 'since_when' field in YYYY-DD-MM hh:mm:ss format. You can either change it in inputs.conf file or edit 'Start date' on Inputs page.".format(when, config_metadata["name"]))
                raise Exception("Date should be in YYYY-DD-MM hh:mm:ss format for input '{}',"
                                " but got {}".format(config_metadata["name"], when))

        # Check if 'filter_data' is in key-value pair format
        if config.get("filter_data"):
            filter_data = config["filter_data"]
            if not _check_filter_data(filter_data, config_metadata['name']):
                raise Exception("Filters should be in key1=value1&key2=value2 format for input '{}', "
                              "but got {}. Please refer to Splunk Add-on for ServiceNow documentation for additional information.".format(config_metadata["name"], filter_data))

        return


    def _get_encrypted_conf(self, conf_name):
        '''
            Return the conf file retrived through legacy conf manager.
            It consists of the password in encrypted form.
        '''
        self.encryption_manager.reload_confs((conf_name,))
        encrypted_conf = self.encryption_manager.get_conf(
            "nobody", APP_NAME, conf_name
        )
        if not encrypted_conf:
            raise Exception("Unable to retrieve the file: {}".format(conf_name))
        return {stanza["stanza"]: stanza for stanza in encrypted_conf}


    def _encrypt_credentials(self, account_conf_manager, settings_conf_manager, session_key, server_uri):
        '''
            This method encrypts the credentials which are in clear text, both in account
            and proxy confs.
        '''

        # Get the legacy password manager
        self.encryption_manager = conf.ConfManager(server_uri,
                                             session_key)

        # This block is in try...except as account_conf_manager.get_conf is raising exception if
        # conf file is not present
        try:
            # Get account password conf for encrypting account information
            account_conf_encrypted = self._get_encrypted_conf("splunk_ta_snow_account")
            # Get account conf
            account_conf = account_conf_manager.get_conf("splunk_ta_snow_account", refresh=True)
            # Get all accounts
            accounts = account_conf.get_all()
            # Iterate for each account and encrypt clear text
            for account, account_info in list(accounts.items()):
                if account_info.get('password'):
                    if not account_conf_encrypted[account].get('password') == account_conf.ENCRYPTED_TOKEN:
                        _LOGGER.info("Encrypting clear password for account={}".format(account))
                        account_conf.update(account, {"password": account_info["password"]},
                                            ["password"])
        except Exception:
            # Pass in case account conf is not obtained, i.e., account not configured
            pass

        # This block is in try...except as settings_conf_manager.get_conf is raising exception if
        # conf file is not present
        try:
            # Get the settings password conf for encrypting proxy information
            settings_conf_encrypted = self._get_encrypted_conf("splunk_ta_snow_settings")
            # Get settings conf
            settings_conf = settings_conf_manager.get_conf("splunk_ta_snow_settings", refresh=True)
            # Get proxy stanza
            setting = settings_conf.get('proxy')
            if setting.get("proxy_password", None):
                if not settings_conf_encrypted['proxy'].get("proxy_password") == settings_conf.ENCRYPTED_TOKEN:
                    _LOGGER.info("Encrypting clear password for proxy")
                    settings_conf.update("proxy", {"proxy_password": setting["proxy_password"]},
                                    ["proxy_password"])
        except Exception:
            # Pass in case settings conf not obtained while reading the proxy settings
            pass


    def stream_events(self, inputs, ew):
        meta_configs = self._input_definition.metadata
        stanza_configs = []

        # Verify if inputs are configured
        if not bool(inputs.inputs):
            _LOGGER.info("No configured inputs found. To collect data from ServiceNow, configure new input(s) or "
                         "update existing input(s) either from Inputs page of the Add-on or manually from inputs.conf.")
            return 0

        for input_name, input_item in inputs.inputs.items():
            if "account" not in input_item:
                rest.simpleRequest("messages",
                           meta_configs[SESSION_KEY],
                           postargs={"severity": "error",
                                     "name": "ServiceNow error message",
                                     "value": "Some configurations are missing in Splunk Add-on for ServiceNow. "
                                              "Fix the configurations to resume data collection."},
                           method="POST")

        # Check for deprecated fields in service_now.conf
        snow_default_fields = ["collection_interval", "loglevel", "since_when", "record_count", "disable_ssl_certificate_validation"]
        snow_account_fields = ["url", "username", "password"]
        snow_proxy_fields = ["proxy_enabled", "proxy_url", "proxy_port", "proxy_username", "proxy_password", "proxy_rdns", "proxy_type"]

        try:
            service_now = conf_manager.ConfManager(
                meta_configs[SESSION_KEY],
                APP_NAME,
                realm="__REST_CREDENTIAL__#{}#configs/conf-service_now".format(APP_NAME))

            conf_service_now = service_now.get_conf("service_now").get_all()

            warning_msg = ""
            
            snow_default = [f for f in snow_default_fields if f in conf_service_now["snow_default"]]
            warning_msg += _create_warning_msg(snow_default, "snow_default")

            if "snow_account" in conf_service_now:
                snow_account = [f for f in snow_account_fields if f in conf_service_now["snow_account"]]
                warning_msg += _create_warning_msg(snow_account, "snow_account")

            if "snow_proxy" in conf_service_now:
                snow_proxy = [f for f in snow_proxy_fields if f in conf_service_now["snow_proxy"]]
                warning_msg += _create_warning_msg(snow_proxy, "snow_proxy")

            if warning_msg:
                _LOGGER.warn(warning_msg)

        except conf_manager.ConfManagerException as e:
            _LOGGER.error(traceback.format_exc())

        try:
            account_cfm = conf_manager.ConfManager(
                meta_configs[SESSION_KEY],
                APP_NAME,
                realm="__REST_CREDENTIAL__#{}#configs/conf-splunk_ta_snow_account".format(APP_NAME))

            settings_cfm = conf_manager.ConfManager(
                meta_configs[SESSION_KEY],
                APP_NAME,
                realm="__REST_CREDENTIAL__#{}#configs/conf-splunk_ta_snow_settings".format(APP_NAME))

            #Read account, settings and snow conf files into variables
            splunk_ta_snow_settings_conf = settings_cfm.get_conf("splunk_ta_snow_settings", refresh=True).get_all()
            loglevel = splunk_ta_snow_settings_conf["logging"].get("loglevel", "INFO")
            log.Logs().set_level(loglevel)
            self._encrypt_credentials(account_cfm, settings_cfm, meta_configs[SESSION_KEY], meta_configs[SERVER_URI])

            try:
                splunk_ta_snow_account_conf = account_cfm.get_conf("splunk_ta_snow_account", refresh=True).get_all()
            except conf_manager.ConfManagerException as e:
                _LOGGER.info("No account configurations found for this add-on. To start data collection, configure new "
                             "account on Configurations page and link it to an input on Inputs page. Exiting TA..")
                return

            service_now_conf = account_cfm.get_conf("service_now", refresh=True).get_all()

            account_info = {}

            #Iterate through multiple account stanzas (if present) in account.conf
            for k, v in splunk_ta_snow_account_conf.items():
                account_info[k] = v
            
            for input_name, input_item in inputs.inputs.items():
                try:
                    input_item['name'] = input_name[input_name.rfind("://") + 3:]

                    # Verifying if account is linked with the enabled input
                    if not input_item.get("account"):
                        _LOGGER.error("No ServiceNow account linked to the data input '{}'. To resume data collection, "
                                    "either configure new account on Configurations page or link an existing account to the"
                                    " input on Inputs page.".format(input_item["name"]))
                        continue

                    # Verifying if table is linked with the enabled input
                    if not input_item.get("table"):
                        _LOGGER.error("No ServiceNow database table linked to the data input '{}'. To resume data collection, "
                                    "either specify table for the input in inputs.conf file or edit 'Table' on Inputs page."
                                    .format(input_item["name"]))
                        continue

                    # Convert duration value to integer
                    if not input_item.get("duration"):
                        input_item["duration"] = 60
                        _LOGGER.warn("No duration specified for input '{}'."
                            "Using default duration=60 for now.".format(input_item["name"]))
                    elif _check_duration(input_item["duration"], input_item["name"]):
                        input_item["duration"] = int(input_item["duration"])
                    else:
                        continue

                    # Logic to specify "since_when" parameter for collecting the events
                    if not input_item.get("since_when"):
                        # Getting the default start date
                        input_item["since_when"] = _get_datetime(input_name=input_item['name'])
                    else:
                        # Verifying the format of start date specified for the input
                        input_item["since_when"] = _get_datetime(
                                when=input_item["since_when"], input_name=input_item['name']
                            )
                    
                    # Logic to check the format of "filter_data"
                    if input_item.get("filter_data"):
                        if not _check_filter_data(input_item["filter_data"], input_item["name"]):
                            continue
                        else:
                            encoded_filter_data = []
                            filter_data_list = input_item.get("filter_data").split("&")
                            for filter_data_value in filter_data_list:
                                filter_key, filter_value = filter_data_value.split("=")
                                filter_dict = {filter_key: filter_value}
                                encoded_value = urllib.parse.urlencode(filter_dict)
                                encoded_filter_data.append(encoded_value)
                            input_item["filter_data"] = "&".join(encoded_filter_data)   

                    # Verify if account parameters are missing and log message for missing parameters
                    account_details = account_info.get(input_item.get('account'))
                    account_warning = ""
                    if not account_details:
                        _LOGGER.error("Specified account {} linked to input '{}' is not configured. You can either configure account in splunk_ta_snow_account.conf file or on Configurations page of add-on.".format(input_item.get('account'), input_item['name']))
                        continue
                    account_parameter = [f for f in snow_account_fields if f not in account_details]

                    if len(account_parameter) > 0:
                        account_warning += "Found {0} parameter(s) missing for account '{1}'. To resume data collection, " \
                                        "fix the account configuration either from Configuration page of the Add-on or by " \
                                        "manual changes in splunk_ta_snow_account.conf."\
                            .format(", ".join(account_parameter), input_item['account'])

                    if account_warning:
                        _LOGGER.error(account_warning)
                        continue

                    # Assign default value if disable_ssl_certificate_validation is missing
                    if "disable_ssl_certificate_validation" not in account_details:
                        account_details["disable_ssl_certificate_validation"] = 0
                        _LOGGER.warn("Found 'disable_ssl_certificate_validation' parameter value missing for account '{}'."
                                    " Using default value='False' to continue data collection.".format(input_item['account']))

                    # Debug log for disable_ssl_certificate_validation
                    _LOGGER.debug("'disable_ssl_certificate_validation' parameter has value {} for account {}"
                                .format(account_details['disable_ssl_certificate_validation'], input_item['account']))

                    # Aggregate all config-related parameters in one dictionary
                    for key, value in account_info[input_item['account']].items():
                        input_item[key] = input_item.get(key, value)

                    input_item.update(meta_configs)

                    for key, value in service_now_conf["snow_default"].items():
                        input_item[key] = input_item.get(key, value)

                    input_item.update(splunk_ta_snow_settings_conf["proxy"])

                    input_item.update(splunk_ta_snow_settings_conf["logging"])

                    if "duration" in input_item:
                        input_item["interval"] = int(input_item["duration"])

                    stanza_configs.append(input_item)
                
                except Exception:
                    _LOGGER.error("Error %s", traceback.format_exc())

            data_loader = dl.GlobalDataLoader.get_data_loader(meta_configs, stanza_configs, jf.JobFactory())

            _setup_signal_handler(data_loader)
            conf_monitor = SnowConfMonitor(data_loader)

            data_loader.add_timer(conf_monitor.check_changes, time.time(), 60)

            checker = opm.OrphanProcessChecker(data_loader.tear_down)
            data_loader.add_timer(checker.check_orphan, time.time(), 2)

            data_loader.run()

        except Exception:
            _LOGGER.error("Error %s", traceback.format_exc())

if __name__ == '__main__':
    exit_code = SNOW().run(sys.argv)
    sys.exit(exit_code)

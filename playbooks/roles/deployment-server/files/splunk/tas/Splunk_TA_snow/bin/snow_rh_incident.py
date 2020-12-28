import json
import traceback

import re
import import_declare_test
import splunk.admin
import splunk.clilib.cli_common as scc

import framework.log as log
from framework import rest
from framework import utils
import os.path as op
from solnlib import conf_manager

utils.remove_http_proxy_env_vars()
APP_NAME = op.basename(op.dirname(op.dirname(op.abspath(__file__))))

_LOGGER = log.Logs().get_logger("main")
log_enter_exit = log.log_enter_exit(_LOGGER)


class SnowIncidentHandler(splunk.admin.MConfigHandler):
    @log_enter_exit
    def setup(self):
        self.supportedArgs.addReqArg('correlation_id')
        self.supportedArgs.addOptArg('account')


    def get_conf_stanzas(self, conf_name, stanza=None):
        '''
        This method returns the configuration stanzas according to the parameters
        passed in clear text form.
        '''
        try:
            cfm = conf_manager.ConfManager(
                self.getSessionKey(),
                APP_NAME,
                realm="__REST_CREDENTIAL__#{}#configs/conf-{}".format(APP_NAME, conf_name)
            )
            if stanza:
                return cfm.get_conf(conf_name, refresh=True).get(stanza)
            else:
                return cfm.get_conf(conf_name, refresh=True).get_all()
        except Exception as e:
            msg = ""
            if conf_name == "splunk_ta_snow_account":
                msg = ("Error while fetching conf: {}. Make sure you have configured "
                "the account.").format(conf_name)
                _LOGGER.error(msg)
            else:
                msg = "Error while fetching conf: {}. Contact Splunk administrator.".format(conf_name)
                _LOGGER.error(msg)
            raise Exception(msg)

    def _get_service_now_account(self, account):
        # Get the required configuration stanzas
        account_conf = self.get_conf_stanzas("splunk_ta_snow_account", account)
        # Handle the condition when account query parameter is not provided
        if not account:
            account_conf = list(account_conf.values())
            # Raise exception in case multiple accounts are configured in absense of account query parameter
            if len(account_conf) != 1:
                raise Exception("As multiple accounts are configured, account parameter must be specified.")
            else:
                # Return the single configured account
                account_conf = account_conf[0]
        settings_conf = self.get_conf_stanzas("splunk_ta_snow_settings")
        service_now_conf = self.get_conf_stanzas("service_now", "snow_default")

        # Set the log level
        loglevel = settings_conf["logging"].get("loglevel", "INFO")
        log.Logs().set_level(loglevel)

        # Update the dictionary of snow account
        snow_account = {}
        for stanza in ("logging", "proxy"):
            snow_account.update(settings_conf[stanza])
        snow_account.update(account_conf)
        snow_account.update(service_now_conf)

        if snow_account.get("proxy_port"):
            try:
                snow_account["proxy_port"] = int(snow_account["proxy_port"])
            except:
                raise Exception("The proxy port must be an integer.")

        snow_url = snow_account.get("url")
        if not snow_url or not snow_account.get("username") or not snow_account.get("password"):
            raise Exception("ServiceNow account has not been setup.")

        prefix = re.search("^https?://", snow_url)
        if not prefix:
            snow_url = "https://%s" % snow_url

        if not snow_url.endswith("/"):
            snow_url = "%s/" % snow_url

        snow_account["url"] = snow_url
        return snow_account

    def _retrieve_incident(self, snow_account, correlation_id):
        http_connection = rest.build_http_connection(
            snow_account)

        url = self._get_incident_url(snow_account["url"], correlation_id)
        try:
            resp, content = http_connection.request(url)
            _LOGGER.info("Got response content {} from {}".format(content, url))
            response_as_json = json.loads(content)
        except Exception:
            msg = ("Failed to get incident for correlation id '{}', "
                   "reason={}").format(correlation_id, traceback.format_exc())
            _LOGGER.error(msg)
            raise Exception(msg)
        else:
            if resp.status not in (200, 201):
                msg = ("Failed to get incident for correlation id '{}', "
                       "code={}, reason={}").format(correlation_id, resp.status,
                                                resp.reason)
                _LOGGER.error(msg)
                raise Exception(msg)
        return response_as_json, url

    @staticmethod
    def _get_incident_url(snow_url, correlation_id):
        return "%sapi/now/table/incident?sysparm_query=correlation_id=%s" \
               % (snow_url, correlation_id)

    @staticmethod
    def _build_error_response(response, code, error_msg):
        response.append("code", code)
        response.append("message", error_msg)

    @staticmethod
    def _get_ticket_link(snow_account, sys_id):
        link = "{}incident.do?sysparm_query=correlation_id={}".format(
            snow_account["url"], sys_id)
        return link

    @log_enter_exit
    def handleList(self, conf_info):
        # Get the account parameter value if provided
        account = self.callerArgs.get('account')[0] if self.callerArgs.get('account') else None
        resp = conf_info["IncidentResult"]

        try:
            snow_account = self._get_service_now_account(account)
        except Exception as e:
            _LOGGER.error("Failed to get snow account, reason={}".format(str(e)))
            self._build_error_response(resp, 400,
                                       "Failed to get snow account, "
                                       "reason={}".format(str(e)))
            return

        correlation_id = self.callerArgs.data['correlation_id'][0]
        _LOGGER.info("Received request with Correlation ID '{}'".format(correlation_id))


        try:
            response_as_json, url = self._retrieve_incident(snow_account,
                                                            correlation_id)
            _LOGGER.info("Fetched incident content {} from url {}".format(response_as_json, url))
            response_result = response_as_json["result"]
            if not response_result:
                msg = "Failed to fetch incident for correlation id {}, reason={}".format(correlation_id, "Record not found.")
                _LOGGER.error(msg)
                raise Exception(msg)
            resp.append("number", response_result[0]["number"])
            resp.append("url_json", url)
            resp.append("url", self._get_ticket_link(snow_account, correlation_id))
        except Exception as e:
            if str(e).__contains__("Unable to find the server"):
                self._build_error_response(resp, 404, "Server Unreachable")
            else:
                self._build_error_response(resp, 404, "Record not found")


@log_enter_exit
def main():
    splunk.admin.init(SnowIncidentHandler, splunk.admin.CONTEXT_NONE)


if __name__ == '__main__':
    main()
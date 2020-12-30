import import_declare_test
from future import standard_library
standard_library.install_aliases()
from builtins import object
import sys
import os.path as op
import gzip
import csv
import json
import re
import traceback
import argparse
import time

import splunk.Intersplunk as si
import splunk.clilib.cli_common as scc

from framework import credentials as cred
from framework import rest
from framework import utils
import framework.log as log
import snow_consts
from solnlib import conf_manager

utils.remove_http_proxy_env_vars()


class ArgumentParser(argparse.ArgumentParser):
    def error(self, message):
        si.parseError("{0}. {1}".format(message, self.format_usage()))


class ICaseDictReader(csv.DictReader, object):
    @property
    def fieldnames(self):
        return [field.strip().lower()
                for field in super(ICaseDictReader, self).fieldnames]


class SnowTicket(object):

    def __init__(self):
        self.session_key = self._get_session_key()
        self.logger = log.Logs().get_logger(self._get_log_file())
        self.snow_account = self._get_service_now_account()
        loglevel = self.snow_account.get("loglevel", "INFO")
        log.Logs().set_level(loglevel)
        self.subcommand = "create"
        self.sys_id = None
        self.account = None

    def _get_session_key(self):
        """
        When called as custom search script, splunkd feeds the following
        to the script as a single line
        'authString:<auth><userId>admin</userId><username>admin</username>\
            <authToken>31619c06960f6deaa49c769c9c68ffb6</authToken></auth>'

        When called as an alert callback script, splunkd feeds the following
        to the script as a single line
        sessionKey=31619c06960f6deaa49c769c9c68ffb6
        """

        import urllib.parse
        session_key = sys.stdin.readline()
        m = re.search("authToken>(.+)</authToken", session_key)
        if m:
            session_key = m.group(1)
        else:
            session_key = session_key.replace("sessionKey=", "").strip()
        session_key = urllib.parse.unquote(session_key.encode("ascii").decode("ascii"))
        session_key = session_key.encode().decode("utf-8")
        return session_key

    def handle(self):
        try:
            self._do_handle()
        except Exception:
            self.logger.error(traceback.format_exc())

    def _do_handle(self):
        self.logger.info("Start of ServiceNow script")

        results = []
        for event in self._get_events():
            if event is None:
                break

            result = self._handle_event(event)
            if result:
                if not result.get('Error Message'):
                    result["_time"] = time.time()
                    results.append(result)
                else:
                    results.append(result)
        si.outputResults(results)

        self.logger.info("End of ServiceNow script")

    def _handle_event(self, event):
        event_data = self._prepare_data(event)
        if not event_data:
            self.logger.info("No event data is available")
            return
        event_data = json.dumps(event_data)

        headers = {
            "Content-type": "application/json",
            "Accept": "application/json",
        }
        endpoint = self._get_endpoint()
        endpoint = "{0}{1}".format(self.snow_account["url"], endpoint)
        http = rest.build_http_connection(
            self.snow_account)
        self.logger.debug("Sending request to %s: %s", endpoint, event_data)
        for _ in range(3):
            ok, result = self._do_event(http, endpoint, event_data, headers)
            if ok:
                return result
        return None

    def _do_event(self, http, endpoint, event_data, headers):
        try:
            response, content = http.request(endpoint,
                                             method=self._get_http_method(),
                                             body=event_data, headers=headers)
            self.logger.info("Sending request to %s, get response code %s",
                             endpoint, response.status)
            result = self._handle_response(response, content)
            return True, result
        except Exception:
            self.logger.error("Failed to connect to %s, error=%s",
                              endpoint, traceback.format_exc())
            self._handle_error()
            return False, None

    def _get_endpoint(self):
        if self.subcommand == "create":
            endpoint = "api/now/table/{}"
            return endpoint.format(self._get_table())
        else:
            endpoint = "api/now/table/{0}/{1}"
            return endpoint.format(self._get_table(), self.sys_id)

    def _get_http_method(self):
        if self.subcommand == "update":
            return "PUT"
        else:
            return "POST"

    def _get_service_now_account(self):
        """
        This function is used read config files
        :return: snow_account dictionary
        """

        app = snow_consts.app_name
        snow_account = {}

        try:
            logger = log.Logs().get_logger("ticket")

            # Read account details from conf file
            account_cfm = conf_manager.ConfManager(
                self.session_key,
                app,
                realm="__REST_CREDENTIAL__#{}#configs/conf-splunk_ta_snow_account".format(app))
            splunk_ta_snow_account_conf = account_cfm.get_conf("splunk_ta_snow_account").get_all()

            # Check if account is empty
            if not self.account:
                si.generateErrorResults("Enter ServiceNow account name.")
                raise Exception("Account name cannot be empty. Enter a configured account name or create new account by going to Configuration page of the Add-on.")
            # Get account details
            elif self.account in splunk_ta_snow_account_conf:
                account_details = splunk_ta_snow_account_conf[self.account]

                snow_account["username"] = account_details["username"]

                prefix = re.search("^https?://", account_details["url"])
                if not prefix:
                    snow_account["url"] = "https://{}".format(account_details["url"])
                else:
                    snow_account["url"] = account_details["url"]

                if not snow_account["url"].endswith("/"):
                    snow_account["url"] = "{}/".format(snow_account["url"])

                snow_account["password"] = account_details["password"].encode("ascii", "replace").decode("ascii")

                snow_account["disable_ssl_certificate_validation"] = account_details["disable_ssl_certificate_validation"]
            # Invalid account name
            else:
                si.generateErrorResults("'" + self.account + "' is not configured. Enter a configured account name or create new account by going to Configuration page of the Add-on.")
                raise Exception("Entered ServiceNow account name is invalid. Enter a configured account name or create new account by going to Configuration page of the Add-on.")

            # Read log and proxy setting details from conf file
            setting_cfm = conf_manager.ConfManager(
                self.session_key,
                app,
                realm="__REST_CREDENTIAL__#{}#configs/conf-splunk_ta_snow_settings".format(app))
            splunk_ta_snow_setting_conf = setting_cfm.get_conf("splunk_ta_snow_settings").get_all()

            if utils.is_true(splunk_ta_snow_setting_conf["proxy"].get("proxy_enabled", False)):
                snow_account["proxy_enabled"] = splunk_ta_snow_setting_conf["proxy"]["proxy_enabled"]
                if splunk_ta_snow_setting_conf["proxy"].get("proxy_port"):
                    snow_account["proxy_port"] = int(splunk_ta_snow_setting_conf["proxy"]["proxy_port"])
                if splunk_ta_snow_setting_conf["proxy"].get("proxy_url"):
                    snow_account["proxy_url"] = splunk_ta_snow_setting_conf["proxy"]["proxy_url"]
                if splunk_ta_snow_setting_conf["proxy"].get("proxy_username"):
                    snow_account["proxy_username"] = splunk_ta_snow_setting_conf["proxy"]["proxy_username"]
                if splunk_ta_snow_setting_conf["proxy"].get("proxy_password"):
                    snow_account["proxy_password"] = splunk_ta_snow_setting_conf["proxy"]["proxy_password"]
                if splunk_ta_snow_setting_conf["proxy"].get("proxy_type"):
                    snow_account["proxy_type"] = splunk_ta_snow_setting_conf["proxy"]["proxy_type"]
                if splunk_ta_snow_setting_conf["proxy"].get("proxy_rdns"):
                    snow_account["proxy_rdns"] = splunk_ta_snow_setting_conf["proxy"]["proxy_rdns"]

            if "loglevel" in list(splunk_ta_snow_setting_conf["logging"].keys()):
                snow_account["loglevel"] = splunk_ta_snow_setting_conf["logging"]["loglevel"]

            return snow_account
        except:
            error_msg = str(traceback.format_exc())
            if "splunk_ta_snow_account does not exist." in error_msg:
                si.generateErrorResults("No ServiceNow account configured. Configure account by going to Configuration page of the Add-on.")
                logger.error("No ServiceNow account configured. Configure account by going to Configuration page of the Add-on.\n" + traceback.format_exc())
            else:
                logger.error(traceback.format_exc())

    def _prepare_data(self, event):
        """
        Return a dict like object
        """
        return event

    def _get_events(self):
        """
        Return events that need to be handled
        """
        raise NotImplementedError("Derive class shall implement this method.")

    def _get_log_file(self):
        """
        Return the log file name
        """
        return "ticket"

    def _handle_response(self, response, content):
        if response.status in (200, 201):
            resp = self._get_resp_record(content)
            if resp:
                result = self._get_result(resp)
            else:
                result = {"error": "Failed to create ticket"}
            return result
        else:
            # For response code 400 log message specifying reasons of possible failures.
            if response.status == 400:
                self.logger.error("Failed to create ticket. Return code is {0} ({1}). One of the possible causes of "
                                  "failure is absence of event management plugin or Splunk Integration plugin on the "
                                  "ServiceNow instance. To fix the issue install the plugin(s) on ServiceNow "
                                  "instance.".format(response.status, response.reason))

                si.parseError("Failed to create ticket. Return code is {0} ({1}). One of the possible causes of failure"
                              " is absence of event management plugin or Splunk Integration plugin on the ServiceNow "
                              "instance. To fix the issue install the plugin(s) on ServiceNow "
                              "instance.".format(response.status, response.reason))

            else:
                self.logger.error("Failed to create ticket. Return code is {0} ({1}).".
                                  format(response.status, response.reason))
                si.parseError("Failed to create ticket. Return code is {0} ({1}).".
                              format(response.status, response.reason))

        return None

    def _handle_error(self, msg="Failed to create ticket."):
        si.parseError(msg)

    def _get_ticket_link(self, sys_id):
        link = "{0}{1}.do?sysparm_query=sys_id={2}".format(
            self.snow_account["url"],
            self._get_table(),
            sys_id)
        return link

    def _get_resp_record(self, content):
        resp = json.loads(content)
        if resp.get("error"):
            self.logger.error("Failed with error: %s", resp["error"])
            return None
        return resp["result"]

    def _get_result(self, resp):
        """
        Return a dict object
        """
        raise NotImplementedError("Derived class shall overrides this")

    def _get_table(self):
        """
        Return a table name
        """
        raise NotImplementedError("Derived class shall overrides this")


def read_alert_results(alert_file, logger):
        logger.info("Reading alert file %s", alert_file)
        if not op.exists(alert_file):
            logger.error("Unable to find the file {}. Contact Splunk administrator for further information."
                         .format(alert_file))
            yield None
        open_type = "rb" if sys.version_info < (3, 0) else "rt"
        with gzip.open(alert_file, open_type) as f:
            for event in ICaseDictReader(f, delimiter=","):
                yield event

def get_account(alert_file):
    """
    This function is used to identify account for alert actions
    :param alert_file: file name
    :return: account name
    """
    try:
        logger = log.Logs().get_logger("ticket")
        if not op.exists(alert_file):
                logger.error("Unable to find the file {}. Contact Splunk administrator for further information."
                             .format(alert_file))
        
        open_type = "rb" if sys.version_info < (3, 0) else "rt"
        with gzip.open(alert_file, open_type) as f:
                for event in ICaseDictReader(f, delimiter=","):
                    return event.get('account')
    except:
        logger.error(traceback.format_exc())
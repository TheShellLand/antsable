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

        import urllib2
        session_key = sys.stdin.readline()
        m = re.search("authToken>(.+)</authToken", session_key)
        if m:
            session_key = m.group(1)
        else:
            session_key = session_key.replace("sessionKey=", "").strip()
        session_key = urllib2.unquote(session_key.encode("ascii"))
        session_key = session_key.decode("utf-8")
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
                result["_time"] = time.time()
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
        for _ in xrange(3):
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
        app = snow_consts.app_name
        snow_conf = scc.getMergedConf("service_now")
        snow_account = {}
        for stanza in ("snow_default", "snow_account", "snow_proxy"):
            snow_account.update(snow_conf[stanza])

        mgr = cred.CredentialManager(self.session_key, scc.getMgmtUri())
        accs = (("url", "username", "password"),
                ("proxy_url", "proxy_username", "proxy_password"))
        for (url_k, user_k, pass_k) in accs:
            url = snow_account[url_k]
            username = snow_account[user_k]
            password = snow_account[pass_k]
            if url and username == "<encrypted>" and password == "<encrypted>":
                userpass = mgr.get_clear_password(url, "dummy", app)
                if not userpass:
                    self.logger.error("Failed to get clear credentials for %s",
                                      url)
                    raise Exception("Failed to get clear credentials"
                                    " for {}".format(url))
                username, password = userpass.split("``")
            snow_account[user_k] = username
            snow_account[pass_k] = password
        if snow_account["proxy_port"]:
            snow_account["proxy_port"] = int(snow_account["proxy_port"])

        if utils.is_false(snow_account["proxy_enabled"]):
            snow_account["proxy_url"] = ""
            snow_account["proxy_port"] = ""

        snow_url = snow_account["url"]
        if not snow_url:
            raise Exception("ServiceNow account has not been setup.")

        if not snow_url.startswith("https://"):
            snow_url = "https://{}".format(snow_url)

        if not snow_url.endswith("/"):
            snow_url = "{}/".format(snow_url)

        snow_account["url"] = snow_url
        return snow_account

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
            self.logger.error("Failed to create ticket. Return code is %s. "
                              "Reason is %s", response.status, response.reason)
            si.parseError("Failed to create ticket. Return code is {0}. Reason"
                          " is {1}".format(response.status, response.reason))
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
            logger.warn("Alert result file %s doesn't exist", alert_file)
            yield None

        with gzip.open(alert_file, "rb") as f:
            for event in ICaseDictReader(f, delimiter=","):
                yield event

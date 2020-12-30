import json
import traceback

import splunk.admin
import splunk.clilib.cli_common as scc

import framework.log as log
import snow_consts
from framework import credentials as cred
from framework import rest
from framework import utils

utils.remove_http_proxy_env_vars()

_LOGGER = log.Logs().get_logger("main")
log_enter_exit = log.log_enter_exit(_LOGGER)


class SnowIncidentHandler(splunk.admin.MConfigHandler):
    @log_enter_exit
    def setup(self):
        self.supportedArgs.addReqArg('correlation_id')

    def _get_service_now_account(self):
        app = snow_consts.app_name
        snow_conf = scc.getMergedConf("service_now")
        snow_account = {}
        for stanza in ("snow_default", "snow_account", "snow_proxy"):
            snow_account.update(snow_conf[stanza])

        mgr = cred.CredentialManager(self.getSessionKey(), scc.getMgmtUri())
        accs = (("url", "username", "password"),
                ("proxy_url", "proxy_username", "proxy_password"))
        for (url_k, user_k, pass_k) in accs:
            url = snow_account[url_k]
            username = snow_account[user_k]
            password = snow_account[pass_k]
            if url and username == snow_consts.encrypted \
                    and password == snow_consts.encrypted:
                userpass = mgr.get_clear_password(url, snow_consts.dummy, app)
                if not userpass:
                    msg = "Failed to get clear credentials for %s" % url
                    _LOGGER.error(msg)
                    raise Exception(msg)
                username, password = userpass.split(snow_consts.userpass_sep)
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
            _LOGGER.info("Got response content %s from %s" % (content, url))
            response_as_json = json.loads(content)
        except Exception:
            msg = ("Failed to get incident for correlation id '%s', "
                   "reason=%s") % (correlation_id, traceback.format_exc())
            _LOGGER.error(msg)
            raise Exception(msg)
        else:
            if resp.status not in (200, 201):
                msg = ("Failed to get incident for correlation id '%s', "
                       "code=%s, reason=%s") % (correlation_id, resp.status,
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
        correlation_id = self.callerArgs.data['correlation_id'][0]
        _LOGGER.info("Received request with Correlation ID '%s'"
                     % correlation_id)
        resp = conf_info["IncidentResult"]

        try:
            snow_account = self._get_service_now_account()
        except Exception as e:
            _LOGGER.error("Failed to get snow account, reason=%s" % str(e))
            self._build_error_response(resp, 400,
                                       "Splunk Add-on for ServiceNow is not "
                                       "configured")
            return

        try:
            response_as_json, url = self._retrieve_incident(snow_account,
                                                            correlation_id)
            _LOGGER.info("Fetched incident content %s from url %s"
                         % (response_as_json, url))
            response_result = response_as_json["result"]
            resp.append("number", response_result[0]["number"])
            resp.append("url_json", url)
            resp.append("url", self._get_ticket_link(snow_account, correlation_id))
        except Exception as e:
            _LOGGER.error("Failed to fetch incident for correlation id %s,"
                          "reason=%s" % (correlation_id, str(e)))
            self._build_error_response(resp, 404, "Record not found")


@log_enter_exit
def main():
    splunk.admin.init(SnowIncidentHandler, splunk.admin.CONTEXT_NONE)


if __name__ == '__main__':
    main()

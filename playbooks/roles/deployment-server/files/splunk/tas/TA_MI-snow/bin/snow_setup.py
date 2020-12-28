"""
Copyright (C) 2018 Splunk Inc. All Rights Reserved.
Description:  This skeleton python script handles the parameters in the
configuration page.

    handleList method: lists configurable parameters in the configuration page
    corresponds to handleractions = list in restmap.conf

    handleEdit method: controls the parameters and saves the values
    corresponds to handleractions = edit in restmap.conf
"""

import os
import os.path as op
import json
import traceback
import re

import splunk.clilib.cli_common as scc
import splunk.admin as admin

from framework import utils
from framework import credentials as cred
from framework import configure as conf
import framework.log as log
import snow_config as sc

utils.remove_http_proxy_env_vars()

_LOGGER = log.Logs().get_logger("setup")


class SetupRestHandler(admin.MConfigHandler):
    snow_args = ("url", "username", "password",
                 "collection_interval", "since_when", "loglevel",
                 "proxy_url", "proxy_port", "proxy_username", "proxy_password",
                 "proxy_enabled", "proxy_rdns", "proxy_type")
    encrypted = "<encrypted>"
    userpass_sep = "``"
    dummy = "dummy"

    def setup(self):
        """
        Set up supported arguments
        """

        if self.requestedAction == admin.ACTION_EDIT:
            for arg in self.snow_args:
                self.supportedArgs.addOptArg(arg)

    def handleList(self, confInfo):
        """
        Read the initial values of the parameters from the custom file
        service_now.conf, and write them to the setup screen.

        If the app has never been set up, uses default/service_now.conf.

        If app has been set up, looks at local/service_now.conf first,
        then looks at default/service_now.conf only if there is no value for
        a field in local/service_now.conf

        For text fields, if the conf file says None, set to the empty string.
        """

        _LOGGER.info("start list")
        conf.reload_confs(("service_now",),
                          self.getSessionKey(), scc.getMgmtUri())

        confDict = self.readConf("service_now")

        if confDict is not None:
            self._decrypt_username_password(confDict)

            for stanza, settings in confDict.items():
                for key, val in settings.items():
                    if key in self.snow_args and val is None:
                        val = ""

                    if key in ("password", "proxy_password"):
                        val = ""

                    confInfo[stanza].append(key, val)
        _LOGGER.info("end list")

    def handleEdit(self, confInfo):
        """
        After user clicks Save on setup screen, take updated parameters,
        normalize them, and save them somewhere
        """

        _LOGGER.info("start edit")

        state_file = op.join(op.dirname(op.abspath(__file__)), ".cred")
        if not op.exists(state_file):
            with open(state_file, "w") as f:
                state = {"url": "None", "proxy_url": "None"}
                json.dump(state, f)
        else:
            with open(state_file) as f:
                state = json.load(f)

        args = self.callerArgs.data
        for arg in self.snow_args:
            if args.get(arg, None) and args[arg][0] is None:
                args[arg][0] = ""

        if "url" in args:
            if not re.findall("^https", str(args["url"][0])):
                err_msg = "Provide a URL in the following format: https://example.com"
                _LOGGER.error(err_msg)
                raise admin.ArgValidationException(err_msg)
            self._handleUpdateSnowAccount(confInfo, args)
            state["url"] = "Done"
            with open(state_file, "w") as f:
                json.dump(state, f)

        if "proxy_url" in args:
            self._handleUpdateProxyAccount(confInfo, args)
            state["proxy_url"] = "Done"
            with open(state_file, "w") as f:
                json.dump(state, f)

        if "collection_interval" in args:
            self._handleUpdateDefaultSettings(confInfo, args)

        conf.reload_confs(("service_now",),
                          self.getSessionKey(), scc.getMgmtUri())

        if state["url"] == "Done" and state["proxy_url"] == "Done":
            os.remove(state_file)
            self._verify_creds()

        _LOGGER.info("end edit")

    def _handleUpdateDefaultSettings(self, confInfo, args):
        # Handle default settings
        default_settings = {}
        for k in ("collection_interval", "since_when", "loglevel"):
            if args.get(k, None):
                default_settings[k] = args[k]
                confInfo["snow_default"].append(k, args[k][0])

        if default_settings:
            self.writeConf("service_now", "snow_default", default_settings)

    def _handleUpdateSnowAccount(self, confInfo, args):
        settings = ("url", "username", "password")

        for k in settings:
            if not args.get(k, None) or not args[k][0]:
                err_msg = 'ServiceNow "{}" is mandatory'.format(k)
                _LOGGER.error(err_msg)
                raise admin.ArgValidationException(err_msg)
        self._handleUpdateAccount(confInfo, args, "snow_account", settings)

    def _handleUpdateProxyAccount(self, confInfo, args):
        settings = ("proxy_url", "proxy_username", "proxy_password",
                    "proxy_port", "proxy_enabled", "proxy_rdns", "proxy_type")

        if not utils.is_true(args["proxy_enabled"][0]):
            _LOGGER.info("Disabling proxy")
            for k in settings:
                if k not in ("proxy_type", "proxy_rdns"):
                    args[k] = [""]
            args["proxy_enabled"][0] = "0"

            confDict = self.readConf("service_now")
            if (confDict.get("snow_proxy") and
                    confDict["snow_proxy"].get("proxy_url")):
                proxy_url = confDict["snow_proxy"]["proxy_url"]
                _LOGGER.info("Remove credentials for proxy %s", proxy_url)
                mgr = cred.CredentialManager(self.getSessionKey(),
                                             scc.getMgmtUri())
                mgr.delete(proxy_url, self.dummy, self.appName)

        if (utils.is_true(args["proxy_enabled"][0]) and
                args["proxy_username"][0] and not args["proxy_password"][0]):
            _LOGGER.error("Missing proxy password")
            raise Exception("Missing proxy password")

        self._handleUpdateAccount(confInfo, args, "snow_proxy", settings)

    def _handleUpdateAccount(self, confInfo, args, stanza, settings):
        mgr = cred.CredentialManager(self.getSessionKey(), scc.getMgmtUri())

        account = {}
        for k in settings:
            if args.get(k, None):
                account[k] = args[k][0]
                confInfo[stanza].append(k, args[k])

        url = args[settings[0]][0].strip()
        user = args[settings[1]][0].strip()
        passwd = args[settings[2]][0].strip()

        if (url and user and passwd and user != self.encrypted and
                    passwd != self.encrypted):
            _LOGGER.info("encrypting")
            userpass = self.userpass_sep.join((user, passwd))
            mgr.update(url, self.dummy, userpass, self.appName)
            account[settings[1]] = self.encrypted
            account[settings[2]] = self.encrypted

        if account:
            self.writeConf("service_now", stanza, account)

    def _decrypt_username_password(self, confDict):
        accounts = (("snow_account", "username", "password", "url"),
                    ("snow_proxy", "proxy_username", "proxy_password",
                     "proxy_url"))
        for (stanza, user_k, passwd_k, url_k) in accounts:
            if not confDict.get(stanza, None):
                continue
            account = confDict[stanza]
            encrypted = all(account.get(k, None) == self.encrypted
                            for k in (user_k, passwd_k))
            if encrypted:
                _LOGGER.info("decrypting")
                mgr = cred.CredentialManager(self.getSessionKey(),
                                             scc.getMgmtUri())
                password = mgr.get_clear_password(account[url_k],
                                                  self.dummy, self.appName)
                if password:
                    user_pass = password.split(self.userpass_sep)
                    account[user_k], account[passwd_k] = user_pass

    def _verify_creds(self):
        _LOGGER.info("Verify credentials")

        confDict = self.readConf("service_now")
        assert confDict

        self._decrypt_username_password(confDict)

        config = {}
        for _, stanza_settings in confDict.iteritems():
            config.update(stanza_settings)

        try:
            # When reset account, verify credentials.
            sc.SnowConfig.verify_user_pass(config)
        except Exception:
            err_msg = ("Failed to validate ServiceNow account. "
                       "Please verify credentials, urls for "
                       "ServiceNow and proxy, and try again. Reason=%s")
            _LOGGER.error(err_msg, traceback.format_exc())
            raise admin.ArgValidationException(err_msg)


admin.init(SetupRestHandler, admin.CONTEXT_APP_ONLY)

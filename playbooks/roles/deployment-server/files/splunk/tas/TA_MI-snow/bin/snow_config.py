import sys
import os.path as op
import os
import json
import re
import copy
import traceback
from datetime import datetime

from framework import configure as conf
from framework import utils
from framework import rest
from framework import credentials as cred
import framework.log as log
import snow_consts as consts

_LOGGER = log.Logs().get_logger("main")


class SnowConfig(object):
    """
    Handles Snow related config, password encryption/decryption
    """

    encrypted = "<encrypted>"
    username_password_sep = "``"
    dummy = "dummy"

    def __init__(self):
        meta_configs, stanza_configs = self.get_modinput_configs()
        self.meta_configs = meta_configs
        self.stanza_configs = stanza_configs
        self.cred_manager = cred.CredentialManager(meta_configs["session_key"],
                                                   meta_configs["server_uri"])
        self.conf_manager = conf.ConfManager(meta_configs["server_uri"],
                                             meta_configs["session_key"])
        self.appname = consts.app_name
        default_configs = self._get_default_configs()
        if all(default_configs[k] for k in ("url", "username", "password")):
            self._set_defaults(default_configs)
            self._encrypt_new_credentials(default_configs)
            self._update_stanza_configs(default_configs)
            self._update_workflow_action_url(default_configs)
        self.default_configs = default_configs

    @staticmethod
    def get_modinput_configs():
        config_str = SnowConfig.get_modinput_config_from_stdin()
        return conf.parse_modinput_configs(config_str)

    @staticmethod
    def get_modinput_config_from_stdin():
        """
        Get modinput from stdin which is feed by splunkd
        """

        try:
            return sys.stdin.read()
        except Exception:
            _LOGGER.error(traceback.format_exc())
            raise

    def _get_default_configs(self):
        """
        Get default configuration of this TA
        If default/service_now.conf doesn't contain the
        default config assign the default configuration
        """

        defaults = {}
        self.conf_manager.reload_confs(("service_now",))
        snow_conf = self.conf_manager.get_conf(
            "nobody", self.appname, "service_now")
        if not snow_conf:
            _LOGGER.error("Failed to get service_now.conf")
            raise Exception("Failed to get service_now.conf")

        snow_conf = {stanza["stanza"]: stanza for stanza in snow_conf}
        for stanza in ("snow_account", "snow_default", "snow_proxy"):
            defaults.update(snow_conf[stanza])

        if defaults["proxy_port"]:
            defaults["proxy_port"] = int(defaults["proxy_port"])

        if defaults["proxy_rdns"]:
            defaults["proxy_rdns"] = utils.is_true(defaults["proxy_rdns"])

        if defaults.get("proxy_type"):
            valid_proxy_types = ("http", "http_no_tunnel", "socks4", "socks5")
            if defaults["proxy_type"] not in valid_proxy_types:
                msg = "Invalid proxy type={}, only {} are supported".format(
                    defaults["proxy_type"], valid_proxy_types)
                _LOGGER.error(msg)
                raise Exception(msg)
        else:
            defaults["proxy_type"] = "http"

        if utils.is_false(defaults["proxy_enabled"]):
            defaults["proxy_url"] = ""
            defaults["proxy_port"] = ""

        conf_copy = copy.deepcopy(defaults)
        self._decrypt_existing_credentials(conf_copy)

        keys = (("collection_interval", 60), ("priority", 10),
                ("loglevel", "INFO"), ("since_when", "now"),
                ("display_value", consts.DEFAULT_DISPLAY_VALUE))

        for k, v in keys:
            if k not in defaults:
                defaults[k] = v

        return defaults

    def _update_workflow_action_url(self, default_configs):
        _LOGGER.info("Update URLs in workflow actions")

        workflows = self.conf_manager.get_conf(
            "nobody", self.appname, "workflow_actions")

        url = default_configs["url"].rstrip("/")
        pat = re.compile(r"(.+)/\w+\.do")
        for workflow in workflows:
            if not workflow["stanza"].startswith("snow_"):
                continue

            m = pat.search(workflow["link.uri"])
            if not m:
                _LOGGER.warn("Failed to extract uri from workflow actions %s",
                             workflow["stanza"])
                continue

            new_uri = workflow["link.uri"].replace(m.group(1), url)
            if workflow["link.uri"] == new_uri:
                continue

            self.conf_manager.update_conf_properties(
                "nobody", self.appname, "workflow_actions", workflow["stanza"],
                {"link.uri": new_uri})

    @staticmethod
    def verify_user_pass(defaults):
        _LOGGER.info("Verify username and password.")
        url = defaults["url"]
        if not url.startswith("https://"):
            url = "https://{}".format(url)

        uri = ("{}/incident.do?JSONv2&sysparm_query="
               "sys_updated_on>=2000-01-01+00:00:00&sysparm_record_count=1")
        url = uri.format(url)
        http = rest.build_http_connection(
            defaults)
        try:
            resp, content = http.request(url)
        except Exception:
            msg = ("Failed to verify ServiceNow username and password, "
                   "reason={}".format(traceback.format_exc()))
            _LOGGER.error(msg)
            raise Exception(msg)
        else:
            if resp.status not in (200, 201):
                msg = ("Failed to verify ServcieNow username and password, "
                       "code={}, reason={}").format(resp.status, resp.reason)
                _LOGGER.error(msg)
                raise Exception(msg)

    @staticmethod
    def _get_datetime(when):
        if not when:
            return "now"

        when = re.sub(r"\s+", " ", when)
        try:
            datetime.strptime(when, "%Y-%m-%d %H:%M:%S")
        except ValueError:
            _LOGGER.warn("{0} is in bad format. "
                         "Expect YYYY-DD-MM hh:mm:ss. "
                         "Use current timestamp.".format(when))
            when = "now"
        return when

    def _set_defaults(self, defaults):
        """
        @parser: default collection configs
        """

        default_when = self._get_datetime(defaults["since_when"])
        # collect category interval name, default interval, default priority
        for sc in self.stanza_configs:
            if not sc.get("duration", None):
                sc["duration"] = int(defaults["collection_interval"])
            else:
                sc["duration"] = int(sc["duration"])

            if not sc.get("priority", None):
                sc["priority"] = int(defaults["priority"])
            else:
                sc["priority"] = int(sc["priority"])

            if not sc.get("since_when", None):
                sc["since_when"] = default_when
            else:
                sc["since_when"] = self._get_datetime(sc["since_when"])

            sc["proxy_enabled"] = 0
            if defaults.get("proxy_enabled"):
                if utils.is_true(defaults["proxy_enabled"]):
                    sc["proxy_enabled"] = 1
            sc["record_count"] = int(defaults["record_count"])
            sc["display_value"] = defaults.get("display_value", "")

        self.meta_configs["loglevel"] = defaults["loglevel"]

    def _encrypt_new_credentials(self, account):
        """
        Encrypt the user credentials if it is new snow.conf
        Update the user credentials if it exists in splunkd and snow.conf
        Encrypt strategy is encrypting both username and password. Splunkd only
        encrypt password, the code works around this by concatenating username
        and password by "``" and treat the concatenated string as password,
        then encrypt the concatenated string. Username is given as "dummy"
        @return None
        """

        encrypted = self.encrypted
        sep = self.username_password_sep

        urls = (("url", "username", "password"),
                ("proxy_url", "proxy_username", "proxy_password"))
        for (url_k, user_k, passwd_k) in urls:
            url, username, password = (account[url_k], account[user_k],
                                       account[passwd_k])
            if (url and username and password and
                    username != encrypted and password != encrypted):
                # Create new one
                user_password = sep.join((username, password))
                self.cred_manager.update(url, self.dummy,
                                         user_password, self.appname)
                _LOGGER.info("Encrypt credential for %s", url)
                key_values = {
                    user_k: self.encrypted,
                    passwd_k: self.encrypted,
                }

                if "proxy" in url_k:
                    stanza = "snow_proxy"
                else:
                    stanza = "snow_account"

                res = self.conf_manager.update_conf_properties(
                    "nobody", self.appname, "service_now", stanza, key_values)
                if not res:
                    raise Exception("Failed to encrypt username password")

    def _decrypt_existing_credentials(self, defaults):
        """
        Decrypt the user credentials if it is encrypted in snow.conf
        @return None
        """

        sep = self.username_password_sep
        urls = (("url", "username", "password"),
                ("proxy_url", "proxy_username", "proxy_password"))
        for (url_k, user_k, passwd_k) in urls:
            url, username, password = (defaults[url_k], defaults[user_k],
                                       defaults[passwd_k])
            if (url and username and password and username == self.encrypted
                    and password == self.encrypted):
                password = self.cred_manager.get_clear_password(url,
                                                                self.dummy,
                                                                self.appname)
                if not password:
                    _LOGGER.error("Failed to get password for ServiceNow")
                    raise Exception("Failed to get password for ServiceNow")

                username, password = password.split(sep)
                defaults[user_k] = username
                defaults[passwd_k] = password

    def _update_stanza_configs(self, defaults):
        self._decrypt_existing_credentials(defaults)
        for sc in self.stanza_configs:
            ks = ("url", "username", "password", "proxy_url",
                  "proxy_port", "proxy_username", "proxy_password",
                  "proxy_type", "proxy_rdns", "disable_ssl_certificate_validation")

            for k in ks:
                sc[k] = defaults[k]
            sc["checkpoint_dir"] = self.meta_configs["checkpoint_dir"]
            stanza_name = sc["name"]
            table = stanza_name[stanza_name.rfind("://") + 3:]
            sc["name"] = table.lower()


class SnowConfMonitor(object):
    def __init__(self, data_loader):
        self.data_loader = data_loader
        app_dir = op.dirname(op.dirname(op.abspath(__file__)))
        conf_files = {
            op.join(app_dir, "local", "inputs.conf"): None,
            op.join(app_dir, "default", "inputs.conf"): None,
            op.join(app_dir, "local", "service_now.conf"): None,
            op.join(app_dir, "default", "service_now.conf"): None,
            op.join(app_dir, "bin", "framework", "setting.conf"): None,
        }

        for k in conf_files:
            try:
                conf_files[k] = op.getmtime(k)
            except OSError:
                _LOGGER.debug("Getmtime for %s, failed: %s",
                              k, traceback.format_exc())
        self.conf_files = conf_files

    def check_changes(self):
        conf_files = self.conf_files
        changed_files = []
        for f, last_mtime in conf_files.iteritems():
            try:
                if op.getmtime(f) != last_mtime:
                    changed_files.append(f)
                    _LOGGER.info("Detect %s has changed", f)
            except OSError:
                pass

        if changed_files:
            conf.reload_confs(changed_files,
                              self.data_loader.meta_configs["session_key"],
                              self.data_loader.meta_configs["server_uri"])
            _LOGGER.info("Detect conf files has changed, exiting...")
            self.data_loader.tear_down()


def remove_checkpoint(meta_configs, stanza):
    ckpt_dir = meta_configs["checkpoint_dir"]
    time_field = stanza.get("timefield", "sys_updated_on")
    ckpt_file = op.join(ckpt_dir, "{0}{1}{2}".format(stanza["name"], ".",
                                                     time_field))
    if op.exists(ckpt_file):
        try:
            os.remove(ckpt_file)
            _LOGGER.warn("Clean checkpoint file: %s", ckpt_file)
        except OSError:
            _LOGGER.error("Failed to clean checkpoint file: %s, with error %s",
                          ckpt_file, traceback.format_exc())


def handle_modinput_checkpoint(meta_configs, stanza_configs):
    modinputs = op.join(meta_configs["checkpoint_dir"], ".modinputs")
    stanza_configs_copy = copy.deepcopy(stanza_configs)
    for stanza in stanza_configs_copy:
        for key in ("password", "username",
                    "proxy_password", "proxy_username"):
            del stanza[key]
    dict_configs = {sc["name"]: sc for sc in stanza_configs_copy}

    def _write_modinputs(modinput_file, configs):
        with open(modinput_file, "w") as f:
            json.dump(configs, f, encoding="utf-8")

    if not op.exists(modinputs):
        _write_modinputs(modinputs, dict_configs)
        return

    with open(modinputs) as f:
        try:
            prev_stanzas = json.load(f, encoding="utf-8")
        except ValueError:
            _LOGGER.error("Failed to load previous modinput checkpoint file")
            _write_modinputs(modinputs, dict_configs)
            return

    for sc in stanza_configs_copy:
        if sc["name"] not in prev_stanzas:
            _LOGGER.warn("Look like a new stanza, try to clean previous "
                         "one if exist")
            remove_checkpoint(meta_configs, sc)
        else:
            if sc["since_when"] != prev_stanzas[sc["name"]]["since_when"]:
                _LOGGER.warn("Detect initial datetime for collection changed "
                             "for table: %s, prev=%s, now=%s",
                             sc["name"],
                             prev_stanzas[sc["name"]]["since_when"],
                             sc["since_when"])
                remove_checkpoint(meta_configs, sc)
    _write_modinputs(modinputs, dict_configs)

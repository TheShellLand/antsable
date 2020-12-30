from builtins import object
import sys
import os
import os.path as op
import traceback
from framework import configure as conf
import framework.log as log
import logging

_LOGGER = log.Logs().get_logger("main")


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
			op.join(app_dir, "local", "splunk_ta_snow_account.conf"): None,
            op.join(app_dir, "default", "splunk_ta_snow_account.conf"): None,
            op.join(app_dir, "local", "splunk_ta_snow_settings.conf"): None,
            op.join(app_dir, "default", "splunk_ta_snow_settings.conf"): None,
        }

        for k in conf_files:
            try:
                if op.isfile(k):
                    conf_files[k] = op.getmtime(k)
            except OSError:
                _LOGGER.error("Failure occurred while reading modified time of the conf file '{0}'. The reason for "
                              "failure is: {1}. Contact Splunk administrator for further information.",
                              k, traceback.format_exc())
        self.conf_files = conf_files

    def check_changes(self):
        conf_files = self.conf_files
        changed_files = []
        for f, last_mtime in conf_files.items():
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
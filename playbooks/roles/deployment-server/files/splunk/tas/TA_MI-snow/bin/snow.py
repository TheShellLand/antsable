#!/usr/bin/python

"""
This is the main entry point for Snow TA
"""

import time
import sys
import re
from datetime import datetime
import traceback

from framework import data_loader as dl
from framework import utils
import framework.log as log
import framework.orphan_process_monitor as opm

import snow_job_factory as jf
import snow_config


utils.remove_http_proxy_env_vars()
_LOGGER = log.Logs().get_logger("main")


def do_scheme():
    """
    Feed splunkd the TA's scheme
    """

    print """
    <scheme>
    <title>Splunk Add-on for ServiceNow</title>
    <description>Enable ServiceNow database table inputs</description>
    <use_external_validation>true</use_external_validation>
    <streaming_mode>xml</streaming_mode>
    <use_single_instance>true</use_single_instance>
    <endpoint>
      <args>
        <arg name="name">
          <title>ServiceNow database table name</title>
        </arg>
        <arg name="duration">
           <title>Collection interval for this table (in seconds)</title>
        </arg>
        <arg name="exclude" required_on_create="false">
          <title>Excluded properties of the database table (comma separated)</title>
        </arg>
        <arg name="timefield" required_on_create="false">
          <title>Time field of the database table (sys_updated_on by default)</title>
        </arg>
        <arg name="since_when" required_on_create="false">
          <title>Date started from (UTC in "YYYY-MM-DD hh:mm:ss" format. Default is one year ago.)</title>
        </arg>
        <arg name="filter_data" required_on_create="false">
          <title>Provide filters in key-value pairs as shown in example for indexing only selected data from the table e.g. key1=value1&amp;key2=value2 (By default no filter will be applied)</title>
        </arg>
      </args>
    </endpoint>
    </scheme>
    """


def _setup_signal_handler(data_loader):
    """
    Setup signal handlers
    @data_loader: data_loader.DataLoader instance
    """

    def _handle_exit(signum, frame):
        _LOGGER.info("Snow TA is going to exit...")
        data_loader.tear_down()

    utils.handle_tear_down_signals(_handle_exit)


def run():
    """
    Main loop. Run this TA for ever
    """

    try:
        snow_conf = snow_config.SnowConfig()
    except Exception as ex:
        _LOGGER.error("Failed to setup config for Snow TA: %s", ex.message)
        _LOGGER.error(traceback.format_exc())
        raise

    if snow_conf.stanza_configs:
        loglevel = snow_conf.default_configs.get("loglevel", "INFO")
        if loglevel != "INFO":
            log.Logs().set_level(loglevel)
    else:
        _LOGGER.info("No data collection for Snow is found in the "
                     "inputs.conf. Do nothing and Quit the TA")
        return

    if not all(snow_conf.default_configs[k]
               for k in ("url", "username", "password")):
        _LOGGER.info("No ServiceNow account is configured, exiting...")
        return

    snow_config.handle_modinput_checkpoint(snow_conf.meta_configs,
                                           snow_conf.stanza_configs)

    data_loader = dl.GlobalDataLoader.get_data_loader(snow_conf.meta_configs,
                                                      snow_conf.stanza_configs,
                                                      jf.JobFactory())
    _setup_signal_handler(data_loader)
    conf_monitor = snow_config.SnowConfMonitor(data_loader)
    data_loader.add_timer(conf_monitor.check_changes, time.time(), 60)
    checker = opm.OrphanProcessChecker(data_loader.tear_down)
    data_loader.add_timer(checker.check_orphan, time.time(), 2)
    data_loader.run()


def validate_config():
    """
    Validate inputs.conf
    """

    _, configs = snow_config.SnowConfig.get_modinput_configs()
    for config in configs:
        if config.get("priority", None):
            try:
                int(config.get("priority"))
            except ValueError:
                _LOGGER.error("priority should be an integer in stanza: {}"
                              .format(config["name"]))
                raise Exception("priority should be an integer in stanza: {}"
                                .format(config["name"]))

        if config.get("duration", None):
            try:
                int(config.get("duration"))
            except ValueError:
                _LOGGER.error("duration should be an integer in stanza: {}"
                              .format(config["name"]))
                raise Exception("duration should be an integer in stanza: {}"
                                .format(config["name"]))

        if config.get("since_when", None):
            when = config["since_when"]
            try:
                when_time = re.sub(r"\s+", " ", when)
                when_time = datetime.strptime(when, "%Y-%m-%d %H:%M:%S")
            except ValueError:
                _LOGGER.error("Date should be in YYYY-DD-MM hh:mm:ss format, "
                              "but got {}".format(when))
                raise Exception("Date should be in YYYY-DD-MM hh:mm:ss format,"
                                " but got {}".format(when))

        if config.get("filter_data"):
            filter_data = config["filter_data"]
            filter_data_list = filter_data.split("&")
            try:
                for filter_data_value in filter_data_list:
                    str_check = re.match(r"^(?:(?:[^\s]+[\S]+?)=(?:[^\s]+[\S]+))$", filter_data_value)
                    if not str_check:
                       _LOGGER.error("Filters should be in key1=value1&key2=value2 format, "
                              "but got {}".format(filter_data))
                       raise Exception
            except:
                _LOGGER.error("Filters should be in key1=value1&key2=value2 format, "
                              "but got {}".format(filter_data))
                raise Exception("Filters should be in key1=value1&key2=value2 format, "
                              "but got {}".format(filter_data))
    return 0


def usage():
    """
    Print usage of this binary
    """

    hlp = "%s --scheme|--validate-arguments|-h"
    print >> sys.stderr, hlp % sys.argv[0]
    sys.exit(1)


def main():
    """
    Main entry point
    """

    args = sys.argv
    if len(args) > 1:
        if args[1] == "--scheme":
            do_scheme()
        elif args[1] == "--validate-arguments":
            sys.exit(validate_config())
        elif args[1] in ("-h", "--h", "--help"):
            usage()
        else:
            usage()
    else:
        _LOGGER.info("Start Snow TA")
        run()
        _LOGGER.info("End Snow TA")
    sys.exit(0)


if __name__ == "__main__":
    main()

from builtins import object
import base64
import json
import logging
import os
import os.path as op
import threading
import traceback
from datetime import datetime
from datetime import timedelta
import re

import framework.log as log
import snow_consts as sc
from framework import rest
from framework import utils

_LOGGER = log.Logs().get_logger("main")


class _ObjectWrapper(object):

    def __init__(self, obj, table, endpoint, timefield, input_name):
        self.obj = obj
        self.table = table
        self.endpoint = endpoint
        self.timefield = timefield
        self.input_name = input_name

    def to_string(self, idx, host, excludes=()):
        evt_fmt = ("<event stanza=\"snow://{0}\"><time>{1}</time><source>{2}</source>"
                   "<sourcetype>{3}</sourcetype><host>{4}</host>"
                   "<index>{5}</index><data>endpoint=\"{6}\",{7}</data>"
                   "</event>")
        tag_vals = ",".join(("{0}=\"{1}\"".format(
            k, str(v).replace('"', ""))
            for k, v in self.obj.items()
            if k not in excludes))

        try:
            timestamp = datetime.strptime(self.obj[self.timefield],
                                          "%Y-%m-%d %H:%M:%S")
        except ValueError:
            timestamp = datetime.utcnow()
        return evt_fmt.format(self.input_name, utils.datetime_to_seconds(timestamp),
                              self.endpoint, "snow:" + self.table, host, idx,
                              self.endpoint, utils.escape_cdata(tag_vals))


class Snow(object):
    _SUPPORTED_DISPLAY_VALUES = ["false", "true", "all"]

    def __init__(self, config):
        """
        @config: dict like, should have url, username, checkpoint_dir,
                 since_when, proxy_url, proxy_username, proxy_password
        """

        host = config["url"]
        prefix = re.search("^https?://", host)
        if not prefix:
            host = "https://{0}".format(host)

        if not host.endswith("/"):
            host = "{0}/".format(host)

        self.host = host
        self.username = config["username"]
        self.password = config["password"]
        self.checkpoint_dir = config["checkpoint_dir"]
        if config["since_when"] == "now":
            now = datetime.utcnow() - timedelta(365)
            self.since_when = datetime.strftime(now, "%Y-%m-%d %H:%M:%S")
        else:
            self.since_when = config["since_when"]
        self.id_field = config["id_field"]
        self.filter_data = config.get("filter_data")
        self.config = config
        self.context = {}
        self._lock = threading.Lock()
        self._display_value = self._get_display_value(config)

    def _get_display_value(self, config):
        dv = config.get("display_value", "")
        if utils.is_false(dv):
            return "false"
        if utils.is_true(dv):
            return "true"
        if dv and dv in self._SUPPORTED_DISPLAY_VALUES:
            return dv
        return sc.DEFAULT_DISPLAY_VALUE

    @staticmethod
    def _rebuild_json_node(json_obj):
        # For latest api, field is returned as dict which contains
        # value and display_value.
        node = {}
        for k, v in json_obj.items():
            if not isinstance(v, dict):
                node[k] = v
            else:
                node[k] = v.get("value", "")
                node["dv_%s" % k] = v.get("display_value", "")
        return node

    def _flat_json_records(self, records):
        _LOGGER.debug("Start to rebuild json content.")
        if self._display_value != "all":
            # For old api, field and display value which starts with 'dv_'
            # are returned together. We don't need to do anything.
            return records
        results = []
        for item in records:
            results.append(self._rebuild_json_node(item))
        _LOGGER.debug("Rebuild json content end.")
        return results

    def collect_data(self, table, timefield, input_name, count=sc.DEFAULT_RECORD_LIMIT):
        assert table and timefield

        objs = []
        _write_checkpoint_status = 0
        with self._lock:
            last_timestamp = self._read_last_collection_time(input_name, timefield)
            params = "{0}>={1}^ORDERBY{0}".format(timefield, last_timestamp)
            _, content = self._do_collect(table, params, limit=count)
            if not content:
                return

            jobjs = self._json_to_objects(content)
            records = jobjs.get("result")

            if not records:
                return

            if jobjs.get("error"):
                _LOGGER.error("Failure occurred while getting records from {0}{1}. The reason for failure= {2}. Contact Splunk administrator "
                              "for further information.".format(self.host, table, str(jobjs["error"])))
                return

            records = self._flat_json_records(records)

            jobjs, refreshed = self._remove_collected_records(
                input_name, timefield, records, count)
            _write_checkpoint_status = self._write_checkpoint(input_name, timefield, jobjs, refreshed)

        if not _write_checkpoint_status:
            return None

        _LOGGER.info("Data collection completed for input {0}. Got {1} records from {2}{3}."
                     .format(input_name, len(jobjs), self.host, table))
        objs.extend((_ObjectWrapper(obj, table, self.host, timefield, input_name)
                     for obj in jobjs))
        return {table: objs}

    def _do_collect(self, table, params, limit):
        rest_uri = self._get_uri(table, params, limit)

        http = rest.build_http_connection(
            self.config, self.config["duration"])
        _LOGGER.info("Initiating request to {}".format(rest_uri))
        response, content = None, None
        try:
            credentials = base64.urlsafe_b64encode(("%s:%s" % (self.config["username"], 
                                                                self.config["password"])).encode('UTF-8')).decode('ascii')
            response, content = http.request(rest_uri, headers={
                "Accept-Encoding": "gzip",
                "Accept": "application/json",
                "Authorization": "Basic %s" % credentials
            })

            if response.status not in (200, 201):
                _LOGGER.error("Failure occurred while connecting to {0}. The reason for failure={1}."
                              .format(rest_uri, response.reason))
        except Exception:
            _LOGGER.error("Failure occurred while connecting to {0}. The reason for failure={1}."
                          .format(rest_uri, traceback.format_exc()))
        
        _LOGGER.info("Ending request to {}".format(rest_uri))
        return response, content

    @staticmethod
    def _json_to_objects(json_str):
        return json.loads(json_str)

    def _remove_collected_records(self, input_name, timefield, jobjs, maxcount):
        # Remove the records already collected
        k = ".".join((input_name, timefield))
        last_timestamp = self.context[k]["last_collection_time"]
        last_time_records = self.context[k]["last_time_records"]
        records_to_be_removed = set()
        refreshed = False
        if jobjs and last_time_records:
            all_records_has_same_timestamp = True
            for obj in jobjs:
                if obj[timefield] == last_timestamp:
                    if obj[self.id_field] in last_time_records:
                        records_to_be_removed.add(obj[self.id_field])
                else:
                    all_records_has_same_timestamp = False
                    break

            if records_to_be_removed:
                _LOGGER.debug("After collecting data for input {0}, found duplicate records. Last time records: {1} "
                              "with timestamp={2}. Remove collected records: {3} with the same timestamp"
                              .format(input_name, last_time_records, last_timestamp, records_to_be_removed))

                record_count = len(jobjs)
                jobjs = [jobj for jobj in jobjs
                         if jobj[self.id_field] not in records_to_be_removed]

                if _LOGGER.level == logging.DEBUG:
                    _LOGGER.debug("Left collected records: {}".format([jobj[self.id_field] for jobj in jobjs]))

                if all_records_has_same_timestamp and record_count == maxcount:
                    # Run into a rare situation that there are more than
                    # maxcount records with the same timestamp. If this
                    # happens, just moves forward and ignores the other
                    # records with the same timestamp
                    _LOGGER.warn("{0} records with same timestamp={1}".format(maxcount, last_timestamp))
                    last_timestamp = datetime.strptime(last_timestamp,
                                                       "%Y-%m-%d %H:%M:%S")
                    last_timestamp = last_timestamp + timedelta(seconds=1)
                    last_timestamp = datetime.strftime(last_timestamp,
                                                       "%Y-%m-%d %H:%M:%S")
                    self.context[k]["last_collection_time"] = last_timestamp
                    del last_time_records[:]
                    refreshed = True
                    _LOGGER.warn("Progress to timestamp={}".format(last_timestamp))
        return jobjs, refreshed

    def _get_uri(self, table, params, limit):

        if self.filter_data:
            endpoint = ("api/now/table/{}?{}&sysparm_display_value={}"
                        "&sysparm_limit={}").format(table, self.filter_data, self._display_value,
                                                    limit)
        else:
            endpoint = ("api/now/table/{}?sysparm_display_value={}"
                        "&sysparm_limit={}").format(table, self._display_value,
                                                    limit)
        if params:
            params = ("&sysparm_exclude_reference_link=true"
                      "&sysparm_query={}").format(params)
        if params is None:
            params = ""
        rest_uri = "".join((self.host, endpoint, params))
        return rest_uri

    def _read_last_collection_time(self, input_name, timefield):
        k = ".".join((input_name, timefield))
        if not self.context.get(k, None):
            _LOGGER.debug("Checkpoint file {} not in cache, reloading from checkpoint file".format(k))
            ckpt = self._read_last_checkpoint(k)
            if not ckpt:
                self.context[k] = {"last_collection_time": self.since_when,
                                   "last_time_records": []}
        return self.context[k]["last_collection_time"].replace(" ", "+")

    def _read_last_checkpoint(self, input_name):
        fname = op.join(self.checkpoint_dir, input_name)
        try:
            with open(fname) as f:
                ckpt = json.load(f)
                assert ckpt["version"] == 1
                self.context[input_name] = ckpt
                return ckpt
        except (OSError, IOError):
            return None

    def _write_checkpoint(self, input_name, timefield, jobjs, refreshed=False):
        if not jobjs:
            return 1

        if not jobjs[-1].get(timefield):
            _LOGGER.error("'{}' field is not found in the data collected for '{}' input. "
                          "In order to resolve the issue, provide valid value in 'Time field of the table' on Inputs page, or "
                          "edit 'timefield' parameter for the affected input in inputs.conf file."
                          .format(timefield, input_name))
            return 0
        # Records already sorted by timestamp descending
        latest_timestamp = jobjs[-1][timefield]
        records = [obj[self.id_field] for obj in jobjs
                   if obj[timefield] == latest_timestamp]

        k = ".".join((input_name, timefield))
        fname = op.join(self.checkpoint_dir, k)
        with open(fname + ".new", "w") as f:
            ckpt = {
                "version": 1,
                "last_collection_time": latest_timestamp,
                "last_time_records": records,
            }
            json.dump(ckpt, f)

        ckpt_exist = op.exists(fname) and op.isfile(fname)
        if ckpt_exist:
            try:
                os.rename(fname, fname + ".old")
            except (OSError, IOError):
                _LOGGER.debug(traceback.format_exc())

        os.rename(fname + ".new", fname)

        if ckpt_exist:
            try:
                os.remove(fname + ".old")
            except (OSError, IOError):
                _LOGGER.debug(traceback.format_exc())

        if not refreshed:
            self.context[k] = ckpt

        return 1

    def is_alive(self):
        return 1

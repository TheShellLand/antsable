import base64
import json
import logging
import os
import os.path as op
import threading
import traceback
from datetime import datetime
from datetime import timedelta

import framework.log as log
import snow_consts as sc
from framework import rest
from framework import utils

_LOGGER = log.Logs().get_logger("main")


class _ObjectWrapper(object):

    def __init__(self, obj, table, endpoint, timefield):
        self.obj = obj
        self.table = table
        self.endpoint = endpoint
        self.timefield = timefield

    def to_string(self, idx, host, excludes=()):
        evt_fmt = ("<event><time>{0}</time><source>{1}</source>"
                   "<sourcetype>{2}</sourcetype><host>{3}</host>"
                   "<index>{4}</index><data>endpoint=\"{5}\",{6}</data>"
                   "</event>")
        tag_vals = ",".join(("{0}=\"{1}\"".format(
            k, str(v).replace('"', ""))
            for k, v in self.obj.iteritems()
            if k not in excludes))

        try:
            timestamp = datetime.strptime(self.obj[self.timefield],
                                          "%Y-%m-%d %H:%M:%S")
        except ValueError:
            timestamp = datetime.utcnow()
        return evt_fmt.format(utils.datetime_to_seconds(timestamp),
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
        if not host.startswith("https://"):
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
        for k, v in json_obj.iteritems():
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

    def collect_data(self, table, timefield, count=sc.DEFAULT_RECORD_LIMIT):
        assert table and timefield

        objs = []
        with self._lock:
            last_timestamp = self._read_last_collection_time(table, timefield)
            params = "{0}>={1}^ORDERBY{0}".format(timefield, last_timestamp)
            _, content = self._do_collect(table, params, limit=count)
            if not content:
                return

            jobjs = self._json_to_objects(content)
            records = jobjs.get("result")

            if not records:
                return

            if jobjs.get("error"):
                _LOGGER.error("Failed to get records from {0}{1}".format(
                    self.host, table))
                return

            records = self._flat_json_records(records)

            jobjs, refreshed = self._remove_collected_records(
                table, timefield, records, count)
            self._write_checkpoint(table, timefield, jobjs, refreshed)
        _LOGGER.info("Get %d records from %s%s", len(jobjs), self.host, table)
        objs.extend((_ObjectWrapper(obj, table, self.host, timefield)
                     for obj in jobjs))
        return {table: objs}

    def _do_collect(self, table, params, limit):
        rest_uri = self._get_uri(table, params, limit)

        http = rest.build_http_connection(
            self.config, self.config["duration"])
        _LOGGER.info("start %s", rest_uri)
        response, content = None, None
        try:
            credentials = base64.b64encode("%s:%s" % (self.config["username"],
                                                      self.config["password"]))
            response, content = http.request(rest_uri, headers={
                "Accept-Encoding": "gzip",
                "Accept": "application/json",
                "Authorization": "Basic %s" % credentials
            })

            if response.status not in (200, 201):
                _LOGGER.error("Failed to connect %s, reason=%s",
                              rest_uri, response.reason)
        except Exception:
            _LOGGER.error("Failed to connect %s, reason=%s",
                          rest_uri, traceback.format_exc())
        _LOGGER.info("end %s", rest_uri)
        return response, content

    @staticmethod
    def _json_to_objects(json_str):
        return json.loads(json_str)

    def _remove_collected_records(self, table, timefield, jobjs, maxcount):
        # Remove the records already collected
        k = ".".join((table, timefield))
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
                _LOGGER.debug("Last time reocords: %s with timestamp=%s. "
                              "Remove collected records: %s with the same "
                              "timestamp", last_time_records, last_timestamp,
                              records_to_be_removed)

                record_count = len(jobjs)
                jobjs = [jobj for jobj in jobjs
                         if jobj[self.id_field] not in records_to_be_removed]

                if _LOGGER.level == logging.DEBUG:
                    _LOGGER.debug("Left collected records: %s",
                                  [jobj[self.id_field] for jobj in jobjs])

                if all_records_has_same_timestamp and record_count == maxcount:
                    # Run into a rare situation that there are more than
                    # maxcount records with the same timestamp. If this
                    # happens, just moves forward and ignores the other
                    # records with the same timestamp
                    _LOGGER.warn("%d records with same timestamp=%s",
                                 maxcount, last_timestamp)
                    last_timestamp = datetime.strptime(last_timestamp,
                                                       "%Y-%m-%d %H:%M:%S")
                    last_timestamp = last_timestamp + timedelta(seconds=1)
                    last_timestamp = datetime.strftime(last_timestamp,
                                                       "%Y-%m-%d %H:%M:%S")
                    self.context[k]["last_collection_time"] = last_timestamp
                    del last_time_records[:]
                    refreshed = True
                    _LOGGER.warn("Progress to timestamp=%s", last_timestamp)
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

    def _read_last_collection_time(self, table, timefield):
        k = ".".join((table, timefield))
        if not self.context.get(k, None):
            _LOGGER.debug("%s not in cache, reload from checkpoint file", k)
            ckpt = self._read_last_checkpoint(k)
            if not ckpt:
                self.context[k] = {"last_collection_time": self.since_when,
                                   "last_time_records": []}
        return self.context[k]["last_collection_time"].replace(" ", "+")

    def _read_last_checkpoint(self, table):
        fname = op.join(self.checkpoint_dir, table)
        try:
            with open(fname) as f:
                ckpt = json.load(f)
                assert ckpt["version"] == 1
                self.context[table] = ckpt
                return ckpt
        except (OSError, IOError):
            return None

    def _write_checkpoint(self, table, timefield, jobjs, refreshed=False):
        if not jobjs:
            return

        # Records already sorted by timestamp descending
        latest_timestamp = jobjs[-1][timefield]
        records = [obj[self.id_field] for obj in jobjs
                   if obj[timefield] == latest_timestamp]

        k = ".".join((table, timefield))
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

    def is_alive(self):
        return 1

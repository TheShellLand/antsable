"""
Create scheduling jobs
"""

import socket

import framework.log as log
import snow_consts as sc
from snow_data_loader import Snow

_LOGGER = log.Logs().get_logger("main")

__all__ = ["JobFactory"]


class _CollectionJob(object):

    def __init__(self, config, endpoint, data_collect_func):
        self._config = config
        self._func = data_collect_func
        self._endpoint = endpoint
        if config.get("exclude", None):
            excludes = config["exclude"].lower().split(",")
            excludes = [ex.strip() for ex in excludes]
        else:
            excludes = ()
        self.excludes = excludes
        if not config.get("host", None):
            config["host"] = socket.gethostname()

    def __call__(self):
        config = self._config
        excludes = self.excludes
        _LOGGER.info("Start collecting from %s.", config["name"])
        results = self._func(config["name"],
                             config.get("timefield", "sys_updated_on"),
                             config.get("record_count",
                                        sc.DEFAULT_RECORD_LIMIT))
        idx = config.get("index", "main")
        host = config["host"]
        if results:
            event_queue = config["event_queue"]
            for _, data_objs in results.iteritems():

                if data_objs:
                    events = "".join(("<stream>%s</stream>"
                                      % obj.to_string(idx, host, excludes)
                                      for obj in data_objs))
                    event_queue.put(events)
        _LOGGER.info("End collecting from %s.", self._config["name"])

    def is_alive(self):
        return self._endpoint.is_alive()

    def get(self, key):
        return self._config[key]


class JobFactory(object):

    def create_job(self, config):
        """
        Create a job according to the config. The job object shall
        be callable and implement is_alive() interface which returns
        True if it is still valid else False
        """

        _LOGGER.info("creating job for %s", config["name"])
        return self._create_snow_job(config)

    @staticmethod
    def _create_snow_job(config):
        snow = Snow(config)
        return _CollectionJob(config, snow, snow.collect_data)

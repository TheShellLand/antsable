"""
Data Loader main entry point
"""


import multiprocessing
import threading
import Queue
import sys
import os.path as op
import ConfigParser

import framework.log as log
import framework.ta_consts as c


_LOGGER = log.Logs().get_logger(c.ta_util)


class DataLoader(object):
    """
    Data Loader boots all underlying facilities to handle data collection
    """

    def __init__(self, meta_configs, stanza_configs, job_factory):
        """
        @meta_configs: a dict like object, implement dict.get/[] like
        interfaces to get the value for a key. meta_configs shall at least
        contain
        {"server_uri": uri, "checkpoint_dir": dir, "session_key": key}
        key/value pairs
        @stanza_configs: a list like object containing a list of dict
        like object. Each element shall implement dict.get/[] like interfaces
        to get the value for a key. Each element in the list shall at least
        contain
        {"duration": an_duration_int} key/value pair
        @job_factory: an object which creates jobs. Shall implement
        create_job(stanza_config) interface and return an callable object
        """

        import thread_pool as tp
        import job_scheduler as js
        import timer_queue as tq

        self.settings = self._read_default_settings()
        self.meta_configs = meta_configs
        self.event_queue = Queue.Queue()
        self.wakeup_queue = Queue.Queue()
        self._set_event_queue(stanza_configs)
        pool_size = self._get_pool_size(stanza_configs)
        self.io_pool = tp.ThreadPool(pool_size)
        self.cpu_pool = self._create_process_pool()
        self.scheduler = js.JobScheduler(job_factory, stanza_configs)
        self.event_reporter = threading.Thread(target=self._output_events)
        self.event_reporter.daemon = True
        self.timer_queue = tq.TimerQueue()
        self._started = False

    def run(self):
        if self._started:
            return
        self._started = True

        self.io_pool.start()
        self.event_reporter.start()
        self.timer_queue.start()

        scheduler = self.scheduler
        io_pool = self.io_pool
        event_queue = self.event_queue
        wakeup_q = self.wakeup_queue
        while 1:
            (sleep_time, jobs) = scheduler.get_ready_jobs()
            io_pool.enqueue_funcs(jobs)
            try:
                go_exit = wakeup_q.get(timeout=sleep_time)
            except Queue.Empty:
                pass
            else:
                if go_exit:
                    break

        _LOGGER.info("Data loader is going to exit...")
        io_pool.tear_down()
        if self.cpu_pool:
            self.cpu_pool.tear_down()
        event_queue.put(None)
        self.timer_queue.tear_down()

    def tear_down(self):
        self.wakeup_queue.put(True)

    def run_computing_job(self, func, args=(), kwargs={}):
        if self.cpu_pool:
            return self.cpu_pool.apply(func, args, kwargs)
        else:
            return func(*args, **kwargs)

    def run_computing_job_async(self, func, args=(), kwargs={}, callback=None):
        assert self.cpu_pool is not None
        return self.cpu_pool.apply_async(func, args, kwargs, callback)

    def add_timer(self, callback, when, interval):
        return self.timer_queue.add_timer(callback, when, interval)

    def remove_timer(self, timer):
        self.timer_queue.remove_timer(timer)

    def _output_events(self):
        event_queue = self.event_queue
        write = sys.stdout.write
        flush = sys.stdout.flush
        while 1:
            event = event_queue.get()
            if event is not None:
                write(event)
                flush()
            else:
                break
        _LOGGER.info("Event writer thread is going to exit...")

    def _get_pool_size(self, configs):
        if self.settings["thread_num"] > 0:
            pool_size = self.settings["thread_num"]
        else:
            cpu_count = multiprocessing.cpu_count()
            pool_size = sum((1 for config in configs
                             if config["duration"] != 0))
            if pool_size / cpu_count > 8:
                pool_size = cpu_count * 8
        _LOGGER.info("thread_pool_size = %d", pool_size)
        return pool_size

    def _set_event_queue(self, configs):
        for config in configs:
            config["event_queue"] = self.event_queue

    def _create_process_pool(self):
        if self.settings["process_num"] == 0:
            proc_count = 0
        elif self.settings["process_num"] > 0:
            proc_count = self.settings["process_num"]
        else:
            proc_count = multiprocessing.cpu_count()
            if proc_count > 3:
                proc_count = proc_count - 2
            else:
                proc_count = 1

        _LOGGER.info("process_pool_size = %d", proc_count)

        if proc_count > 0:
            import process_pool as pp
            return pp.ProcessPool(proc_count)
        else:
            return None

    @staticmethod
    def _read_default_settings():
        cur_dir = op.dirname(op.abspath(__file__))
        setting_file = op.join(cur_dir, "setting.conf")
        parser = ConfigParser.ConfigParser()
        parser.read(setting_file)
        settings = {}
        for option in ("process_num", "thread_num"):
            try:
                settings[option] = parser.get("global", option)
            except ConfigParser.NoOptionError:
                settings[option] = -1

            if settings[option] == "dynamic":
                settings[option] = -1

            try:
                settings[option] = int(settings[option])
            except ValueError:
                settings[option] = -1
        _LOGGER.debug("settings:%s", settings)
        return settings


class GlobalDataLoader(object):
    """ Singleton, inited when started"""

    __instance = None

    @staticmethod
    def get_data_loader(meta_configs, stanza_configs, job_factory):
        if GlobalDataLoader.__instance is None:
            GlobalDataLoader.__instance = DataLoader(meta_configs,
                                                     stanza_configs,
                                                     job_factory)
        return GlobalDataLoader.__instance

    @staticmethod
    def reset():
        GlobalDataLoader.__instance = None

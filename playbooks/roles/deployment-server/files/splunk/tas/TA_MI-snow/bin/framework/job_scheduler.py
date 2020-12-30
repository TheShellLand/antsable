"""
A simple scheduler which schedules the periodic or once job
"""

from heapq import (heapify, heappush, heappop)
from time import time
import random

import framework.log as log
import framework.ta_consts as c


_LOGGER = log.Logs().get_logger(c.ta_util)


class JobScheduler(object):
    """
    A simple scheduler which schedules the periodic or once job
    """

    def __init__(self, job_factory, configs):
        """
        @job_factory: an object which creates jobs. Shall implement
        create_job(config) interface and return an callable object. The
        returned job object shall implement dict.get like interface, and shall
        support get("name") => string, get("duration") => int,
        get("priority") => int, and implements is_alive() => boolean interfaces
        @configs: a list of dict like objects
        """
        self.job_factory = job_factory
        self.job_heap = None
        self.update_jobs(configs)

    def get_ready_jobs(self):
        """
        @return: a 2 element tuple. The first element is the next ready
                 duration. The second element is ready jobs list
        """

        job_heap = self.job_heap
        now = time()
        ready_jobs = []
        sleep_time = 1
        while job_heap:
            if job_heap[0][0] <= now:
                job = heappop(job_heap)
                if job[1].is_alive():
                    ready_jobs.append(job[1])
                    if job[1].get("duration") != 0:
                        # repeated job, calculate next due time and enqueue
                        job[0] = now + job[1].get("duration")
                        heappush(job_heap, job)
                else:
                    _LOGGER.warn("Removing dead endpoint: %s",
                                 job[1].get("name"))
            else:
                sleep_time = job_heap[0][0] - now
                break
        _LOGGER.info(("Get %d ready jobs, next duration is %f, "
                      "and there are %s jobs scheduling"),
                     len(ready_jobs), sleep_time, len(job_heap))

        ready_jobs.sort(key=lambda job: job.get("priority"), reverse=True)
        return (sleep_time, ready_jobs)

    def update_jobs(self, configs):
        """
        Create new jobs according to configs
        """

        jobs = (self.job_factory.create_job(config) for config in configs)
        now = time()
        self.job_heap = [[now + random.randrange(0, 60), job] for job in jobs]
        heapify(self.job_heap)

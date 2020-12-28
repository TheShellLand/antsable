"""
A wrapper of multiprocessing.pool
"""

import multiprocessing

import framework.log as log
import framework.ta_consts as c


_LOGGER = log.Logs().get_logger(c.ta_util)


class ProcessPool(object):
    """
    A simple wrapper of multiprocessing.pool
    """

    def __init__(self, min_size=0, maxtasksperchild=10000):
        if min_size <= 0:
            min_size = multiprocessing.cpu_count()
        self.size = min_size
        self._pool = multiprocessing.Pool(processes=min_size,
                                          maxtasksperchild=maxtasksperchild)

    def tear_down(self):
        """
        Tear down the pool
        """

        _LOGGER.info("ProcessPool is going to exit...")
        self._pool.close()
        self._pool.join()

    def apply(self, func, args=(), kwargs={}):
        """
        Run the job synchronously
        """

        return self._pool.apply(func, args, kwargs)

    def apply_async(self, func, args=(), kwargs={}, callback=None):
        """
        Run the job asynchronously
        """

        return self._pool.apply_async(func, args, kwargs, callback)

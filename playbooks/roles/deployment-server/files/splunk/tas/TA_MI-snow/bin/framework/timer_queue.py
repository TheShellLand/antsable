"""
A timer queue implementation
"""

import bisect
import threading
import Queue
from time import time

import framework.log as log
import framework.ta_consts as c


_LOGGER = log.Logs().get_logger(c.ta_util)


class Timer(object):
    """
    Timer wraps the callback and timestamp related stuff
    """

    ident = 0
    _lock = threading.Lock()

    def __init__(self, callback, when, interval):
        self.callback = callback
        self.when = when
        self.interval = interval
        with Timer._lock:
            self.ident = Timer.ident + 1
            Timer.ident = Timer.ident + 1

    def __cmp__(self, other):
        if self.when == other.when:
            return 0
        elif self.when < other.when:
            return -1
        else:
            return 1

    def __call__(self):
        self.callback()


class TimerQueue(object):
    """
    A timer queue implementation, runs a separate thread to handle timers
    """

    def __init__(self):
        self._timers = []
        self._cancelling_timers = {}
        self._lock = threading.Lock()
        self._wakeup_queue = Queue.Queue()
        self._thr = threading.Thread(target=self._check_and_execute)
        self._thr.daemon = True

    def start(self):
        """
        Start the timer queue to make it start function
        """

        self._thr.start()

    def add_timer(self, callback, when, interval):
        """
        Add timer to the queue
        """

        timer = Timer(callback, when, interval)
        with self._lock:
            bisect.insort_right(self._timers, timer)
        self._wakeup()
        return timer

    def remove_timer(self, timer):
        """
        Remove timer from the queue. For now O(n*n) complexity
        """

        # FIX ME, for now, O(n) algorithm
        with self._lock:
            for i, this_timer in enumerate(self._timers):
                if timer.ident == this_timer.ident:
                    self._timers.pop(i)
                    break
            else:
                self._cancelling_timers[timer.ident] = timer

    def _check_and_execute(self):
        wakeup_queue = self._wakeup_queue
        while 1:
            (next_expired_time, expired_timers) = self._get_expired_timers()
            for timer in expired_timers:
                try:
                    timer()
                except Exception:
                    import traceback
                    _LOGGER.error(traceback.format_exc())

            self._reset_timers(expired_timers)

            # Calc sleep time
            if next_expired_time:
                now = time()
                if now < next_expired_time:
                    sleep_time = next_expired_time - now
                else:
                    sleep_time = 0.1
            else:
                sleep_time = 1

            try:
                wakeup = wakeup_queue.get(timeout=sleep_time)
                if wakeup is None:
                    break
            except Queue.Empty:
                pass
        _LOGGER.info("TimerQueue thread is going to exit...")

    def _get_expired_timers(self):
        next_expired_time = 0
        now_timer = Timer(None, time(), 0)
        with self._lock:
            timers = self._timers
            idx = bisect.bisect(timers, now_timer)
            expired_timers = timers[:idx]
            del timers[:idx]
            if timers:
                next_expired_time = timers[0].when
        return (next_expired_time, expired_timers)

    def _reset_timers(self, expired_timers):
        now = time()
        has_new_timer = False
        with self._lock:
            cancelling_timers = self._cancelling_timers
            for timer in expired_timers:
                if timer.ident in cancelling_timers:
                    continue
                elif timer.interval:
                    # Repeated timer
                    timer.when = now + timer.interval
                    bisect.insort_right(self._timers, timer)
                    has_new_timer = True
            cancelling_timers.clear()

        if has_new_timer:
            self._wakeup()

    def _wakeup(self, something="not_None"):
        self._wakeup_queue.put(something)

    def tear_down(self):
        self._wakeup(None)

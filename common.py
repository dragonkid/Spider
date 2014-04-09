#!/usr/bin python
# -*- coding: UTF-8 -*-

import time
from threading import Thread, Event


class Timer(object):
    """
    this class used for test performance on time.
    """
    def __init__(self, verbose=True):
        self.__verbose = verbose

    def __enter__(self):
        self.__start = time.time()
        return self

    def __exit__(self, *args):
        self.__end = time.time()
        self.secs = self.__end - self.__start
        self.msecs = self.secs * 1000  # millisecs
        if self.__verbose:
            print 'time costs: %f ms' % self.msecs


# exceptions
class ParameterInvalid(Exception):
    """
    raise when parameters invalid.
    """
    pass


class RepeatTimer(Thread):
    def __init__(self, func, interval, counts=0, args=[], kwargs={}):
        """
        @param func: function invoked at a configureble interval by a looping thread.
        @param interval: invoke interval. must be positive or zero.
        @param counts: invoke counts. must be positive or zero.
                       if zero, continual until cancle called.
        """
        if not callable(func) or interval < 0 or counts < 0:
            raise ParameterInvalid
        Thread.__init__(self)
        self.__func = func
        self.__interval = interval
        self.__counts = counts
        self.__args = args
        self.__kwargs = kwargs
        self.__finished = Event()
        self.setName('RepeatTimer')
        # set daemon true for terminate RepeatTimer when main thread exit.
        self.setDaemon(True)
        self.start()

    def cancle(self):
        self.__finished.set()

    def run(self):
        count = 0
        while self.__counts == 0 or self.__counts > count:
            self.__finished.wait(self.__interval)
            if self.__finished.is_set():
                break
            self.__func(*self.__args, **self.__kwargs)
            count += 1

if __name__ == '__main__':
    a = ['aaaa']
    b = ['bbbb']
    c = ['cccc']
    with Timer() as t:
        c = a + b + c
    a = ['aaaa']
    b = ['bbbb']
    c = ['cccc']
    with Timer() as t:
        c.extend(a)
        c.extend(b)
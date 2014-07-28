#!/usr/bin python
# -*- coding: UTF-8 -*-

from threading import Thread, Event
import time


def get_root():
    '''
    get root permission. make *.py can be executed without 'sudo python'.
    but there is some problem when using this in eclipse console and python idle.
    '''
    import os
    import sys
    if os.geteuid():
        args = [sys.executable] + sys.argv
        os.execlp('sudo', 'sudo', *args)


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
class ParaError(Exception):
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
        """
        if not callable(func) or interval < 0 or counts < 0:
            raise ParaError
        Thread.__init__(self)
        self.__func = func
        self.__interval = interval
        self.__counts = counts
        self.__args = args
        self.__kwargs = kwargs
        self.__finished = Event()
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


def timeout_limit(func, args, seconds, default=None):
    """
    限制func执行的最大超时时长, 如果超过这个时间, 就返回default.
    """
    ret = []

    def inner():
        try:
            ret.append(func(args))
        except Exception, e:
            # do something
            pass

    t = Thread(target=inner)
    t.setDaemon(True)
    t.start()
    t.join(seconds)

    if not t.isAlive() and len(ret):
        return ret.pop()
    return default

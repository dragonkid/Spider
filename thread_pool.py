#!/usr/bin python
# -*- coding: UTF-8 -*-

import sys
import threading
import Queue
import traceback

from logger import logger

_TIMEOUT = 10  # default timeout


# execptions
class NoResultsPending(Exception):
    """
    all requests have been processed.
    """
    pass


class NoWorkerAvaliable(Exception):
    """
    no worker threads avaliable to process remaining requests.
    """
    pass


# used only in moudle.
def _handle_thread_exception(request, exc_info):
    """
    print the execeptions.
    """
    traceback.print_exception(*exc_info)


# classes
class DownloadRequest(object):
    """
    @param callable: function want to execute.
    @param args: list param.
    @param kwds: dict param.
    @param exception: True if this request get an exception.
    """
    def __init__(self, callable_, args=[], kwds={}, \
                 callback=None, excCallback=_handle_thread_exception, \
                 reqLevel=1):
        self._requestID = id(self)
        self.exception = False
        self.callable = callable_
        self.args = args
        self.kwds = kwds
        self.callback = callback
        self.excCallback = excCallback
        self.reqLevel = reqLevel

    def __str__(self):
        return "DownloadRequest:\n id = %s\n exception = %s\n args = %r\n kwds = %r"\
                % self._requestID, self.exception, self.args, self.kwds


class WorkerThread(threading.Thread):
    """
    the real working thread.
    get requests from requestQueue, and put results into resultQueue.
    WorkerThread will __start work immediately when it was created.
    """
    def __init__(self, reqQueue, respQueue, timeout=_TIMEOUT, **kwargs):
        threading.Thread.__init__(self, **kwargs)
        # set as daemon.
        self.setDaemon(False)
        self._reqQueue = reqQueue
        self._respQueue = respQueue
        self._timeout = timeout
        # set a flag to indicate whether this worker still working.
        self.__start()

    def run(self):
        """
        every worker process requests as more as it run.
        """
        logger.debug('thread working.')
        while True:
            try:
                request = self._reqQueue.get(True, self._timeout)
                logger.debug('get request from reqQueue. reqQueue size: %d', self._reqQueue.qsize())
            except Queue.Empty:
                logger.info('still no request pending.')
                break
            except:
                logger.error('get from reqQueue raise other exceptions.')
                break
            try:
                result = request.callable(*request.args, **request.kwds)
                self._respQueue.put((request, result))
#                 self._reqQueue.task_done()
            except:
                request.exception = True
                # exc_info() -> (type, value, traceback).
                # just the params print_exception needed.
                self._respQueue.put((request, sys.exc_info()))
        logger.debug('thread exit.')


class Scheduler(object):
    """
    @param poolSize: number of threads will be created when initialize.
    @param reqSize: size of request queue.
    @param respSize: size of response queue.
    @param timeout: it will work when too many requests were pulled in the request queue.
    """
    def __init__(self, poolSize, reqSize=0, respSize=0, timeout=_TIMEOUT):
        self._reqQueue = Queue.Queue(reqSize)
        self._respQueue = Queue.Queue(respSize)
        self._workers = []
        self.__createWorkers(poolSize, timeout)

    def __createWorkers(self, num, timeout):
        """
        create 'num' WorkerThreads, and set the timeout 'timeout'.
        WorkerThread has started to handle requests when it was append to _workers.
        """
        for _ in range(num):
            self._workers.append(WorkerThread(self._reqQueue, self._respQueue, timeout))

    def processing(self, level=1):
        while True:
            try:
                (request, result) = self._respQueue.get(False)
                logger.debug('get response from respQueue. respQueue size: %d', self._respQueue.qsize())
                if request.exception and request.excCallback:
                    request.excCallback(request, result)
                elif request.callback:
                    urls = request.callback(request, result)
                    # processing end condition.
                    if level == request.reqLevel:
                        continue
                    if not urls:
                        continue
                    for url in urls:
                        nextReq = DownloadRequest(callable_=request.callable, \
                                              args=[url], callback=request.callback,\
                                              reqLevel=request.reqLevel+1)
                        self.putRequest(nextReq)
            except Queue.Empty:
#                 logger.debug('respQueue is empty.')
                break

    def putRequest(self, request, block=True, timeout=_TIMEOUT):
        assert isinstance(request, DownloadRequest)
        try:
            self._reqQueue.put(request, block, timeout)
        except Queue.Full:
            logger.warning('request queue is full.')

    def workerAliveSize(self):
        count = 0
        for worker in self._workers:
            if worker.is_alive():
                count += 1
        return count

# test
if __name__ == '__main__':
    import time
    import random
    import datetime

    def doWork(data):
        time.sleep(random.randint(1, 3))
        res = str(datetime.datetime.now()) + "" + str(data)
        return res

    def printResult(request, result):
        print 'Result from request %s: %r' % (request._requestID, result)

    main = Scheduler(3)
    for i in range(10):
        req = DownloadRequest(doWork, args=[i], callback=printResult)
        main.putRequest(req)

    print '-' * 20, main.workerAliveSize(), '-' * 20

    while True:
        main.processing(2)
        if main.workerAliveSize() == 0:
            break
    logger.debug('main thread exit.')
# end

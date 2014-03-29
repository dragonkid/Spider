import sys
import threading
import Queue
import traceback

# __name__ == 'threadpool'
__name__ == '__main__'

_TIMEOUT = 10   # default timeout

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
class WorkRequest(object):
    """
    @param callable: function want to execute.
    @param args: list param.
    @param kwds: dict param.
    @param exception: True if this request get an exception.
    """
    def __init__(self, callable_, args=[], kwds={}, \
                 callback=None, excCallback=_handle_thread_exception):
        self._requestID = id(self)
        self.exception = False
        self.callable = callable_
        self.args = args
        self.kwds = kwds
        self.callback = callback
        self.excCallback = excCallback

    def __str__(self):
        return "WorkRequest:\n id = %s\n exception = %s\n args = %r\n kwds = %r"\
                % self._requestID, self.exception, self.args, self.kwds

class WorkerThread(threading.Thread):
    """
    the real working thread.
    get requests from requestQueue, and put results into resultQueue.
    WorkerThread will start work immediately when it was created.
    """
    def __init__(self, reqQueue, respQueue, timeout = _TIMEOUT, **kwargs):
        threading.Thread.__init__(self, **kwargs)
        # set as daemon.
        self.setDaemon(True)
        self._reqQueue = reqQueue
        self._respQueue = respQueue
        self._timeout = timeout
        # set a flag to indicate whether this worker still working.
        self._dismissed = threading.Event()
        self.start()

    def run(self):
        """
        every worker process requests as more as it can.
        """
        while True:
            if self._dismissed.is_set():
                break
            try:
                request = self._reqQueue.get(True, self._timeout)
            except Queue.Empty:
                continue
            # it may be dismissed during timeout, so rejudge the Event.
            if self._dismissed.is_set():
                self._reqQueue.put(request)
                break
            try:
                result = request.callable(*request.args, **request.kwds)
                print self.getName()
                self._respQueue.put((request, result))
            except:
                request.exception = True
                # exc_info() -> (type, value, traceback). just the params print_exception needed.
                self._respQueue.put((request, sys.exc_info()))

    def dismiss(self):
        """
        set the Event.
        """
        self._dismissed.set()

class ThreadPool(object):
    """
    @param poolSize: number of threads will be created when initialize.
    @param reqSize: size of request queue.
    @param respSize: size of response queue.
    @param timeout: it will work when too many requests were pulled in the request queue.
    """
    def __init__(self, poolSize, reqSize = 0, respSize = 0, timeout = _TIMEOUT):
        self._reqQueue = Queue.Queue(reqSize)
        self._respQueue = Queue.Queue(respSize)
        self._workers = []
        self._dismissedWorkers = []
        self._workRequests = {}
        self.createWorkers(poolSize, timeout)

    def createWorkers(self, num, timeout):
        """
        create 'num' WorkerThreads, and set the timeout 'timeout'.
        WorkerThread has started to handle requests when it was append to _workers.
        """
        for _ in range(num):
            self._workers.append(WorkerThread(self._reqQueue, self._respQueue, timeout))

    def dismissWorkers(self, num, doJoin = False):
        __dismissList = []
        # min(num, len(self._workers)) used to avoid access out of range.
        for _ in range(min(num, len(self._workers))):
            worker = self._workers.pop()
            worker.dismiss()
            __dismissList.append(worker)
        if doJoin:
            for worker in __dismissList:
                worker.join()
        else:
            self._dismissedWorkers.extend(__dismissList)

    def joinAllDismissedWorkers(self):
        for worker in self._dismissedWorkers:
            worker.join()
        self._dismissedWorkers = []

    def putRequest(self, request, block = True, timeout = _TIMEOUT):
        assert isinstance(request, WorkRequest)
        self._reqQueue.put(request, block, timeout)
        self._workRequests[request._requestID] = request

    def poll(self, block = True):
        while True:
            if not self._workRequests:
                raise NoResultsPending
            elif block and not self._workers:
                raise NoWorkerAvaliable
            try:
                (request, result) = self._respQueue.get(block)
                if request.exception and request.excCallback:
                    request.excCallback(request, result)
                elif request.callback:
                    request.callback(request, result)
                del self._workRequests[request._requestID]
            except Queue.Empty:
                break
    
    def wait(self):
        while True:
            try:
                # must block here. in order to wait for all workers finish there work.
                self.poll(True)
            except NoResultsPending:
                break
    
    def workerSize(self):
        return len(self._workers)
    
    def stop(self):
        self.dismissWorkers(self.workerSize(), True)
        self.joinAllDismissedWorkers()
        
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
        print '---Result from request %s: %r' % (request._requestID, result)
        
    main = ThreadPool(3)
    for i in range(40):
        req = WorkRequest(doWork, args = [i], callback = printResult)
        main.putRequest(req)
        print 'Work request #%s added.' % req._requestID
        
    print '-' * 20, main.workerSize(), '-' * 20
    
    counter = 0
    while True:
        try:
            time.sleep(0.5)
            main.poll()
            print 'Main thread working...'
            print '(Active worker threads: %i)' % threading.activeCount() - 1
            if 10 == counter:
                print 'Add 3 more working threads.'
                main.createWorkers(3)
                print '-' * 20, main.workerSize(), '-' * 20
            if 20 == counter:
                print 'Dismiss 2 working threads.'
                main.dismissWorkers(2)
                print '-' * 20, main.workerSize(), '-' * 20
            counter += 1
        except KeyboardInterrupt:
            print '**** Interrupted!'
            break;
        except NoResultsPending:
            print '**** No pending results.'
            break;
    main.dismissWorkers(threading.activeCount() - 1)
    main.joinAllDismissedWorkers()
# end              
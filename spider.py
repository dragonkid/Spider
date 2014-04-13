#!/usr/bin python
# -*- coding: UTF-8 -*-

"""
spider the 'url' into level 'deep',
and get the pages which match the 'key'.

use like this:
>>> scheduler = initSpider(5, 1, u'')
>>> scheduler.processing()
"""

# import std module.
import threading
import Queue
import traceback
import urllib2
import re
import time

# import my module.
from logger import logger
import dboperate
from common import RepeatTimer

#defines
_ORIGIN_URL = 'http://sina.com.cn'
_HEADERS = {
           'User-Agent': 'Mozilla/5.0 (Windows; U; Windows NT 6.1; \
                          en-US; rv:1.9.1.6) Gecko/20091201 Firefox/3.5.6'
           }
_TIMEOUT = 20  # default timeout

# condition variables of spider.
_KEY = ''
_LEVEL = 1


def initSpider(poolSize, level, key):
    """
    @param poolSize: num of downloaders.
    @param level: level in breadth-first traversal which processing to.
    @param key: key to match.
    @return: scheduler of spider.
    """
    global _LEVEL
    global _KEY
    _LEVEL = level
    _KEY = key
    scheduler = Scheduler(poolSize)
    firstReq = DownloadRequest(_ORIGIN_URL)
    scheduler.putRequest(firstReq)
    RepeatTimer(func=scheduler.getProcessState, interval=10)
    return scheduler


def spider(poolSize=5, level=1, key='', dbfile='', url=''):
    if url:
        _ORIGIN_URL = url
    print 'spider start to work.'
    scheduler = initSpider(poolSize, level, key)
    scheduler.processing()
    dbopt = dboperate.DBOperation(dbfile)
    dbopt.insertMany(scheduler.resultBuf)
    print 'spider end to work.'


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


class ParameterInvalid(Exception):
    """
    raise when parameters invalid.
    """
    pass


# classes
class DownloadRequest(object):
    def __init__(self, url, urlLevel=1):
        """
        @param url: url want to download.
        @param urlLevel: breadth-first traversal of urls,
                         indicate the level of url.
        """
        self.__requestID = id(self)
        self.url = url
        self.urlLevel = urlLevel

    def __str__(self):
        return "\nDownloadRequest: id = %s; urlLevel = %d;\nurl = %s"\
                % self.__requestID, self.exception, self.urlLevel, self.url


class Downloader(threading.Thread):
    """
    the real working thread.
    get download request from reqQueue, and put results into respQueue.
    Downloader will start to work immediately when it was created.
    """
    def __init__(self, reqQueue, respQueue, timeout=_TIMEOUT):
        threading.Thread.__init__(self)
        # set as daemon.
        self.setDaemon(True)
        self.__reqQueue = reqQueue
        self.__respQueue = respQueue
        self.__timeout = timeout
        self.event = threading.Event()
        # set a flag to indicate whether this worker still working.
        self.start()

    def run(self):
        """
        every worker process requests as more as it run.
        """
        logger.debug('thread working.')
        while True:
            if self.event.is_set():
                # interrupted by stop function.
                break
            try:
                downloadReq = self.__reqQueue.get(True, self.__timeout)
                logger.debug('get request from reqQueue. reqQueue size: %d', \
                             self.__reqQueue.qsize())
            except Queue.Empty:
                logger.info('still no request pending.')
                break
            content = self.__downloadHtml(downloadReq.url)
            if content:
                self.__respQueue.put((downloadReq, content))
        logger.debug('thread exit.')

    def __downloadHtml(self, url):
        """
        download the content from url.
        @param url: url which you want to get content from it.
        @return: content get from url.
        """
        if not re.match(u'^https?://.*?$', url):
            return u''
        req = urllib2.Request(url=url, headers=_HEADERS)
        try:
            # must set timeout. if not, thread may block here.
            resp = urllib2.urlopen(req, timeout=_TIMEOUT)
        except:
            logger.error('url %s open error.', url)
            return u''
        headers = resp.info()
        try:
            content = resp.read()
        except:
            logger.error('read response of urlopen timeout. url = %s', url)
            return u''
        # get whether content encoded by gzip, if encoded , decode it.
        if ('Content-Encoding' in headers)\
            and (headers['Content-Encoding'].lower() == 'gzip'):
            logger.debug('content encoded by gzip.')
            import gzip
            import StringIO
            fileobj = StringIO.StringIO(content)
            gzipFile = gzip.GzipFile(fileobj=fileobj)
            content = gzipFile.read()
            gzipFile.close()
        # decode the content by character set of the page.
        try:
            content = content.decode('GB18030')
        except:
            try:
                content = content.decode('utf-8')
            except:
                logger.error('decode failed.')
                return u''
        logger.info('html download complete.')
        return content


class Parser(object):
    """
    parse the content.
    get urls in this content, and match the key in content.
    """
    def __init__(self, content):
        """
        @param content: html content.
        """
        if not content:
            raise ParameterInvalid
        self.__content = content

    def getUrls(self):
        """
        get urls from content.
        now can only get the value of attribute 'href' in label 'a'.
        the ability of wipping out invalid url is weak.
        @param content: html content.
        @return: urls
        """
        # get label 'a' has attribute 'href'.
        urlPattern = re.compile(u'<a .*?href="(https?://.*?)".*?>')
        urls = urlPattern.findall(self.__content)
        logger.info('urls length: %d\nurls: \n%r', len(urls), str(urls))
        return urls

    def ifMatched(self, key):
        """
        only match the key in label title, keywords and description.
        @param key: key which you want to match in content.
                    if key is empty, all matched.
        @return: True if matched, False if not.
        """
        # if key is empty, all matched.
        if not key:
            return True
        titlePattern = re.compile(u'<title>(\S*?)</title>')
        titles = titlePattern.findall(self.__content)
        keyPattern = re.compile(u'<meta name="keywords" content="(\S*?)" />')
        keywords = keyPattern.findall(self.__content)
        descPattern = re.compile(u'<meta name="description" content="(\S*?)" />')
        descriptions = descPattern.findall(self.__content)
        textInLable = titles + keywords + descriptions
        text = u','.join(textInLable)
        logger.debug(text)
        if text.find(key):
            return True
        else:
            return False


class Scheduler(object):
    """
    @param poolSize: number of threads will be created when initialize.
    @param reqSize: size of request queue.
    @param respSize: size of response queue.
    @param timeout: it will work when too many requests were pulled in the request queue.
    """
    def __init__(self, poolSize, reqSize=0, respSize=0, timeout=_TIMEOUT):
        self.__reqQueue = Queue.Queue(reqSize)
        self.__respQueue = Queue.Queue(respSize)
        self.__downloaders = []
        self.__start = time.time()
        # buffer results, write to DB at the end.
        self.resultBuf = []
        self.__createWorkers(poolSize, timeout)

    def __createWorkers(self, num, timeout):
        """
        create 'num' Downloaders, and set the timeout by 'timeout'.
        Downloader has started to handle requests when it was append to __downloaders.
        """
        for _ in range(num):
            self.__downloaders.append(Downloader(self.__reqQueue, self.__respQueue, timeout))

    def __handleException(self, exc_info):
        """
        print the execeptions.
        """
        traceback.print_exception(*exc_info)

    def processing(self):
        while True:
            try:
                (request, content) = self.__respQueue.get(True, 1)
                logger.debug('get response from respQueue. respQueue size: %d',\
                             self.__respQueue.qsize())
            except Queue.Empty:
                # end of the processing.
                # in this case, no downloader(all finished because of no more requests)
                # continually put content into response queue.
                if self.downloadersAlived() == 0:
                    print 'total time costs: %s' % unicode(time.time() - self.__start)
                    break
                continue
            parser = Parser(content)
            if parser.ifMatched(_KEY) and isinstance(content, unicode):
                self.resultBuf.append((request.url, content))
            # get urls in next level or not.
            if _LEVEL == request.urlLevel:
                continue
            urls = parser.getUrls()
            if not urls:
                continue
            for url in urls:
                nextReq = DownloadRequest(url, request.urlLevel+1)
                self.putRequest(nextReq)

    def stop(self):
        for downloader in self.__downloaders:
            if downloader.is_alive():
                downloader.event.set()

    def putRequest(self, request, block=True, timeout=_TIMEOUT):
        assert isinstance(request, DownloadRequest)
        try:
            self.__reqQueue.put(request, block, timeout)
        except Queue.Full:
            logger.warning('request queue is full.')

    def downloadersAlived(self):
        """
        @return: the num of downloaders still alived.
        """
        count = 0
        for downloader in self.__downloaders:
            if downloader.is_alive():
                count += 1
        return count

    def getProcessState(self):
        state = u'Process state:'\
                + u'\n\tDownloaders alived: ' + unicode(self.downloadersAlived())\
                + u'\n\tRequest queue size: ' + unicode(self.__reqQueue.qsize())\
                + u'\n\tResponse queue size: ' + unicode(self.__respQueue.qsize())\
                + u'\n\tResult size: ' + unicode(len(self.resultBuf))\
                + u'\n\tTime costs:' + unicode(time.time() - self.__start)\
                + u'\n'
        print state


def _test():
    import doctest
    doctest.testmod()

if __name__ == '__main__':
    _test()

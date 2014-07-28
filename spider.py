#!/usr/bin python
# -*- coding: UTF-8 -*-

import urllib2
import re

from thread_pool import Scheduler, WorkRequest
from logger import logger
import dboperate


# defines
_ORIGIN_URL = 'http://sina.com.cn'
_HEADERS = {
           'User-Agent': 'Mozilla/5.0 (Windows; U; Windows NT 6.1; en-US; rv:1.9.1.6) \
                           Gecko/20091201 Firefox/3.5.6'
           }
_CHARACTER_SET = 'GB18030'
_KEY = ''
_TIMEOUT = 10


# functions
def setKey(key):
    _KEY = key


def getUrls(content=''):
    """
    get urls from content.
    now can only get the value of attribute 'href' in label 'a'.
    the ability of wipping out invalid url is weak.
    @param bs: BeautifulSoup object constructed by html content.
    @return: urls
    """
    # get label 'a' has attribute 'href'.
    urlPattern = re.compile(u'<a .*?href="(https?://.*?)".*?>')
    urls = urlPattern.findall(content)
    logger.info('urls length: %d\nurls: \n%r', len(urls), str(urls))
    return urls


def ifMatched(content, key):
    """
    only match the key in label title, keywords and description.
    @param bs: BeautifulSoup object constructed by html content.
    @param key: key to match.
    @return: True if matched, False if not.
    """
    titles = re.compile(u'<title>(\S*?)</title>').findall(content)
    keywords = re.compile(u'<meta name="keywords" content="(\S*?)" />').findall(content)
    descriptions = re.compile(u'<meta name="description" content="(\S*?)" />').findall(content)
    textInLable = []
    textInLable.extend(titles)
    textInLable.extend(keywords)
    textInLable.extend(descriptions)
    text = ','.join(textInLable)
    logger.debug(text)
    if text.find(key):
        return True
    else:
        return False


def parseContent(request, content='', key=_KEY):
    """
    parse the content.
    get urls in this content, and match the key in content.
    if matched, insert this url into table in db.
    @param content: content content.
    @param key: key which you want to match in content.
    @return: urls
    """
    global results
    if not content:
        return
    # match the key.
    if not key or ifMatched(content, key):
        # insert into results.
        logger.debug('key matched.')
        if isinstance(content, unicode):
            results.append((request.args[0], content))
    # get urls.
    urls = getUrls(content)
    return urls


def getContentCharset(content):
    # <meta http-equiv="Content-type" content="text/html; charset=gb2312" />
    if not content:
        return ''
    pattern = re.compile(r'<meta http-equiv="Content-type" content=".*?charset=(.*?)" />')
    charset = pattern.findall(content)
    if charset:
        logger.debug('charset is %s', charset[0])
        return charset[0].lower()
    else:
        return ''


def gethtml(url=''):
    """
    get the content from url.
    @param url: url which you want to get content from it.
    @return: content get from url.
    """
    if not re.match(r'^https?://.*?$', url):
        return ''
    req = urllib2.Request(url=url, headers=_HEADERS)
    try:
        # must set timeout. if not, thread may block here.
        resp = urllib2.urlopen(req, timeout=_TIMEOUT)
    except:
        logger.error('url %s open error.', url)
        return ''
    headers = resp.info()
    content = resp.read()
    # get whether content encoded by gzip, if encoded by gzip, need to decode.
    if ('content-Encoding' in headers) \
        and ('gzip' == headers['content-Encoding'].lower()):
        logger.debug('content encoded by gzip.')
        import gzip
        import StringIO
        fileobj = StringIO.StringIO(content)
        gzipFile = gzip.GzipFile(fileobj=fileobj)
        content = gzipFile.read()
        gzipFile.close()
    # decode the content by character set of the page.
    charset = getContentCharset(content)
    if charset == 'gbk' or charset == 'gb2312' or charset == 'gb18030':
        try:
            content = content.decode(_CHARACTER_SET)
        except:
            logger.error('decode with %s failed. content is \n%s', charset, content)
            return ''
    logger.info('html download complete.')
    return content


# main
if __name__ == '__main__':
    results = []
    threadPool = Scheduler(5)
    firstReq = WorkRequest(gethtml, args=[_ORIGIN_URL], callback=parseContent)
    threadPool.putRequest(firstReq)
    while True:
        threadPool.processing(2)
        if threadPool.workerAliveSize() == 0:
            break
    logger.debug('size of results: %d', len(results))
    dbopt = dboperate.DBOperation()
    dbopt.insert(results)
    logger.debug('main thread exit.')

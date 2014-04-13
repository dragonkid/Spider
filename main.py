#!/usr/bin/python
# -*- coding: UTF-8 -*-

import argparse

from spider import spider
from logger import setLogLevel
from cookielib import logger

# defines
_DESC = \
"""
This is a program used for spider the html pages.
And get the page which match the key.
"""
_LOG_HELP = \
"""
level of log(choose from 0, 1, 2, 3, 4, 5);
0--NOTSET, 1--DEBUG, 2--INFO, 3--WARNING, 4--ERROR, 5--CRITICAL;
log write into spider.log
"""

# module init.
parser = argparse.ArgumentParser(description=_DESC)
parser.add_argument('--testself', help='test it self', action='store_true',\
                    dest='testself')
parser.add_argument('-u', metavar='url', help='start url of spider',\
                    type=str, default='http://sina.com.cn')
parser.add_argument('-d', metavar='deep', help='depth of traversal',\
                    type=int, default=1)
parser.add_argument('--thread', metavar='thread', default=10,\
                    type=int, help='size of thread pool used for downloader')
parser.add_argument('--dbfile', metavar='dbfile', help='name of database file',\
                    type=str, default='')
parser.add_argument('--key', metavar='key', default='',\
                    type=str, help='key to match')
parser.add_argument('-l', metavar='loglevel',\
                    help=_LOG_HELP,\
                    type=int, default=4,\
                    choices=[0, 1, 2, 3, 4, 5])
args = parser.parse_args()

# parser.print_help()


# functions
def parserTest(args):
    print 'url: %s' % args.u
    print 'deep: %d' % args.d
    print 'threads: %d' % args.thread
    print 'dbfile: %s' % args.dbfile
    print 'key: %s' % args.key
    print 'log level: %d' % args.l
    print 'test self: %r' % args.testself


def testself():
    import doctest
    import common
    import logger
    for module in (common, logger):
        testRet = doctest.testmod(module)
        print 'test module %s...\n%s' % (module.__name__, unicode(testRet))


def main(args):
    # test self.
    if args.testself:
        testself()
        return
    # set log level.
    logLevel = args.l * 10
    setLogLevel(logLevel)
    spider(poolSize=args.thread, level=args.d,\
           key=args.key, dbfile=args.dbfile, url=args.u)


if __name__ == '__main__':
    main(args)

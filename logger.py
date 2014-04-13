#!/usr/bin python
# -*- coding: UTF-8 -*-

"""
supply a logger has been initiated.
the log will be write to spider.log in the same path of logger.

use like this:
>>> setLogLevel(logging.DEBUG)
>>> logger.info('info')
>>> logger.debug('my log: %s', _MYLOG)
>>> logger.debug('debug')
>>> logger.warning('warning')
"""

import os
import logging
import logging.handlers

# defines
_MYLOG = 'spider.log'
_LOG_FORMAT = '%(asctime)s %(levelname)s [%(threadName)s][%(filename)s][%(lineno)d] >> %(message)s'
_MAX_LOG_SIZE = 50 * 1024 * 1024
_BACKUP_COUNT = 5
_DEFAULT_LEVEL = logging.DEBUG

logger = logging.getLogger('Spider')
# create formatter.
_fmt = logging.Formatter(_LOG_FORMAT)
# create rotating file handler.
_logPath = os.path.join(os.path.realpath(''), _MYLOG)
fileHandler = logging.handlers.RotatingFileHandler(_logPath, 'w')
fileHandler.setLevel(logging.DEBUG)
fileHandler.setFormatter(_fmt)
# add handler.
logger.addHandler(fileHandler)


def setLogLevel(level=_DEFAULT_LEVEL):
    logger.setLevel(level)


def _test():
    import doctest
    doctest.testmod()
    print 'log file: %s' % _logPath

if __name__ == '__main__':
    _test()

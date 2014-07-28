#!/usr/bin python
# -*- coding: UTF-8 -*-

import os
import logging.handlers

# defines
_MYLOG = 'spider.log'
_LOG_FORMAT = '%(asctime)s %(levelname)s [%(filename)s][%(funcName)s][%(lineno)d] >> %(message)s'
_MAX_LOG_SIZE = 50 * 1024 * 1024
_BACKUP_COUNT = 5
_DEFAULT_LEVEL = logging.DEBUG
# _DEFAULT_LEVEL = logging.ERROR

logger = logging.getLogger('Spider')
# create formatter.
_fmt = logging.Formatter(_LOG_FORMAT)
# basic log config
logging.basicConfig(level=_DEFAULT_LEVEL, format=_LOG_FORMAT)
# create rotating file handler.
_logPath = os.path.join(os.path.realpath(''), _MYLOG)
fileHandler = logging.handlers.RotatingFileHandler(_logPath, 'w')
fileHandler.setLevel(logging.DEBUG)
fileHandler.setFormatter(_fmt)
# add handler.
logger.addHandler(fileHandler)


def setLogLevel(level=_DEFAULT_LEVEL):
    logger.setLevel(level)

# test start.
if __name__ == '__main__':
    setLogLevel(logging.INFO)
    logger.debug('debug')
    logger.info('info')
    logger.warning('warning')
    logger.debug('test = %s', _MYLOG)
# test end.

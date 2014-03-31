#!/usr/bin python
# -*- coding: UTF-8 -*-

import os
import logging
import logging.handlers

# defines
_MYLOG = 'spider.log'
_LOG_FORMAT = '%(asctime)s %(levelname)s [%(threadName)s][%(filename)s][%(lineno)d] >> %(message)s'
_MAX_LOG_SIZE = 1024*1024
_BACKUP_COUNT = 5

logger = logging.getLogger('Spider')
# create formatter.
_fmt = logging.Formatter(_LOG_FORMAT)
# basic log config
logging.basicConfig(level = logging.DEBUG, format = _LOG_FORMAT)
# create rotating file handler.
_logPath = os.path.join(os.path.realpath(''), _MYLOG)
fileHandler = logging.handlers.RotatingFileHandler(_logPath, 'a', _MAX_LOG_SIZE, _BACKUP_COUNT)
fileHandler.setLevel(logging.DEBUG)
fileHandler.setFormatter(_fmt)

logger.addHandler(fileHandler)

# test start.
if __name__ == '__main__':
    logger.debug('debug')
    logger.info('info')
    logger.warning('warning')
    logger.debug('test = %s', _MYLOG)
# test end.
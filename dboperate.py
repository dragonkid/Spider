#!/usr/bin python
# -*- coding: UTF-8 -*-
    
import sqlite3
from logger import logger

# get whether table spider has existed.
# select count(*) from sqlite_master where type='table' and name='spider'

# defines
_EXCEPT_MSG = 'table spider already exists'


# exceptions
class TableAlreadyExist(Exception):
    """
    raise when catch sqlite3.OperationalError: table stocks already exists.
    """
    pass


class DBOperation(object):
    def __init__(self, dbname='spider.db'):
        self.__dbconn = sqlite3.connect(dbname)
        self.__dbcur = self.__dbconn.cursor()
        res = self.__dbcur.execute("select count(*) from sqlite_master \
                    where type='table' and name='spider'").fetchone()
        if res and res[0] != 0:
            logger.debug('table spider has existed.')
            return
        # create default table.
        try:
            self.__dbcur.execute('create table spider (url text, html clob)')
        except sqlite3.OperationalError, e:
            logger.error(str(e))
            if str(e) == _EXCEPT_MSG:
                raise TableAlreadyExist
            else:
                raise e

    def __del__(self):
        self.__dbconn.close()

    def insert(self, lst):
        self.__dbcur.executemany('insert into spider values (?, ?)', lst)
        self.__dbconn.commit()


if __name__ == '__main__':
    lst = [(u'http://www.baidu.com',  u'aaa'),\
            (u'http://www.baidu.com11',  u'bbb')]
    dbopt = DBOperation()
    dbopt.insert(lst)

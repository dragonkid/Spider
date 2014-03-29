#!/usr/bin/env python
# -*- coding: UTF-8 -*-
"""
文件名 : logProcess.py
版本号 : 1.0
作者 : yangfan
生成日期 : 2012-03-12
功能描述 : 规划工具日志类
修改历史 （日期 作者 修改内容） :
"""
import sys
import os
import logging
import logging.handlers
from common import runpath
strLevel = logging.INFO
strFileName = os.path.join(runpath, 'Logs\log.txt')
strForMat = '%(asctime)s %(filename)s[line:%(lineno)d] %(levelname)s >> %(message)s'
logging.basicConfig(filename = os.path.join(runpath, 'Logs\log.txt')
, level = strLevel
, filemode = 'w'
, format = '%(asctime)s %(filename)s[line:%(lineno)d] %(levelname)s >> %(message)s'
# , datefmt='%a, %d %b %Y %H:%M:%S'
)
#定义一个StreamHandler，将DEBUG级别或更高的日志信息打印到标准错误，并将其添加到当前的日志处理对象#
log = logging.getLogger('PDT')
log.setLevel(strLevel)
console = logging.StreamHandler(sys.stdout)
formatter = logging.Formatter(strForMat)
console.setFormatter(formatter)
log.addHandler(console)
# 使用方法如下
# log.debug("dubug messagess")
# log.info("info message")
# log.warning("warning message")
# log.errot("error message")
# def CloseLog(self):
#
# logging.shutdown()
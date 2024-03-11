#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
@author: Florian Timm
@version: 2024.03.11
"""

import logging
from configparser import ConfigParser
import sys


class Conf(object):
    __instance = None
    __conf = None
    __LOGGER = None

    def __init__(self):
        pass  # raise RuntimeError('Call instance() instead')

    @classmethod
    def instance(cls):
        if cls.__instance is None:
            cls.__instance = cls.__new__(cls)
            cls.__instance.__init__()
        return cls.__instance

    def load_conf(self):
        if self.__conf is None:
            self.__conf = ConfigParser()
            self.__conf.read("./config.ini")
        return self.__conf

    def get_logger(self):
        conf = self.load_conf()
        if self.__LOGGER is None:
            self.__LOGGER = logging.getLogger('PhotoBox')
            if conf['both']['LogLevel'] == "DEBUG":
                self.__LOGGER.setLevel(logging.DEBUG)
            if conf['both']['LogLevel'] == "INFO":
                self.__LOGGER.setLevel(logging.INFO)
            if conf['both']['LogLevel'] == "WARNING":
                self.__LOGGER.setLevel(logging.WARNING)
            else:
                self.__LOGGER.setLevel(logging.ERROR)
            self.__LOGGER.addHandler(logging.StreamHandler(sys.stdout))
        return self.__LOGGER

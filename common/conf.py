#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
@author: Florian Timm
@version: 2024.03.11
"""

import logging
from configparser import ConfigParser
import sys

from common.singleton import SingletonMeta


class Conf(metaclass=SingletonMeta):
    __conf = None
    __LOGGER = None

    def load_conf(self):
        if self.__conf is None:
            self.__conf = ConfigParser()
            self.__conf.read("./config.ini")
        return self.__conf

    def get_logger(self):
        if self.__LOGGER is None:
            conf = self.load_conf()
            logLevel = logging.ERROR

            if conf['both']['LogLevel'] == "DEBUG":
                logLevel = logging.DEBUG
            if conf['both']['LogLevel'] == "INFO":
                logLevel = logging.INFO
            if conf['both']['LogLevel'] == "WARNING":
                logLevel = logging.WARNING
            if conf['both']['LogLevel'] == "ERROR":
                logLevel = logging.ERROR
            if conf['both']['LogLevel'] == "CRITICAL":
                logLevel = logging.CRITICAL
            if conf['both']['LogLevel'] == "NOTSET":
                logLevel = logging.NOTSET

            stdout_handler = logging.StreamHandler(stream=sys.stdout)
            handlers: list[logging.Handler] = [stdout_handler]
            if conf['both']['LogFile'] != "":
                file_handler = logging.FileHandler(
                    filename=conf['both']['LogFile'])
                handlers.append(file_handler)

            logging.basicConfig(
                level=logLevel,
                format='[%(asctime)s] {%(filename)s:%(lineno)d} %(levelname)s - %(message)s',
                handlers=handlers
            )
            self.__LOGGER = logging.getLogger('PhotoBoxLogger')
            self.__LOGGER.info("Logger loaded")
        return self.__LOGGER

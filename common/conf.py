#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
@author: Florian Timm
@version: 2024.03.11
"""

from configparser import ConfigParser

from common.singleton import SingletonMeta


class Conf(metaclass=SingletonMeta):
    __conf: ConfigParser

    def __load(self) -> None:
        if hasattr(self, '__conf'):
            return
        self.__conf = ConfigParser()
        self.__conf.read("./config.ini")

    def get(self) -> ConfigParser:
        self.__load()
        return self.__conf

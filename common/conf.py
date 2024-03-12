#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
@author: Florian Timm
@version: 2024.03.11
"""

from configparser import ConfigParser

from pyparsing import C

from common.singleton import SingletonMeta


class Conf(metaclass=SingletonMeta):
    __conf: ConfigParser | None = None

    def __load(self) -> ConfigParser:
        conf = ConfigParser()
        conf.read("./config.ini")
        return conf

    def get(self) -> ConfigParser:
        if self.__conf is None:
            self.__conf = self.__load()
        return self.__conf

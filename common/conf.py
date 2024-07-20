#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
This module provides a singleton class for managing configuration settings.

Author: Florian Timm
Version: 2024.06.20
"""

from configparser import ConfigParser

from common.singleton import SingletonMeta


class Conf(metaclass=SingletonMeta):
    """
    A singleton class for managing configuration settings.

    This class provides methods for loading and accessing configuration settings
    from a 'config.ini' file.

    Attributes:
        __conf (ConfigParser | None): The loaded configuration settings.

    Methods:
        __load: Load the configuration settings from the 'config.ini' file.
        get: Get the configuration settings.

    Usage:
        conf = Conf.get()
        value = conf.get('section', 'key')
    """

    __conf: ConfigParser | None = None

    def __load(self) -> ConfigParser:
        """
        Load the configuration settings from the 'config.ini' file.

        Returns:
            A ConfigParser object containing the loaded configuration settings.
        """
        conf = ConfigParser()
        conf.read("./config.ini")
        return conf

    def get(self) -> ConfigParser:
        """
        Get the configuration settings.

        If the settings have not been loaded yet, this method will load them first.

        Returns:
            A ConfigParser object containing the configuration settings.
        """
        if self.__conf is None:
            self.__conf = self.__load()
        return self.__conf

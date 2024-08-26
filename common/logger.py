#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
This module contains the Logger class, which is a singleton class used to log messages to the console and a file.
The log level and log file are set in the configuration file.

Author: Florian Timm
Version: 2024.06.20
"""

from common.conf import Conf
from common.singleton import SingletonMeta

import logging
import sys


class Logger(metaclass=SingletonMeta):
    """
    A singleton class used to log messages to the console and a file.

    This class provides methods for logging messages with different severity levels.

    Attributes:
        __logger (Logger | None): The logger object.

    Methods:
        log: Log a message with the specified severity level.   
        info: Log a message with severity 'INFO'.
        debug: Log a message with severity 'DEBUG'.
        warning: Log a message with severity 'WARNING'.
        error: Log a message with severity 'ERROR'.
        critical: Log a message with severity 'CRITICAL'.

    Usage:
        logger = Logger.get()
        logger.info("This is an info message.")
        logger.debug("This is a debug message.")
        logger.warning("This is a warning message.")
        logger.error("This is an error message.")
        logger.critical("This is a critical message.")
    """

    __logger: logging.Logger | None = None

    def log(self, level, msg, *args, **kwargs) -> None:
        """
        Log 'msg % args' with the integer severity 'level'.

        To pass exception information, use the keyword argument exc_info with
        a true value, e.g.

        logger.log(level, "Houston, we have a %s", "interesting problem", exc_info=1)
        """
        return self.get().log(level, msg, *args, **kwargs, stacklevel=2)

    def info(self, msg, *args, **kwargs) -> None:
        """
        Log 'msg % args' with severity 'INFO'.

        To pass exception information, use the keyword argument exc_info with
        a true value, e.g.

        logger.info("Houston, we have a %s", "interesting problem", exc_info=1)
        """
        return self.get().info(msg, *args, **kwargs, stacklevel=2)

    def debug(self, msg, *args, **kwargs) -> None:
        """
        Log 'msg % args' with severity 'DEBUG'.

        To pass exception information, use the keyword argument exc_info with
        a true value, e.g.

        logger.debug("Houston, we have a %s", "interesting problem", exc_info=1)
        """

        return self.get().debug(msg, *args, **kwargs, stacklevel=2)

    def warning(self, msg, *args, **kwargs) -> None:
        """
        Log 'msg % args' with severity 'WARNING'.

        To pass exception information, use the keyword argument exc_info with
        a true value, e.g.

        logger.warning("Houston, we have a %s", "interesting problem", exc_info=1)
        """

        return self.get().warning(msg, *args, **kwargs, stacklevel=2)

    def error(self, msg, *args, **kwargs) -> None:
        """
        Log 'msg % args' with severity 'ERROR'.

        To pass exception information, use the keyword argument exc_info with
        a true value, e.g.

        logger.error("Houston, we have a %s", "interesting problem", exc_info=1)

        """
        return self.get().error(msg, *args, **kwargs, stacklevel=2)

    def critical(self, msg, *args, **kwargs) -> None:
        """
        Log 'msg % args' with severity 'CRITICAL'.

        To pass exception information, use the keyword argument exc_info with
        a true value, e.g.

        logger.critical("Houston, we have a %s", "interesting problem", exc_info=1)
        """
        return self.get().critical(msg, *args, **kwargs, stacklevel=2)

    def __load(self) -> logging.Logger:
        logger = logging.getLogger('PhotoBoxLogger')
        conf = Conf().get()
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

        logger.info("Logger loaded")
        return logger

    def get(self) -> logging.Logger:
        if self.__logger is None:
            self.__logger = self.__load()
        return self.__logger

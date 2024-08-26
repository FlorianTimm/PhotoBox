#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
This module contains the SingletonMeta metaclass for implementing the Singleton design pattern.

Author: Florian Timm
Version: 2024.06.20
"""

from threading import Lock


class SingletonMeta(type):
    """
    Metaclass for implementing the Singleton design pattern.

    This metaclass ensures that only one instance of a class is created and
    provides a thread-safe implementation of the Singleton pattern.

    The class based on https://refactoring.guru/design-patterns/singleton/python/example#example-1.

    Attributes:
        _instances (dict): A dictionary to store the instances of the classes.
        _lock (Lock): A lock object to ensure thread safety during instance creation.
    """

    _instances = {}
    _lock: Lock = Lock()

    def __call__(cls, *args, **kwargs):
        """
        Create or return the instance of the class.

        This method is called when the class is called as a function. It checks
        if an instance of the class already exists, and if not, it creates a new
        instance and stores it in the _instances dictionary.

        Args:
            *args: Variable length argument list.
            **kwargs: Arbitrary keyword arguments.

        Returns:
            The instance of the class.

        """
        with cls._lock:
            if cls not in cls._instances:
                instance = super().__call__(*args, **kwargs)
                cls._instances[cls] = instance
        return cls._instances[cls]

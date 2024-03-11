#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
@author: Florian Timm
@version: 2024.03.11
"""

from flask import Flask
from configparser import ConfigParser
from master.control import Control


class TestMasterControl:
    conf = ConfigParser()
    conf.read("./config.ini")
    app = Flask(__name__)

    def test___init__(self):
        control = Control(self.conf, self.app)
        assert control is not None

    def test_get_marker(self):
        control = Control(self.conf, self.app)
        marker = control.get_marker()
        assert marker is not None
        assert type(marker) == dict

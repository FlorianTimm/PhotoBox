#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
@author: Florian Timm
@version: 2024.03.11
"""

from flask import Flask
from master.control import Control


class TestMasterControl:
    app = Flask(__name__)

    def test___init__(self):
        control = Control(self.app)
        assert control is not None

    def test_get_marker(self):
        control = Control(self.app)
        marker = control.get_marker()
        assert marker is not None
        assert type(marker) == dict

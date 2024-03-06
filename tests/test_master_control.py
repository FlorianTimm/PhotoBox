from flask import Flask
import pytest
from configparser import ConfigParser
from control import Control


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

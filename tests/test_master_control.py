from master.control import Control
from flask import Flask
import pytest
from configparser import ConfigParser


class TestMasterControl:
    conf = ConfigParser()
    conf.read("./config.ini")
    app = Flask(__name__)

    def test___init__(self):
        control = Control(self.conf, self.app)
        assert control is not None

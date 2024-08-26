#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
@author: Florian Timm
@version: 2024.03.11
"""

from glob import glob
from json import dump
import pytest

from camera.camera_aruco import Aruco
from cv2 import imread
from cv2 import cvtColor, COLOR_BGR2GRAY
from common.logger import Logger


class TestCameraAruco:
    img = imread('tests/test.jpg')
    img_sw = cvtColor(img, COLOR_BGR2GRAY)

    @pytest.fixture
    def aruco(self):
        return Aruco()

    def test_detect_from_rgb(self, aruco: Aruco):
        marker = aruco.detect_from_rgb(self.img)
        Logger().info(len(marker))
        assert len(marker) == 24
        assert isinstance(marker[0]['id'], int)
        assert isinstance(marker[0]['corner'], int)
        assert isinstance(marker[0]['x'], float)
        assert isinstance(marker[0]['y'], float)
        assert marker[0]['x'] >= 0
        assert marker[0]['y'] >= 0
        assert marker[0]['x'] <= 4608
        assert marker[0]['y'] <= 2592

    def test_detect(self, aruco: Aruco):
        marker = aruco.detect(self.img_sw)
        assert len(marker) == 24
        assert isinstance(marker[0]['id'], int)
        assert isinstance(marker[0]['corner'], int)
        assert isinstance(marker[0]['x'], float)
        assert isinstance(marker[0]['y'], float)
        assert marker[0]['x'] >= 0
        assert marker[0]['y'] >= 0
        assert marker[0]['x'] <= 4608
        assert marker[0]['y'] <= 2592

    @pytest.fixture
    def test_prepare_marker_check(self, aruco: Aruco):
        bilder = glob("../bilderserien/TPKarton/F01/*.jpg")
        marker = {}
        for b in bilder:
            img = imread(b)
            camera = b.split('/')[-1].split('.')[0]
            img_sw = cvtColor(img, COLOR_BGR2GRAY)
            marker[camera] = aruco.detect(img_sw)

        dump(marker, open('tests/aruco.json', 'w'), indent=2)

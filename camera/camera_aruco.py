#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
@author: Florian Timm
@version: 2024.03.11
"""

from cv2.aruco import Dictionary_create, DetectorParameters, CORNER_REFINE_SUBPIX, detectMarkers
from cv2 import cvtColor, COLOR_BGR2GRAY

from common.typen import ArucoMarkerPos
from common.logger import Logger


class Aruco:
    '''
    This class is used to detect Aruco markers in images.

    Attributes:
    - __parameter: DetectorParameters
    - __dict: Dictionary


    Methods:
    - detect_from_rgb(image: bytes) -> list[ArucoMarkerPos]
    - detect(image: bytes) -> list[ArucoMarkerPos]
    '''

    def __init__(self):
        self.__parameter = DetectorParameters.create()
        self.__parameter.cornerRefinementMethod = CORNER_REFINE_SUBPIX
        self.__dict = Dictionary_create(32, 3)

    def detect_from_rgb(self, image: bytes) -> list[ArucoMarkerPos]:
        img = cvtColor(image, COLOR_BGR2GRAY)
        return self.detect(img)

    def detect(self, image: bytes) -> list[ArucoMarkerPos]:
        corners, ids, _ = detectMarkers(
            image, self.__dict, parameters=self.__parameter)
        if ids is None:
            return []
        marker: list[ArucoMarkerPos] = [{'id': int(id_[0]),
                                         'corner': int(eid),
                                         'x': float(e[0]),
                                         'y': float(e[1])} for ecke, id_ in zip(corners, ids)
                                        for eid, e in enumerate(ecke[0])]
        Logger().info("Found Aruco: %d", len(marker))
        return marker

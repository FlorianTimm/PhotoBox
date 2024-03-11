#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
@author: Florian Timm
@version: 2024.03.11
"""

from cv2.aruco import Dictionary_create, DetectorParameters, CORNER_REFINE_SUBPIX, detectMarkers, detectMarkers
from cv2 import cvtColor, COLOR_BGR2GRAY

from common.typen import ArucoMarkerPos
from common.conf import Conf

LOGGER = Conf().get_logger()


class Aruco:
    def __init__(self):
        self.parameter = DetectorParameters.create()
        self.parameter.cornerRefinementMethod = CORNER_REFINE_SUBPIX
        self.dict = Dictionary_create(32, 3)

    def detect_from_rgb(self, image: bytes) -> list[ArucoMarkerPos]:
        img = cvtColor(image, COLOR_BGR2GRAY)
        return self.detect(img)

    def detect(self, image: bytes) -> list[ArucoMarkerPos]:
        corners, ids, _ = detectMarkers(
            image, self.dict, parameters=self.parameter)
        if ids is None:
            return []
        marker: list[ArucoMarkerPos] = [{'id': int(id_[0]),
                                         'corner': int(eid),
                                         'x': float(e[0]),
                                         'y': float(e[1])} for ecke, id_ in zip(corners, ids) for eid, e in enumerate(ecke[0])]
        LOGGER.info("Found Aruco: %d", len(marker))
        return marker

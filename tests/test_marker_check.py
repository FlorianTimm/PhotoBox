#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
@author: Florian Timm
@version: 2024.03.11
"""

from copy import deepcopy
from json import load, dump
import pandas as pd
import pytest

from master.marker_check import MarkerChecker
from common.typen import ArucoMarkerPos
from common.logger import Logger


class TestMarkerChecker:

    @pytest.fixture
    def test_create_testdata(self):
        file = "tests/marker.csv"
        marker = {}
        m = pd.read_csv(file)
        for _, r in m.iterrows():
            id = int(r['id'])
            if not id in marker:
                marker[id] = {}
            c = int(r['corner'])
            marker[id][c] = (r['x'], r['y'], r['z'])
        dump(marker, open('tests/marker.json', 'w'))

    def test_false_position(self):
        marker_coords = load(open('tests/marker.json', 'r'))
        marker_coords = {int(k): {int(corner): pos for corner, pos in v.items()}
                         for k, v in marker_coords.items()}

        marker_pos: dict[str, list[ArucoMarkerPos]] = load(
            open('tests/aruco.json', 'r'))
        # create a difference to test the filter
        marker_pos["camera04"][7]['x'] += 20

        metadata: dict[str, dict[str, int | float]] = {
            key: {'LensPosition': 1.} for key in marker_pos.keys()}
        marker_checker = MarkerChecker(marker_coords, marker_pos, metadata)
        marker_checker.check()
        c = marker_checker.get_corrected_coordinates()
        p = marker_checker.get_filtered_positions()
        assert len(p['camera04'])+1 == len(marker_pos['camera04'])

    def test_false_coordinate(self):
        marker_coords = load(open('tests/marker.json', 'r'))
        marker_coords = {int(k): {int(corner): pos for corner, pos in v.items()}
                         for k, v in marker_coords.items()}
        marker_coords_org = deepcopy(marker_coords)
        marker_coords[15][1][2] += 0.1

        marker_pos: dict[str, list[ArucoMarkerPos]] = load(
            open('tests/aruco.json', 'r'))
        # create a difference to test the filter

        metadata: dict[str, dict[str, int | float]] = {
            key: {'LensPosition': 1.} for key in marker_pos.keys()}
        marker_checker = MarkerChecker(marker_coords, marker_pos, metadata)
        marker_checker.check()
        c = marker_checker.get_corrected_coordinates()
        p = marker_checker.get_filtered_positions()
        assert len(p['camera04']) == len(marker_pos['camera04'])
        assert abs(c[15][1][2] -
                   marker_coords_org[15][1][2]) < 0.01

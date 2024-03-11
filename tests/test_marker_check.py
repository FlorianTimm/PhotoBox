from json import load, dump
import pandas as pd
import py
import pytest

from marker_check import MarkerChecker
from master import marker_get
from typen import ArucoMarkerPos


import logging

LOGGER = logging.getLogger(__name__)


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

    def test___init__(self):
        marker_coords = load(open('tests/marker.json', 'r'))
        marker_coords = {int(k): {int(corner): pos for corner, pos in v.items()}
                         for k, v in marker_coords.items()}

        marker_pos: dict[str, list[ArucoMarkerPos]] = load(
            open('tests/aruco.json', 'r'))
        # create a difference to test the filter
        marker_pos["camera04"][7]['x'] += 20

        metadata: dict[str, dict[str, int | float]] = {
            'camera04': {'LensPosition': 1.}}
        marker_checker = MarkerChecker(marker_coords, marker_pos, metadata)
        marker_checker.check()
        c = marker_checker.get_corrected_coordinates()
        p = marker_checker.get_filtered_positions()
        assert len(p['camera04'])+1 == len(marker_pos['camera04'])

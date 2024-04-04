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
from common.typen import ArucoMarkerCorners, ArucoMarkerPos, Metadata, Point3D
from common.logger import Logger


class TestMarkerChecker:

    @pytest.fixture
    def test_create_testdata(self):
        file = "tests/marker.csv"
        marker = {}
        m = pd.read_csv(file)
        for _, r in m.iterrows():
            id = int(r['id'])
            if id not in marker:
                marker[id] = {}
            c = int(r['corner'])
            marker[id][c] = (r['x'], r['y'], r['z'])
        dump(marker, open('tests/marker.json', 'w'))

    def test_false_position(self):
        marker_coords = self.load_marker_coords()
        marker_pos: dict[str, list[ArucoMarkerPos]] = load(
            open('tests/aruco.json', 'r'))
        # create a difference to test the filter
        marker_pos["camera04"][7]['x'] += 20

        metadata: dict[str, Metadata] = {
            key: {'LensPosition': 1.} for key in marker_pos.keys()}
        marker_checker = MarkerChecker(marker_coords, marker_pos, metadata)
        marker_checker.check()
        p = marker_checker.get_filtered_positions()
        assert len(p['camera04'])+1 == len(marker_pos['camera04'])

    def test_camera_positions(self):
        marker_coords = self.load_marker_coords()
        marker_pos: dict[str, list[ArucoMarkerPos]] = load(
            open('tests/aruco.json', 'r'))

        metadata: dict[str, Metadata] = {
            key: {'LensPosition': 1.} for key in marker_pos.keys()}
        marker_checker = MarkerChecker(marker_coords, marker_pos, metadata)
        marker_checker.check()
        p = marker_checker.get_cameras()
        Logger().info(p)
        assert len(p) == len(marker_pos)

    def load_marker_coords(self) -> dict[int, ArucoMarkerCorners]:
        marker_coord_str: dict[str, dict[str, list[float]]] = load(
            open('tests/marker.json', 'r'))
        marker_coords: dict[int, ArucoMarkerCorners] = {
            int(marker): ArucoMarkerCorners({
                int(corner): Point3D(coords[0], coords[1], coords[2])
                for corner, coords in marker_corners.items()})
            for marker,
            marker_corners in marker_coord_str.items()}

        return marker_coords

    def test_false_coordinate(self):
        marker_coords = self.load_marker_coords()
        marker_coords_org = deepcopy(marker_coords)

        mc = marker_coords[15][1]
        if mc is not None:
            mc_neu = Point3D(mc[0], mc[1], mc[2]+0.1)
            marker_coords[15][1] = mc_neu
        else:
            assert False

        marker_pos: dict[str, list[ArucoMarkerPos]] = load(
            open('tests/aruco.json', 'r'))
        # create a difference to test the filter

        metadata: dict[str, Metadata] = {
            key: {'LensPosition': 1.} for key in marker_pos.keys()}
        marker_checker = MarkerChecker(marker_coords, marker_pos, metadata)
        marker_checker.check()
        c = marker_checker.get_corrected_coordinates()
        p = marker_checker.get_filtered_positions()
        assert len(p['camera04']) == len(marker_pos['camera04'])
        c15_1 = c[15][1]
        mco15_1 = marker_coords_org[15][1]
        assert c15_1 is not None
        assert mco15_1 is not None
        if c15_1 is not None and mco15_1 is not None:
            assert abs(c15_1[2] - mco15_1[2]) < 0.01

    def test_missing_coordinate(self):
        marker_coords = self.load_marker_coords()
        marker_coords_org = deepcopy(marker_coords)
        del marker_coords[15]

        marker_pos: dict[str, list[ArucoMarkerPos]] = load(
            open('tests/aruco.json', 'r'))
        # create a difference to test the filter

        metadata: dict[str, Metadata] = {
            key: {'LensPosition': 1.} for key in marker_pos.keys()}
        marker_checker = MarkerChecker(marker_coords, marker_pos, metadata)
        marker_checker.check()
        c = marker_checker.get_corrected_coordinates()
        p = marker_checker.get_filtered_positions()
        assert len(p['camera04']) == len(marker_pos['camera04'])
        c15_1 = c[15][1]
        mco15_1 = marker_coords_org[15][1]
        assert c15_1 is not None
        assert mco15_1 is not None
        if c15_1 is not None and mco15_1 is not None:
            assert abs(c15_1[2] - mco15_1[2]) < 0.01

    def test_create_json_files(self):
        marker_coords = self.load_marker_coords()
        marker_pos: dict[str, list[ArucoMarkerPos]] = load(
            open('/home/timm/PhotoBox/focus_2/aruco.json', 'r'))

        metadata: dict[str, Metadata] = {
            key: {'LensPosition': 0.9} for key in marker_pos.keys()}
        marker_checker = MarkerChecker(marker_coords, marker_pos, metadata)
        marker_checker.check()
        p = marker_checker.get_cameras()
        Logger().info(p)
        from json import dump as json_dump
        detected_marker = marker_checker.get_filtered_positions()
        marker = marker_checker.get_corrected_coordinates()
        cameras = marker_checker.get_cameras()
        folder = "/tmp/"
        json_dump(detected_marker, open(
            folder + 'aruco.json', "w"), indent=2)

        marker_neu = {}
        for pid, corners in marker.items():
            marker_neu[pid] = {}
            for corner, pos in enumerate(corners):
                if pos is None:
                    continue
                marker_neu[pid][corner] = [pos.x,  pos.y,  pos.z]
        Logger().info("Marker: %s", marker_neu)

        json_dump(marker_neu, open(
            folder + 'marker.json', "w"), indent=2)

        json_dump(cameras, open(
            folder + 'cameras.json', "w"), indent=2)
        assert len(p) == len(marker_pos)

    def test_no_nan_in_json(self):
        marker_coords = self.load_marker_coords()
        marker_pos: dict[str, list[ArucoMarkerPos]] = load(
            open("tests/aruco _nan.json", 'r'))

        metadata: dict[str, Metadata] = load(
            open("tests/meta_nan.json", 'r'))
        marker_checker = MarkerChecker(marker_coords, marker_pos, metadata)
        marker_checker.check()
        p = marker_checker.get_cameras()
        detected_marker = marker_checker.get_filtered_positions()
        marker = marker_checker.get_corrected_coordinates()
        cameras = marker_checker.get_cameras()

        assert not any([v is None for v in marker.values()])
        assert not any([v is None for v in detected_marker.values()])
        assert not any([v is None for v in cameras.values()])

        Logger().info(marker)

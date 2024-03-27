#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
@author: Florian Timm
@version: 2024.03.11
"""

import cv2
import numpy as np
import pandas as pd
from common.logger import Logger
from common.typen import ArucoMarkerPos
from common.conf import Conf
from scipy import stats


class MarkerChecker:
    """A class to check marker positions and filter them if necessary.

    Attributes:
        __marker_coords (dict[int, dict[int, tuple[float, float, float]]]): A dictionary containing marker coordinates.
        __marker_pos (dict[str, list[ArucoMarkerPos]]): A dictionary containing marker positions.
        __metadata (dict[str, dict[str, int | float]]): A dictionary containing metadata.
        __is_filtered (bool): A boolean indicating if the marker positions have been filtered.
    """

    __marker_coords: pd.DataFrame
    __marker_pos: pd.DataFrame
    __metadata:  pd.DataFrame

    def __init__(self, marker_coords: dict[int, dict[int, tuple[float, float, float]]], marker_pos: dict[str, list[ArucoMarkerPos]], metadata: dict[str, dict[str, int | float]]):
        """
        Initialize the MarkerChecker class.

        Args:
            marker_coords (dict[int, dict[int, tuple[float, float, float]]]): A dictionary containing marker coordinates.
            marker_pos (dict[str, list[ArucoMarkerPos]]): A dictionary containing marker positions.
            metadata (dict[str, dict[str, int | float]]): A dictionary containing metadata.
        """
        self.__marker_coords = self.__create_marker_coords_dataframe(
            marker_coords)
        self.__marker_pos = self.__create_marker_pos_dataframe(marker_pos)
        self.__metadata = self.__create_metadata_dataframe(metadata)
        self.__is_filtered = False

    def __create_marker_coords_dataframe(self, marker_coords: dict[int, dict[int, tuple[float, float, float]]]) -> pd.DataFrame:
        """
        Create a dataframe containing the marker coordinates.

        Returns:
            A dataframe containing the marker coordinates.
        """
        data = []
        for id, corners in marker_coords.items():
            for corner, coord in corners.items():
                data.append([id, corner, coord[0], coord[1], coord[2]])
        return pd.DataFrame(data, columns=['id', 'corner', 'wx', 'wy', 'wz']).set_index(['id', 'corner'])

    def __create_marker_pos_dataframe(self, marker_pos: dict[str, list[ArucoMarkerPos]]) -> pd.DataFrame:
        """
        Create a dataframe containing the marker positions.

        Returns:
            A dataframe containing the marker positions.
        """
        data = []
        for hostname, positions in marker_pos.items():
            for pos in positions:
                data.append(
                    [hostname, pos['id'], pos['corner'], pos['x'], pos['y'], None])
        d = pd.DataFrame(
            data, columns=['hostname', 'id', 'corner', 'x', 'y', 'inlier']).set_index(['hostname', 'id', 'corner'])
        return d

    def __create_metadata_dataframe(self, metadata: dict[str, dict[str, int | float]]) -> pd.DataFrame:
        """
        Create a dataframe containing the metadata.

        Returns:
            A dataframe containing the metadata.
        """
        # read metadata
        pdm = pd.DataFrame.from_dict(metadata, orient='index', dtype='float32').reset_index().rename(
            columns={'index': 'hostname'}).astype({'hostname': str}).set_index('hostname')
        return pdm

    def __camera_matrix(self, lens_position: float, c_offset: float = 0, cx_offset: float = 0, cy_offset: float = 0) -> tuple[np.ndarray, np.ndarray]:
        """
        Get the camera matrix and distortion coefficients.

        Args:
            lens_position: The lens position value.
            c_offset: The c offset value.
            cx_offset: The cx offset value.
            cy_offset: The cy offset value.

        Returns:
            A tuple containing the camera matrix and distortion coefficients.
        """
        param = Conf().get()['calibration']
        c = float(param['f']) + c_offset + \
            lens_position * float(param['f_factor'])
        cx = float(param['cx']) + cx_offset + \
            lens_position * float(param['cx_factor'])
        cy = float(param['cy']) + cy_offset + \
            lens_position * float(param['cy_factor'])
        cameraMatrix = np.array([[c, 0, cx], [0, c, cy], [0, 0, 1]])
        distCoeffs = np.array([float(param['k1']) + lens_position *
                               float(param['k1_factor']),
                               float(param['k2']) + lens_position *
                               float(param['k2_factor']),
                               float(param['p1']) + lens_position *
                               float(param['p1_factor']),
                               float(param['p2']) + lens_position *
                               float(param['p2_factor']),
                               float(param['k3']) + lens_position *
                               float(param['k3_factor'])])
        return cameraMatrix, distCoeffs

    def check(self) -> None:
        """
        Check the marker positions and filter them if necessary.
        """

        # check and mark marker positions
        cameras = self.__check_marker_position()

        # check outliers on wrong coordinates
        t = self.__marker_pos.groupby(['id', 'corner'])['inlier'].agg(
            [pd.Series.count, pd.Series.mode])
        t = t[t['count'] > 2]
        t = t[t['mode'] == False].reset_index()

        Logger().info(t)

        # recalculate coordinates
        something_changed = self.recalculate_coordinates(cameras, t)

        if something_changed:
            Logger().info("Some coordinates have changed")
            cameras = self.__check_marker_position()

        self.__is_filtered = True

    def recalculate_coordinates(self, cameras: dict[str, dict[str, np.ndarray]], t: pd.DataFrame) -> bool:
        """
        Recalculate the coordinates.

        Args:
            cameras: A dictionary containing the cameras.
            df: A dataframe containing the marker positions.
            t: A dataframe containing the marker positions.

        Returns:
            A boolean indicating if the coordinates have been recalculated.
        """
        df = self.__create_dataframe()

        something_changed = False
        for _, row in t.iterrows():
            group: pd.DataFrame = df[(df['id'] == row['id']) & (
                df['corner'] == row['corner'])]
            # group['index'] = df.reset_index().index

            coord_neu = []
            j = group.add_suffix('_a').merge(
                group.add_suffix('_b'), how='cross')
            j = j[j['hostname_a'] < j['hostname_b']]

            for _, view in j.iterrows():
                camera1 = cameras[view['hostname_a']]
                camera2 = cameras[view['hostname_b']]
                r1, _ = cv2.Rodrigues(camera1['rvecs'])
                r2, _ = cv2.Rodrigues(camera2['rvecs'])
                P1 = np.c_[r1, camera1['tvecs']]
                P2 = np.c_[r2, camera2['tvecs']]
                v1 = cv2.undistortPoints(
                    np.array([[[view['x_a'], view['y_a']]]]), camera1['cameraMatrix'], camera1['distCoeffs'])
                v2 = cv2.undistortPoints(
                    np.array([[[view['x_b'], view['y_b']]]]), camera2['cameraMatrix'], camera2['distCoeffs'])
                coord = cv2.triangulatePoints(P1, P2, v1, v2)
                coord = coord / coord[3]
                coord_neu.append(coord[:3].flatten())
            if len(coord_neu) == 0:
                continue
            Logger().debug(coord_neu)
            coords_neu = pd.DataFrame(coord_neu, columns=['wx', 'wy', 'wz'])
            # df.loc[(df['id'] == row['id']) & (df['corner'] == row['corner']),
            #       ['x', 'y']] = coord_neu[:2]
            Logger().info(f"Korrigiere {row['id']} {row['corner']}")
            zscore = np.abs(stats.zscore(coords_neu[["wx", "wy", "wz"]]))
            # print(zscore)
            Logger().debug(zscore)
            # Identify outliers as students with a z-score greater than 3
            threshold = 2
            coords_neu = coords_neu[zscore <= threshold].dropna()
            Logger().debug(coords_neu.mean())
            Logger().debug(group[['wx', 'wy', 'wz']])

            neu = coords_neu.mean().to_numpy()
            self.__marker_coords.at[(row['id'], row['corner']), 'wx'] = neu[0]
            self.__marker_coords.at[(row['id'], row['corner']), 'wy'] = neu[1]
            self.__marker_coords.at[(row['id'], row['corner']), 'wz'] = neu[2]

            # row['id']) & (
            #   self.__marker_coords['corner'] == row['corner']), ['wx', 'wy', 'wz']] = coords_neu.mean().to_numpy()
            # self.__marker_coords[row['id']][row['corner']] = (
            #    coords_neu['wx'].mean(), coords_neu['wy'].mean(), coords_neu['wz'].mean())

            Logger().debug(
                f"Original: {group[['wx', 'wy', 'wz']].mean().to_numpy()}")
            Logger().debug(self.__marker_coords)
            something_changed = True
        return something_changed

    def __check_marker_position(self) -> dict[str, dict[str, np.ndarray]]:
        """
        Check the marker positions and filter them if necessary.

        Returns:
            A tuple containing the cameras and the marker positions.
        """

        df = self.__create_dataframe()
        if len(df) == 0:
            Logger().warning("No data to process")
            return {}
        cameras = {}

        for (hostname, lensposition), group in df[df["wx"] != None].groupby(['hostname', 'LensPosition']):
            Logger().debug(f"Processing {hostname}")
            cameraMatrix, distCoeffs = self.__camera_matrix(lensposition)
            objp = group[['wx', 'wy', 'wz']].to_numpy(dtype=np.float32)
            imgp = group[['x', 'y']].to_numpy(dtype=np.float32)
            ret, rvecs, tvecs, inlier = cv2.solvePnPRansac(
                objp, imgp, cameraMatrix, distCoeffs, reprojectionError=10.0)
            cameras[hostname] = {'cameraMatrix': cameraMatrix,
                                 'distCoeffs': distCoeffs, 'rvecs': rvecs, 'tvecs': tvecs}
            for i, ind in enumerate(group.index):
                id = df.at[ind, 'id']
                corner = df.at[ind, 'corner']
                if inlier is None:
                    self.__marker_pos.at[(
                        hostname, id, corner), 'inlier'] = False
                if i in inlier:
                    self.__marker_pos.at[(
                        hostname, id, corner), 'inlier'] = True
                else:
                    self.__marker_pos.at[(
                        hostname, id, corner), 'inlier'] = False

        return cameras

    def __create_dataframe(self) -> pd.DataFrame:
        return pd.merge(self.__marker_pos.reset_index(), self.__marker_coords.reset_index(),
                        left_on=['id', 'corner'],
                        right_on=['id', 'corner'], how='outer'). \
            merge(self.__metadata.reset_index(), left_on='hostname',
                  right_on='hostname')

    def get_corrected_coordinates(self) -> dict[int, dict[int, tuple[float, float, float]]]:
        """
        Get the corrected marker coordinates.

        Returns:
            A dictionary containing the corrected marker coordinates.
        """
        if not self.__is_filtered:
            self.check()
        d = {}
        for id, corners in self.__marker_coords.reset_index().groupby('id'):
            d[id] = {}
            for _, coord in corners.iterrows():
                d[id][int(coord['corner'])] = (
                    coord['wx'], coord['wy'], coord['wz'])
        return d

    def get_filtered_positions(self) -> dict[str, list[ArucoMarkerPos]]:
        """
        Get the filtered marker positions.

        Returns:
            A dictionary containing the filtered marker positions.
        """
        if not self.__is_filtered:
            self.check()
        d = {}

        for hostname, positions in self.__marker_pos[self.__marker_pos['inlier']].reset_index().groupby('hostname'):
            d[hostname] = []
            for _, pos in positions.iterrows():
                d[hostname].append(
                    {'id': pos['id'], 'corner': pos['corner'], 'x': pos['x'], 'y': pos['y']})
        return d

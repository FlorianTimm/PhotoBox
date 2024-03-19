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
from scipy import stats


class MarkerChecker:
    """A class to check marker positions and filter them if necessary.

    Attributes:
        __marker_coords (dict[int, dict[int, tuple[float, float, float]]]): A dictionary containing marker coordinates.
        __marker_pos (dict[str, list[ArucoMarkerPos]]): A dictionary containing marker positions.
        __metadata (dict[str, dict[str, int | float]]): A dictionary containing metadata.
        __is_filtered (bool): A boolean indicating if the marker positions have been filtered.
    """

    __marker_coords: dict[int, dict[int, tuple[float, float, float]]] = {}
    __marker_pos: dict[str, list[ArucoMarkerPos]] = {}
    __metadata:  dict[str, dict[str, int | float]] = {}
    __params = np.array([2.63572488e+01,  6.31322513e-01, -9.88069511e+00,  2.92706002e+01,
                         -4.15690296e-03, -1.99188205e-02, -1.01408404e-04,  2.60612862e-06,
                         2.79208519e-02,  0.00000000e+00,  0.00000000e+00,  0.00000000e+00,
                         0.00000000e+00,  0.00000000e+00])

    def __init__(self, marker_coords: dict[int, dict[int, tuple[float, float, float]]], marker_pos: dict[str, list[ArucoMarkerPos]], metadata: dict[str, dict[str, int | float]]):
        """
        Initialize the MarkerChecker class.

        Args:
            marker_coords (dict[int, dict[int, tuple[float, float, float]]]): A dictionary containing marker coordinates.
            marker_pos (dict[str, list[ArucoMarkerPos]]): A dictionary containing marker positions.
            metadata (dict[str, dict[str, int | float]]): A dictionary containing metadata.
        """
        self.__marker_coords = marker_coords
        self.__marker_pos = marker_pos
        self.__metadata = metadata
        self.__is_filtered = False

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
        x = self.__params.tolist()
        if len(x) == 9:
            [x.append(0) for _ in range(5)]
        c = 3385 + x[0] + c_offset + x[3] * lens_position
        cx = 2304 + x[1] + cx_offset
        cy = 1296 + x[2] + cy_offset
        cameraMatrix = np.array([[c, 0, cx], [0, c, cy], [0, 0, 1]])
        distCoeffs = np.array([x[9:14]]) + np.array([x[4:9]]) * lens_position
        return cameraMatrix, distCoeffs

    def check(self) -> None:
        """
        Check the marker positions and filter them if necessary.
        """
        pdm = pd.DataFrame.from_dict(self.__metadata)
        Logger().debug(pdm)

        cameras, df = self.__check_marker_position()

        # check outliers on wrong coordinates
        t = df.groupby(['id', 'corner'])['inlier'].agg(
            [pd.Series.count, pd.Series.mode])
        t = t[t['count'] > 2]
        t = t[t['mode'] == False].reset_index()

        # recalculate coordinates
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
            coords_neu = pd.DataFrame(coord_neu, columns=['x', 'y', 'z'])
            # df.loc[(df['id'] == row['id']) & (df['corner'] == row['corner']),
            #       ['x', 'y']] = coord_neu[:2]
            Logger().info(f"Korrigiere {row['id']} {row['corner']}")
            zscore = np.abs(stats.zscore(coords_neu[["x", "y", "z"]]))
            # print(zscore)
            Logger().debug(zscore)
            # Identify outliers as students with a z-score greater than 3
            threshold = 2
            coords_neu = coords_neu[zscore <= threshold].dropna()
            Logger().debug(coords_neu.mean())
            Logger().debug(group[['xw', 'yw', 'zw']])

            self.__marker_coords[row['id']][row['corner']] = (
                coords_neu['x'].mean(), coords_neu['y'].mean(), coords_neu['z'].mean())

            Logger().info(
                f"Korrigiert: {self.__marker_coords[row['id']][row['corner']]}")
            Logger().debug(
                f"Original: {group[['xw', 'yw', 'zw']].mean().to_numpy()}")
            Logger().debug(self.__marker_coords)
            something_changed = True

        if something_changed:
            Logger().info("Some coordinates have changed")
            cameras, df = self.__check_marker_position()

        self.__is_filtered = True

    def __check_marker_position(self) -> tuple[dict[str, dict[str, np.ndarray]], pd.DataFrame]:
        """
        Check the marker positions and filter them if necessary.

        Returns:
            A tuple containing the cameras and the marker positions.
        """

        df = self.__create_dataframe()
        if len(df) == 0:
            Logger().warning("No data to process")
            return {}, df

        cameras = {}

        for (hostname, lensposition), group in df.groupby(['hostname', 'LensPosition']):
            Logger().debug(f"Processing {hostname}")
            cameraMatrix, distCoeffs = self.__camera_matrix(lensposition)
            objp = group[['xw', 'yw', 'zw']].to_numpy(dtype=np.float32)
            imgp = group[['x', 'y']].to_numpy(dtype=np.float32)
            ret, rvecs, tvecs, inliner = cv2.solvePnPRansac(
                objp, imgp, cameraMatrix, distCoeffs, reprojectionError=10.0)
            cameras[hostname] = {'cameraMatrix': cameraMatrix,
                                 'distCoeffs': distCoeffs, 'rvecs': rvecs, 'tvecs': tvecs}
            for i, ind in enumerate(group.index):
                if inliner is None:
                    df.at[ind, 'inlier'] = False
                if i in inliner:
                    df.at[ind, 'inlier'] = True
                else:
                    df.at[ind, 'inlier'] = False

        self.__marker_pos = {str(hostname): [{'id': row['id'], 'corner': row['corner'], 'x': row['x'], 'y': row['y']}
                                             for _, row in group.iterrows()] for (hostname,), group in df[df['inlier'] == True].groupby(['hostname'])}
        # df.to_excel('tests/debug_positions.xlsx')
        return cameras, df

    def __create_dataframe(self) -> pd.DataFrame:
        data = []

        for hostname, positions in self.__marker_pos.items():
            Logger().debug(f"Processing {hostname}")

            lenspos = self.__metadata[hostname]['LensPosition']
            for pos in positions:
                if not pos['id'] in self.__marker_coords:
                    Logger().warning(
                        f"Marker {pos['id']} not found in marker_coords")
                    continue
                if not pos['corner'] in self.__marker_coords[pos['id']]:
                    Logger().warning(
                        f"Corner {pos['corner']} not found in marker_coords[{pos['id']}]")
                    continue
                c = self.__marker_coords[pos['id']][pos['corner']]
                data.append([hostname, pos['id'], pos['corner'], lenspos, pos['x'],
                            pos['y'], c[0], c[1], c[2]])

        df: pd.DataFrame = pd.DataFrame(data, columns=['hostname',
                                                       'id', 'corner', 'LensPosition', 'x', 'y', 'xw', 'yw', 'zw']).astype({'hostname': str, 'id': 'int32', 'corner': 'int32', 'LensPosition': 'float32', 'x': 'float32', 'y': 'float32', 'xw': 'float32', 'yw': 'float32', 'zw': 'float32'})
        df['inlier'] = None
        return df

    def get_corrected_coordinates(self) -> dict[int, dict[int, tuple[float, float, float]]]:
        """
        Get the corrected marker coordinates.

        Returns:
            A dictionary containing the corrected marker coordinates.
        """
        if not self.__is_filtered:
            self.check()
        return self.__marker_coords

    def get_filtered_positions(self) -> dict[str, list[ArucoMarkerPos]]:
        """
        Get the filtered marker positions.

        Returns:
            A dictionary containing the filtered marker positions.
        """
        if not self.__is_filtered:
            self.check()
        return self.__marker_pos

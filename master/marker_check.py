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
from common.typen import ArucoMarkerPos, ArucoMarkerCorners, CameraExterior, Metadata, Point3D
from common.conf import Conf
from scipy import stats


class MarkerChecker:
    """A class to check marker positions and filter them if necessary.

    Attributes:
        __marker_coords (dict[int, ArucoMarkerCorners]): A dictionary containing marker coordinates.
        __marker_pos (dict[str, list[ArucoMarkerPos]]): A dictionary containing marker positions.
        __metadata (dict[str, Metadata]): A dictionary containing metadata.
        __is_filtered (bool): A boolean indicating if the marker positions have been filtered.
    """

    __marker_coords: pd.DataFrame
    __marker_pos: pd.DataFrame
    __metadata:  pd.DataFrame
    __cameras: dict[str, CameraExterior]

    def __init__(self, marker_coords: dict[int, ArucoMarkerCorners], marker_pos: dict[str, list[ArucoMarkerPos]], metadata: dict[str, Metadata], cameras: dict[str, CameraExterior] = {}):
        """
        Initialize the MarkerChecker class.

        Args:
            marker_coords (dict[int, ArucoMarkerCorners]): A dictionary containing marker coordinates.
            marker_pos (dict[str, list[ArucoMarkerPos]]): A dictionary containing marker positions.
            metadata (dict[str, Metadata]): A dictionary containing metadata.
        """
        self.__marker_coords = self.__create_marker_coords_dataframe(
            marker_coords)
        self.__marker_pos = self.__create_marker_pos_dataframe(marker_pos)
        self.__metadata = self.__create_metadata_dataframe(metadata)
        self.__cameras = cameras
        self.__is_filtered = False

    def __create_marker_coords_dataframe(self, marker_coords: dict[int, ArucoMarkerCorners]) -> pd.DataFrame:
        """
        Create a dataframe containing the marker coordinates.

        Returns:
            A dataframe containing the marker coordinates.
        """
        data: list[tuple[int, int, float, float, float]] = []
        for id, corners in marker_coords.items():
            if corners is None:
                continue
            for corner, coord in enumerate(corners):
                if coord is None:
                    continue
                data.append((id, corner, coord.x, coord.y, coord.z))
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

    def __create_metadata_dataframe(self, metadata: dict[str, Metadata]) -> pd.DataFrame:
        """
        Create a dataframe containing the metadata.

        Returns:
            A dataframe containing the metadata.
        """
        # read metadata
        data = []
        for hostname, meta in metadata.items():
            if 'LensPosition' not in meta:
                continue
            data.append([hostname, meta['LensPosition']])
        pdm = pd.DataFrame(
            data, columns=['hostname', 'LensPosition']).set_index('hostname')
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
        # Replace with True if mode is a list (Number of outliers = Number of inliers)
        # Logger().info(type(t['mode']))
        t['mode'] = t['mode'].apply(
            lambda x: True if isinstance(x, list) else x)

        t = t[t['count'] > 2]
        try:
            # TODO: REPAIR THIS
            t = t[(t['mode'] == False)]
        except Exception:
            Logger().info("Error in filtering")
            pass

        t.reset_index(inplace=True)

        # Logger().info(t)

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

        for (hostname, lensposition), group in df[df["wx"] != None].groupby(['hostname', 'LensPosition']):  # noqa: E711
            Logger().debug(f"Processing {hostname}")
            cameraMatrix, distCoeffs = self.__camera_matrix(lensposition)
            objp = group[['wx', 'wy', 'wz']].to_numpy(dtype=np.float32)
            imgp = group[['x', 'y']].to_numpy(dtype=np.float32)
            ret, rvecs, tvecs, inlier = cv2.solvePnPRansac(
                objp, imgp, cameraMatrix, distCoeffs, reprojectionError=10.0)
            cameras[hostname] = {'cameraMatrix': cameraMatrix,
                                 'distCoeffs': distCoeffs, 'rvecs': rvecs, 'tvecs': tvecs}
            rVec = rvecs[:, 0]
            rMat = cv2.Rodrigues(rVec)[0]
            R = np.linalg.inv(rMat)
            t = tvecs[:, 0].T
            t = -R@t
            rVecEuler = self.rotationMatrixToEuler(R)
            self.__cameras[hostname] = {
                "x": t[0], "y": t[1], "z": t[2], "roll": rVecEuler[0], "pitch": rVecEuler[1], "yaw": rVecEuler[2]}

            for i, ind in enumerate(group.index):
                id = df.at[ind, 'id']
                corner = df.at[ind, 'corner']
                is_inlier = False
                if inlier is not None and i in inlier:
                    is_inlier = True
                self.__marker_pos.loc[(
                    hostname, id, corner), 'inlier'] = is_inlier
        return cameras

    def __create_dataframe(self) -> pd.DataFrame:
        return pd.merge(self.__marker_pos.reset_index(), self.__marker_coords.reset_index(),
                        left_on=['id', 'corner'],
                        right_on=['id', 'corner'], how='outer'). \
            merge(self.__metadata.reset_index(), left_on='hostname',
                  right_on='hostname')

    def get_corrected_coordinates(self) -> dict[int, ArucoMarkerCorners]:
        """
        Get the corrected marker coordinates.

        Returns:
            A dictionary containing the corrected marker coordinates.
        """
        if not self.__is_filtered:
            self.check()
        d = {}
        for id, corners in self.__marker_coords.reset_index().groupby('id'):
            d[id] = ArucoMarkerCorners()
            for _, coord in corners.iterrows():
                d[id][int(coord['corner'])] = Point3D(
                    coord['wx'], coord['wy'], coord['wz'])
                # Logger().info(
                #    f"ID: {id} Corner: {coord['corner']} Coord: {coord['wx']} {coord['wy']} {coord['wz']}")

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

        group = self.__marker_pos[self.__marker_pos['inlier']
                                  != False].reset_index().groupby('hostname')  # noqa: E712

        for hostname, positions in group:
            d[hostname] = []
            for _, pos in positions.iterrows():
                d[hostname].append(
                    {'id': pos['id'], 'corner': pos['corner'], 'x': pos['x'], 'y': pos['y']})
        return d

    def get_cameras(self) -> dict[str, CameraExterior]:
        """
        Get the cameras.

        Returns:
            A dictionary containing the cameras.
        """
        return self.__cameras

    def rotationMatrixToEuler(self, R: np.ndarray) -> np.ndarray:
        """
        Converts a rotation matrix to Euler angles.
        from: https://learnopencv.com/rotation-matrix-to-euler-angles/

        Args:
            R: The rotation matrix.

        Returns:
            The Euler angles.
        """
        if not self.isRotationMatrix(R):
            raise ValueError("Not a valid rotation matrix")

        sy = np.sqrt(R[0, 0] * R[0, 0] + R[1, 0] * R[1, 0])

        singular = sy < 1e-6

        if not singular:
            x = np.arctan2(R[2, 1], R[2, 2])
            y = np.arctan2(-R[2, 0], sy)
            z = np.arctan2(R[1, 0], R[0, 0])
        else:
            x = np.arctan2(-R[1, 2], R[1, 1])
            y = np.arctan2(-R[2, 0], sy)
            z = 0

        return np.array([x, y, z])

    def isRotationMatrix(self, R: np.ndarray) -> bool:
        """
        Check if a matrix is a valid rotation matrix.
        from: https://learnopencv.com/rotation-matrix-to-euler-angles/

        Args:
            R: The rotation matrix.

        Returns:
            A boolean indicating if the matrix is a valid rotation matrix.
        """
        rt = np.transpose(R)
        shouldBeIdentity = np.dot(rt, R)
        ident = np.identity(3, dtype=R.dtype)
        n = np.linalg.norm(ident - shouldBeIdentity)
        return n < 1e-6  # type: ignore

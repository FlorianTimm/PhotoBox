import cv2
import numpy as np
from typen import ArucoMarkerPos


class MarkerChecker:
    __marker_coords: dict[int, dict[int, tuple[float, float, float]]] = {}
    __marker_pos: dict[str, dict[str, list[ArucoMarkerPos]]] = {}
    __metadata: dict[str, dict[str, dict[str, int | float]]] = {}
    __params = np.array([2.63572488e+01,  6.31322513e-01, -9.88069511e+00,  2.92706002e+01,
                         -4.15690296e-03, -1.99188205e-02, -1.01408404e-04,  2.60612862e-06,
                         2.79208519e-02,  0.00000000e+00,  0.00000000e+00,  0.00000000e+00,
                         0.00000000e+00,  0.00000000e+00])

    def __init__(self, marker_coords: dict[int,
                                           dict[int, tuple[float, float, float]]], marker_pos: dict[str, dict[str, list[ArucoMarkerPos]]], metadata: dict[str, dict[str, dict[str, int | float]]]):
        self.__marker_coords = marker_coords
        self.__marker_pos = marker_pos
        self.__metadata = metadata

    def __calibrate(self, fokus, f_offset=0, x_offset=0, y_offset=0) -> tuple[np.ndarray, np.ndarray]:
        x = self.__params.tolist()
        if len(x) == 9:
            [x.append(0) for _ in range(5)]
        c = 3385 + x[0] + f_offset + x[3] * fokus
        cx = 2304 + x[1] + x_offset
        cy = 1296 + x[2] + y_offset
        cameraMatrix = np.array([[c, 0, cx], [0, c, cy], [0, 0, 1]])
        distCoeffs = np.array([x[9:14]]) + np.array([x[4:9]]) * fokus
        return cameraMatrix, distCoeffs

    def check(self) -> None:
        camera_matrix, dist_coeffs = self.__calibrate(self.__metadata['focus'])
        retval, rvec, tvec, inliers = cv2.solvePnPRansac(self.__marker_coords, self.__marker_pos,
                                                         camera_matrix, dist_coeffs)

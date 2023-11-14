import cv2
import numpy as np
import sqlite3
import matplotlib.pyplot as plt
from random import choices
from typing import List, Any
from numpy.typing import NDArray


def cart2hom(arr: NDArray[np.float32]) -> NDArray[np.float32]:
    """ Convert catesian to homogenous points by appending a row of 1s
    :param arr: array of shape (num_dimension x num_points)
    :returns: array of shape ((num_dimension+1) x num_points)
    """
    if arr.ndim == 1:
        return np.hstack([arr, 1])
    return np.asarray(np.vstack([arr, np.ones(arr.shape[1])]))


def scale_and_translate_points(points: NDArray[np.float32]) -> tuple[Any, NDArray[Any]]:
    """ Scale and translate image points so that centroid of the points
        are at the origin and avg distance to the origin is equal to sqrt(2).
        Hartley p109
    :param points: array of homogenous point (3 x n)
    :returns: array of same input shape and its normalization matrix
    """
    x = points[0]
    y = points[1]
    center = points.mean(axis=1)  # mean of each row
    cx = x - center[0]  # center the points
    cy = y - center[1]
    dist = np.sqrt(np.power(cx, 2) + np.power(cy, 2))
    scale = np.sqrt(2) / dist.mean()
    norm3d = np.array([
        [scale, 0, -scale * center[0]],
        [0, scale, -scale * center[1]],
        [0, 0, 1]
    ])

    return np.dot(norm3d, points), norm3d


def correspondence_matrix(p1: NDArray[np.float32], p2: NDArray[np.float32]) -> NDArray[np.float64]:
    """Each row in the A matrix below is constructed as
        [x'*x, x'*y, x', y'*x, y'*y, y', x, y, 1]
        Hartley p279"""
    p1x, p1y = p1[:2]
    p2x, p2y = p2[:2]

    return np.array([
        p1x * p2x, p1x * p2y, p1x,
        p1y * p2x, p1y * p2y, p1y,
        p2x, p2y, np.ones(len(p1x))
    ]).T


def compute_essential_normalized(p1: NDArray[np.float32], p2: NDArray[np.float32]) -> NDArray[np.float64]:
    """ Computes the fundamental or essential matrix from corresponding points
        using the normalized 8 point algorithm.
        Hartley p294
    :input p1, p2: corresponding points with shape 3 x n
    :returns: fundamental or essential matrix with shape 3 x 3
    """
    n = p1.shape[1]
    if p2.shape[1] != n:
        raise ValueError('Number of points do not match.')

    # preprocess image coordinates
    # Hartley p282
    p1n, T1 = scale_and_translate_points(p1)
    p2n, T2 = scale_and_translate_points(p2)

    # compute F or E with the coordinates
    # Harley p280
    A = correspondence_matrix(p1n, p2n)
    # compute linear least square solution
    U, S, V = np.linalg.svd(A)
    F: NDArray[np.float64] = V[-1].reshape(3, 3)

    # constrain F. Make rank 2 by zeroing out last singular value
    # Hartley p. 259
    U, S, V = np.linalg.svd(F)
    # S[-1] = 0 # Fundamental Hartley p.281
    S = np.array([1, 1, 0])  # Force rank 2 and equal eigenvalues
    F = U @ np.diag(S) @ V

    # reverse preprocessing of coordinates
    # We know that P1' E P2 = 0
    # Hartley p282
    F = T1.T@F@T2

    np.divide(F, F[2, 2], F)
    return F


def reconstruct_points(p1: NDArray[np.float32], p2: NDArray[np.float32], m1: NDArray[np.float32], m2: NDArray[np.float32]) -> NDArray[np.float64]:
    num_points = p1.shape[1]
    res = np.ones((4, num_points))

    for i in range(num_points):
        res[:, i] = reconstruct_one_point(p1[:, i], p2[:, i], m1, m2)

    return res


def skew(x: NDArray[np.float32]) -> NDArray[np.float64]:
    """ Create a skew symmetric matrix *A* from a 3d vector *x*.
        Property: np.cross(A, v) == np.dot(x, v)
    :param x: 3d vector
    :returns: 3 x 3 skew symmetric matrix from *x*
    """
    return np.array([
        [0, -x[2], x[1]],
        [x[2], 0, -x[0]],
        [-x[1], x[0], 0]
    ], dtype=np.float64)


def reconstruct_one_point(pt1: NDArray[np.float32], pt2: NDArray[np.float32], m1: NDArray[np.float32], m2: NDArray[np.float32]) -> NDArray[np.float64]:
    """
        pt1 and m1 * X are parallel and cross product = 0
        pt1 x m1 * X  =  pt2 x m2 * X  =  0
        :param p1, p2: 2D points in homo. or catesian coordinates. Shape (3 x n)
        :param m1, m2: Camera matrices associated with p1 and p2. Shape (3 x 4)
    """
    A = np.vstack([
        np.dot(skew(pt1), m1),
        np.dot(skew(pt2), m2)
    ])
    U, S, V = np.linalg.svd(A)
    P = np.ravel(V[-1, :4])

    np.divide(P, P[3])
    return P


def linear_triangulation(p1: NDArray[np.float32], p2: NDArray[np.float32], m1: NDArray[np.float32], m2: NDArray[np.float32]) -> NDArray[np.float64]:
    """
    Linear triangulation (Hartley ch 12.2 pg 312) to find the 3D point X
    where p1 = m1 * X and p2 = m2 * X. Solve AX = 0.
    :param p1, p2: 2D points in homo. or catesian coordinates. Shape (3 x n)
    :param m1, m2: Camera matrices associated with p1 and p2. Shape (3 x 4)
    :returns: 4 x n homogenous 3d triangulated points
    """
    num_points = p1.shape[1]
    res = np.ones((4, num_points))

    for i in range(num_points):
        A = np.asarray([
            (p1[0, i] * m1[2, :] - m1[0, :]),
            (p1[1, i] * m1[2, :] - m1[1, :]),
            (p2[0, i] * m2[2, :] - m2[0, :]),
            (p2[1, i] * m2[2, :] - m2[1, :])
        ])

        _, _, V = np.linalg.svd(A)
        X = V[-1, :4]
        res[:, i] = X / X[3]

    return res

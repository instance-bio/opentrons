import logging
import numpy as np  # type: ignore
from numpy import insert, dot  # type: ignore
from numpy.linalg import inv  # type: ignore
from typing import List, Tuple, Union

from opentrons.calibration_storage.types import AttitudeMatrix
from opentrons.config import feature_flags as ff

mod_log = logging.getLogger(__name__)

# (TODO(lc, 8/11/2020): temporary type until
# old calibration data is removed.
AxisPosition = Union[
    Tuple[float, float, float], Tuple[float, float]]

SolvePoints = Tuple[
    Tuple[float, float, float],
    Tuple[float, float, float],
    Tuple[float, float, float]]


def identity_deck_transform() -> np.ndarray:
    """ The default deck transform """
    if ff.enable_calibration_overhaul():
        return np.identity(3)
    else:
        return np.identity(4)


def solve_attitude(
        expected: SolvePoints,
        actual: SolvePoints
        ) -> AttitudeMatrix:
    ex = np.array([
        list(point)
        for point in expected
    ]).transpose()
    ac = np.array([
            list(point)
            for point in actual
        ]).transpose()
    t = np.dot(ac, inv(ex))

    mask_transform = np.array([
        [True, True, False],
        [True, True, False],
        [False, False, False]])
    masked_array = np.ma.masked_array(t, ~mask_transform)

    no_z_component = np.zeros((3, 3))
    np.put(no_z_component, [8, 8], 1)

    transform = masked_array.filled(0) + no_z_component
    return transform.round(4).tolist()


def solve(expected: List[Tuple[float, float]],
          actual: List[Tuple[float, float]]) -> np.ndarray:
    """
    Takes two lists of 3 x-y points each, and calculates the matrix
    representing the transformation from one space to the other.

    The 3x3 matrix returned by this method represents the 2-D transformation
    matrix from the actual point to the expected point.

    Example:
        If the expected points are:
            [ (1, 1),
              (2, 2),
              (1, 2) ]
        And the actual measured points are:
            [ (1.1, 1.1),
              (2.1, 2.1),
              (1.1, 2.1) ]
        (in other words, a shift of exaxtly +0.1 in both x and y)

        Then the resulting transformation matrix T should be:
            [ 1  0  -0.1 ]
            [ 0  1  -0.1 ]
            [ 0  0   1   ]

        Then, if we take a 3x3 matrix B representing one of the measured points
        on the deck:
            [ 1  0  1.1 ]
            [ 0  1  2.1 ]
            [ 0  0  1   ]

        The B*T will yeild the "actual" point:
            [ 1  0  1 ]
            [ 0  1  2 ]
            [ 0  0  1 ]

        The return value of this function is the transformation matrix T
    """
    # Note: input list shape validation is handled by the type checker

    # Turn expected and actual matricies into numpy ndarrays with the last row
    # of [1 1 1] appended, and then take the dot product of the resulting
    # actual matrix with the inverse of the resulting expected matrix.

    # Shape of `expected` and `actual`:
    # [ (x1, y1),
    #   (x2, y2),
    #   (x3, y3) ]
    ex = np.array([
            list(point) + [1]
            for point in expected
        ]).transpose()

    ac = np.array([
            list(point) + [1]
            for point in actual
        ]).transpose()
    # Shape of `ex` and `ac`:
    # [ x1 x2 x3 ]
    # [ y1 y2 y3 ]
    # [  1  1  1 ]

    transform = np.dot(ac, inv(ex))
    # `dot` in numpy is a misnomer. When both arguments are square, N-
    # dimensional arrays, the return type is the result of performing matrix
    # multiplication, rather than the dot-product (so the return here will be
    # a 4x4 matrix)
    return transform


def add_z(xy: np.ndarray, z: float) -> np.ndarray:
    """
    Turn a 2-D transform matrix into a 3-D transform matrix (scale/shift only,
    no rotation).

    :param xy: A two-dimensional transform matrix (a 3x3 numpy ndarray) in the
        following form:
            [ 1  0  x ]
            [ 0  1  y ]
            [ 0  0  1 ]
    :param z: a float for the z component
    :return: a three-dimensional transformation matrix (a 4x4 numpy ndarray)
        with x, y, and z from the function parameters, in the following form:
            [ 1  0  0  x ]
            [ 0  1  0  y ]
            [ 0  0  1  z ]
            [ 0  0  0  1 ]
    """
    # First, insert a column of zeros as into the input matrix
    interm = insert(xy, 2, [0, 0, 0], axis=1)
    # Result:
    # [ 1  0  0  x ]
    # [ 0  1  0  y ]
    # [ 0  0  0  1 ]

    # Then, insert the z row to create a properly formed 3-D transform matrix:
    xyz = insert(
        interm,
        2,
        [0, 0, 1, z],
        axis=0)
    # Result:
    # [ 1  0  0  x ]
    # [ 0  1  0  y ]
    # [ 0  0  1  z ]
    # [ 0  0  0  1 ]

    return xyz.round(11)


def add_matrices(
        t1: Tuple[float, float, float],
        t2: Tuple[float, float, float]) -> Tuple[float, float, float]:
    """
    Simple method to convert tuples to numpy arrays and add them.
    """
    return tuple(np.asarray(t1) + np.asarray(t2))  # type: ignore


def apply_transform(
        t: Union[List[List[float]], np.ndarray],
        pos: AxisPosition,
        with_offsets=True) -> Tuple[float, float, float]:
    """
    Change of base using a transform matrix. Primarily used to render a point
    in space in a way that is more readable for the user.

    :param t: A transformation matrix from one 3D space [A] to another [B]
    :param pos: XYZ point in space A
    :param with_offsets: Whether to apply the transform as an affine transform
                         or as a standard transform. You might use
                         with_offsets=False
    :return: corresponding XYZ point in space B
    """
    if with_offsets:
        return tuple(dot(t, list(pos) + [1])[:3])  # type: ignore
    else:
        return tuple(dot(t, list(pos))[:3])  # type: ignore


def apply_reverse(
        t: Union[List[List[float]], np.ndarray],
        pos: AxisPosition,
        with_offsets=True) -> Tuple[float, float, float]:
    """ Like apply_transform but inverts the transform first
    """
    return apply_transform(inv(t), pos, with_offsets)

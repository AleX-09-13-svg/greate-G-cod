# -*- coding: utf-8 -*-
import math
from collections import OrderedDict

import rhinoscriptsyntax as rs

from cam import config as cam_config
from core import layers as core_layers
from geometry import curves as curve_utils
from plugins import rhino8


def curves_by_layer(curves):
    groups = OrderedDict()
    for curve in sorted(curves, key=lambda item: rhino8.object_layer(item)):
        layer_name = rhino8.object_layer(curve)
        groups.setdefault(layer_name, []).append(curve)
    return groups


def is_cam_curve(curve):
    return core_layers.is_cam_layer(rhino8.object_layer(curve))


def curve_size(curve):
    rectangle_size = rectangular_polyline_size(curve)
    if rectangle_size:
        return rectangle_size

    curve_bounds = curve_utils.bounds([curve])
    if not curve_bounds:
        return None

    width = curve_bounds["max_x"] - curve_bounds["min_x"]
    height = curve_bounds["max_y"] - curve_bounds["min_y"]
    return width, height


def point_distance_xy(a, b):
    dx = a.X - b.X
    dy = a.Y - b.Y
    return math.sqrt(dx * dx + dy * dy)


def same_point_xy(a, b):
    return point_distance_xy(a, b) <= cam_config.SIZE_TOLERANCE_MM


def rectangular_polyline_points(curve):
    try:
        points = list(rs.PolylineVertices(curve) or [])
    except Exception:
        return None

    if len(points) >= 2 and same_point_xy(points[0], points[-1]):
        points = points[:-1]

    if len(points) != 4:
        return None

    return points


def rectangular_polyline_size(curve):
    points = rectangular_polyline_points(curve)
    if not points:
        return None

    lengths = [
        point_distance_xy(points[index], points[(index + 1) % 4])
        for index in range(4)
    ]
    if any(length <= cam_config.SIZE_TOLERANCE_MM for length in lengths):
        return None

    if (
        abs(lengths[0] - lengths[2]) > cam_config.SIZE_TOLERANCE_MM
        or abs(lengths[1] - lengths[3]) > cam_config.SIZE_TOLERANCE_MM
    ):
        return None

    return lengths[0], lengths[1]


def long_side_angle_degrees(curve):
    points = rectangular_polyline_points(curve)
    if not points:
        return None

    side_0 = point_distance_xy(points[0], points[1])
    side_1 = point_distance_xy(points[1], points[2])
    if abs(side_0 - side_1) <= cam_config.SIZE_TOLERANCE_MM:
        return None

    if side_0 > side_1:
        start = points[0]
        end = points[1]
    else:
        start = points[1]
        end = points[2]

    angle = math.degrees(math.atan2(end.Y - start.Y, end.X - start.X))
    while angle < 0.0:
        angle += 180.0
    while angle >= 180.0:
        angle -= 180.0
    return angle


def is_larger_than(width, height, size):
    return width >= size and height >= size


def matches_square_size(width, height, size):
    return (
        abs(width - size) <= cam_config.SIZE_TOLERANCE_MM
        and abs(height - size) <= cam_config.SIZE_TOLERANCE_MM
    )


def matches_any_side_size(width, height, size):
    return (
        abs(width - size) <= cam_config.SIZE_TOLERANCE_MM
        or abs(height - size) <= cam_config.SIZE_TOLERANCE_MM
    )


def classify_curves(curves):
    groups = OrderedDict(
        [
            ("hole_marks", []),
            ("through_holes", []),
            ("pockets_35_15_5", []),
            ("pockets_8", []),
            ("paz_dno_zadnst", []),
            ("perimeters", []),
        ]
    )

    skipped = []
    for curve in curves:
        data = curve_utils.describe(curve)
        if not data["closed"] or not data["planar"]:
            skipped.append(curve)
            continue

        size = curve_size(curve)
        if not size:
            skipped.append(curve)
            continue

        width, height = size
        if matches_square_size(width, height, cam_config.HOLE_MARK_SIZE_MM):
            groups["hole_marks"].append(curve)
        elif matches_square_size(width, height, cam_config.THROUGH_HOLE_SIZE_MM):
            groups["through_holes"].append(curve)
        elif any(
            matches_square_size(width, height, pocket_size)
            for pocket_size in cam_config.POCKET_35_15_5_SIZES_MM
        ):
            groups["pockets_35_15_5"].append(curve)
        elif any(
            matches_square_size(width, height, pocket_size)
            for pocket_size in cam_config.POCKET_8_SIZES_MM
        ):
            groups["pockets_8"].append(curve)
        elif any(
            matches_any_side_size(width, height, paz_side_size)
            for paz_side_size in cam_config.PAZ_DNO_ZADNST_SIDE_SIZES_MM
        ):
            groups["paz_dno_zadnst"].append(curve)
        elif is_larger_than(width, height, cam_config.MIN_CAM_SIZE_MM):
            groups["perimeters"].append(curve)
        else:
            skipped.append(curve)

    return groups, skipped

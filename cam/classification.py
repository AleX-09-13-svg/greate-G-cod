# -*- coding: utf-8 -*-
from collections import OrderedDict

from cam import config as cam_config
from core.layers import is_cam_layer
from geometry import curves as curve_utils
from plugins import rhino8


def curves_by_layer(curves):
    groups = OrderedDict()
    for curve in sorted(curves, key=lambda item: rhino8.object_layer(item)):
        layer_name = rhino8.object_layer(curve)
        groups.setdefault(layer_name, []).append(curve)
    return groups


def is_cam_curve(curve):
    return is_cam_layer(rhino8.object_layer(curve))


def curve_size(curve):
    curve_bounds = curve_utils.bounds([curve])
    if not curve_bounds:
        return None

    width = curve_bounds["max_x"] - curve_bounds["min_x"]
    height = curve_bounds["max_y"] - curve_bounds["min_y"]
    return width, height


def is_larger_than(width, height, size):
    return width > size and height > size


def matches_square_size(width, height, size):
    return (
        abs(width - size) <= cam_config.SIZE_TOLERANCE_MM
        and abs(height - size) <= cam_config.SIZE_TOLERANCE_MM
    )


def classify_curves(curves):
    groups = OrderedDict(
        [
            ("hole_marks", []),
            ("through_holes", []),
            ("pockets", []),
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
            for pocket_size in cam_config.POCKET_SIZES_MM
        ):
            groups["pockets"].append(curve)
        elif is_larger_than(width, height, cam_config.MIN_CAM_SIZE_MM):
            groups["perimeters"].append(curve)
        else:
            skipped.append(curve)

    return groups, skipped

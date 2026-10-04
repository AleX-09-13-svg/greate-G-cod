#! python3
# -*- coding: utf-8 -*-
import re

import rhinoscriptsyntax as rs


TARGET_LAYER_PREFIX = "List"
GRID_RECT_WIDTH_MM = 1081.5
BOUNDS_TOLERANCE_MM = 0.01


def log(message):
    print("[Geometry to zero] {}".format(message))


def layer_index(layer_name):
    match = re.match(r"^{}_(\d+)$".format(TARGET_LAYER_PREFIX), layer_name or "")
    if not match:
        return None
    return int(match.group(1))


def list_layers():
    layers = []
    for layer_name in rs.LayerNames() or []:
        index = layer_index(layer_name)
        if index is not None:
            layers.append((index, layer_name))
    return sorted(layers)


def object_bounds(objects):
    bbox = rs.BoundingBox(objects)
    if not bbox:
        return None

    return {
        "min_x": min(point.X for point in bbox),
        "max_x": max(point.X for point in bbox),
        "min_y": min(point.Y for point in bbox),
        "max_y": max(point.Y for point in bbox),
    }


def expected_layer_offset(index):
    return (index - 1) * GRID_RECT_WIDTH_MM


def layer_already_moved(bounds, expected_offset):
    return bounds["min_x"] < expected_offset - BOUNDS_TOLERANCE_MM


def move_layer_to_zero(index, layer_name):
    objects = rs.ObjectsByLayer(layer_name) or []
    if not objects:
        log("{} skipped: no objects.".format(layer_name))
        return 0

    if index == 1:
        log("{} skipped: first layer is already at zero.".format(layer_name))
        return 0

    bounds = object_bounds(objects)
    if not bounds:
        log("{} skipped: bounds not found.".format(layer_name))
        return 0

    offset_x = expected_layer_offset(index)
    if layer_already_moved(bounds, offset_x):
        log(
            "{} skipped: looks already moved, x_min={:.3f}.".format(
                layer_name, bounds["min_x"]
            )
        )
        return 0

    vector = (-offset_x, 0.0, 0.0)
    moved = rs.MoveObjects(objects, vector) or []
    log(
        "{}: objects={}, moved={}, x_offset={:.3f}.".format(
            layer_name, len(objects), len(moved), -offset_x
        )
    )
    return len(moved)


def run():
    layers = list_layers()
    if not layers:
        log("DONE: no List_* layers found.")
        return False

    log("Found List_* layers: {}".format(", ".join(layer for _, layer in layers)))

    total_moved = 0
    rs.EnableRedraw(False)
    try:
        for index, layer_name in layers:
            total_moved += move_layer_to_zero(index, layer_name)
    finally:
        rs.EnableRedraw(True)

    log("DONE: moved {} objects.".format(total_moved))
    return True


run()

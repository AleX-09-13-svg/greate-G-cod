#! python3
import math

import rhinoscriptsyntax as rs

GROUP_GAP_MM = 80.0
TARGET_LAYER_PREFIX = "List"
TEST_LAYER_NAME = "Test"
BOUNDS_TOLERANCE_MM = 0.01
GRID_RECT_WIDTH_MM = 1081.5
GRID_RECT_HEIGHT_MM = 2600.0
GRID_RECT_COUNT = 50
GRID_ORIGIN_X = 0.0
GRID_ORIGIN_Y = 0.0
GUIDE_LAYER_NAME = "List_Rectangles"


def log(message):
    print("[Geometry to layers] {}".format(message))


def curve_bounds(curve):
    bbox = rs.BoundingBox(curve)
    if not bbox:
        return None

    return {
        "min_x": min(point.X for point in bbox),
        "max_x": max(point.X for point in bbox),
        "min_y": min(point.Y for point in bbox),
        "max_y": max(point.Y for point in bbox),
        "min_z": min(point.Z for point in bbox),
        "max_z": max(point.Z for point in bbox),
    }


def union_bounds(items):
    return {
        "min_x": min(item["bounds"]["min_x"] for item in items),
        "max_x": max(item["bounds"]["max_x"] for item in items),
        "min_y": min(item["bounds"]["min_y"] for item in items),
        "max_y": max(item["bounds"]["max_y"] for item in items),
        "min_z": min(item["bounds"]["min_z"] for item in items),
        "max_z": max(item["bounds"]["max_z"] for item in items),
    }


def bounds_distance_xy(a, b):
    if a["max_x"] < b["min_x"]:
        dx = b["min_x"] - a["max_x"]
    elif b["max_x"] < a["min_x"]:
        dx = a["min_x"] - b["max_x"]
    else:
        dx = 0.0

    if a["max_y"] < b["min_y"]:
        dy = b["min_y"] - a["max_y"]
    elif b["max_y"] < a["min_y"]:
        dy = a["min_y"] - b["max_y"]
    else:
        dy = 0.0

    return math.sqrt(dx * dx + dy * dy)


def color_channels(color):
    if not color:
        return None

    if hasattr(color, "R") and hasattr(color, "G") and hasattr(color, "B"):
        return color.R, color.G, color.B

    try:
        return color[0], color[1], color[2]
    except Exception:
        return None


def object_display_color(obj):
    color = rs.ObjectColor(obj)
    channels = color_channels(color)
    if channels:
        return channels

    layer = rs.ObjectLayer(obj)
    if layer:
        return color_channels(rs.LayerColor(layer))

    return None


def is_red_object(obj):
    channels = object_display_color(obj)
    if not channels:
        return False

    red, green, blue = channels
    return red >= 180 and green <= 100 and blue <= 100


def bounds_contains(outer, inner, tolerance):
    return (
        inner["min_x"] >= outer["min_x"] - tolerance
        and inner["max_x"] <= outer["max_x"] + tolerance
        and inner["min_y"] >= outer["min_y"] - tolerance
        and inner["max_y"] <= outer["max_y"] + tolerance
    )


def is_generated_layer(layer):
    return (
        layer.startswith(TARGET_LAYER_PREFIX + "_")
        or layer == GUIDE_LAYER_NAME
        or layer == TEST_LAYER_NAME
    )


def is_source_curve(obj, include_locked):
    if not include_locked and rs.IsObjectLocked(obj):
        return False

    if not rs.IsCurve(obj):
        return False

    layer = rs.ObjectLayer(obj) or ""
    if is_generated_layer(layer):
        return False

    return True


def join_source_curves():
    source_curves = [
        obj
        for obj in (rs.AllObjects() or [])
        if is_source_curve(obj, include_locked=False)
    ]

    if not source_curves:
        log("Join skipped: no unlocked source curves.")
        return False

    rs.UnselectAllObjects()
    rs.SelectObjects(source_curves)
    ok = rs.Command("_Join", False)
    rs.UnselectAllObjects()
    log("Rhino Join command ok={}".format(ok))
    return ok


def collect_closed_curves(include_locked):
    curves = []
    for obj in rs.AllObjects() or []:
        if not is_source_curve(obj, include_locked) or not rs.IsCurveClosed(obj):
            continue

        bbox = curve_bounds(obj)
        if bbox:
            curves.append({"id": obj, "bounds": bbox})

    return curves


def grid_container_bounds(index):
    min_x = GRID_ORIGIN_X + index * GRID_RECT_WIDTH_MM
    min_y = GRID_ORIGIN_Y
    return {
        "min_x": min_x,
        "max_x": min_x + GRID_RECT_WIDTH_MM,
        "min_y": min_y,
        "max_y": min_y + GRID_RECT_HEIGHT_MM,
        "min_z": 0.0,
        "max_z": 0.0,
    }


def create_grid_containers():
    return [
        {
            "name": "{}_{}".format(TARGET_LAYER_PREFIX, index + 1),
            "bounds": grid_container_bounds(index),
        }
        for index in range(GRID_RECT_COUNT)
    ]


def draw_grid_rectangles(containers):
    if rs.IsLayer(GUIDE_LAYER_NAME):
        was_locked = rs.LayerLocked(GUIDE_LAYER_NAME)
        if was_locked:
            rs.LayerLocked(GUIDE_LAYER_NAME, False)

        old_guides = rs.ObjectsByLayer(GUIDE_LAYER_NAME) or []
        if old_guides:
            rs.DeleteObjects(old_guides)
    else:
        rs.AddLayer(GUIDE_LAYER_NAME, color=(255, 0, 0))

    guide_ids = []
    for container in containers:
        bounds = container["bounds"]
        points = [
            (bounds["min_x"], bounds["min_y"], 0.0),
            (bounds["max_x"], bounds["min_y"], 0.0),
            (bounds["max_x"], bounds["max_y"], 0.0),
            (bounds["min_x"], bounds["max_y"], 0.0),
            (bounds["min_x"], bounds["min_y"], 0.0),
        ]
        rect = rs.AddPolyline(points)
        if rect:
            rs.ObjectLayer(rect, GUIDE_LAYER_NAME)
            guide_ids.append(rect)

    rs.LayerLocked(GUIDE_LAYER_NAME, True)
    log("Guide rectangles created: {}".format(len(guide_ids)))
    return guide_ids


def split_by_grid_containers(curves, containers):
    groups = []
    assigned_ids = set()

    for container in containers:
        group = [
            item
            for item in curves
            if item["id"] not in assigned_ids
            and bounds_contains(
                container["bounds"], item["bounds"], BOUNDS_TOLERANCE_MM
            )
        ]

        if not group:
            continue

        groups.append({"name": container["name"], "items": group})
        for item in group:
            assigned_ids.add(item["id"])

    return groups


def split_by_red_containers(curves, containers):
    groups = []
    assigned_ids = set()

    sorted_containers = sorted(
        containers,
        key=lambda item: (item["bounds"]["min_x"], item["bounds"]["min_y"]),
    )

    for container in sorted_containers:
        group = [
            item
            for item in curves
            if item["id"] != container["id"]
            and item["id"] not in assigned_ids
            and bounds_contains(
                container["bounds"], item["bounds"], BOUNDS_TOLERANCE_MM
            )
        ]

        if not group:
            continue

        groups.append(group)
        for item in group:
            assigned_ids.add(item["id"])

    return groups


def split_into_groups(curves, max_gap):
    remaining = sorted(
        curves, key=lambda item: (item["bounds"]["min_x"], item["bounds"]["min_y"])
    )
    groups = []

    while remaining:
        group = [remaining.pop(0)]
        changed = True

        while changed:
            changed = False
            for item in remaining[:]:
                close_to_group = any(
                    bounds_distance_xy(item["bounds"], other["bounds"]) <= max_gap
                    for other in group
                )
                if close_to_group:
                    group.append(item)
                    remaining.remove(item)
                    changed = True

        groups.append(group)

    return sorted(
        groups,
        key=lambda group: (union_bounds(group)["min_x"], union_bounds(group)["min_y"]),
    )


def ensure_layer(layer_name):
    if not rs.IsLayer(layer_name):
        rs.AddLayer(layer_name)
    return layer_name


def ensure_unlocked_layer(layer_name, color=None):
    if not rs.IsLayer(layer_name):
        rs.AddLayer(layer_name, color=color)
    elif rs.LayerLocked(layer_name):
        rs.LayerLocked(layer_name, False)
    return layer_name


def add_rectangle(min_x, min_y, width, height, layer_name):
    points = [
        (min_x, min_y, 0.0),
        (min_x + width, min_y, 0.0),
        (min_x + width, min_y + height, 0.0),
        (min_x, min_y + height, 0.0),
        (min_x, min_y, 0.0),
    ]
    curve = rs.AddPolyline(points)
    if curve:
        rs.ObjectLayer(curve, layer_name)
    return curve


def add_circle(center_x, center_y, diameter, layer_name):
    curve = rs.AddCircle((center_x, center_y, 0.0), diameter / 2.0)
    if curve:
        rs.ObjectLayer(curve, layer_name)
    return curve


def create_test_layer():
    ensure_unlocked_layer(TEST_LAYER_NAME)

    old_objects = rs.ObjectsByLayer(TEST_LAYER_NAME) or []
    if old_objects:
        rs.DeleteObjects(old_objects)

    previous_layer = rs.CurrentLayer()
    rs.CurrentLayer(TEST_LAYER_NAME)
    created = []
    try:
        # CAM classification control geometry.
        created.append(add_rectangle(20.0, 20.0, 200.0, 200.0, TEST_LAYER_NAME))
        created.append(add_rectangle(201.0, 21.0, 6.0, 198.0, TEST_LAYER_NAME))

        created.append(add_circle(60.414, 212.0, 4.9, TEST_LAYER_NAME))
        created.append(add_circle(156.414, 212.0, 4.9, TEST_LAYER_NAME))

        created.append(add_circle(28.0, 89.049, 8.0, TEST_LAYER_NAME))
        created.append(add_circle(28.0, 121.049, 5.0, TEST_LAYER_NAME))
        created.append(add_circle(28.0, 57.049, 5.0, TEST_LAYER_NAME))

        created.append(add_circle(62.0, 121.049, 15.0, TEST_LAYER_NAME))
        created.append(add_circle(62.0, 57.049, 15.0, TEST_LAYER_NAME))

        created.append(add_circle(40.0, 171.125, 3.0, TEST_LAYER_NAME))
        created.append(add_circle(72.0, 171.125, 3.0, TEST_LAYER_NAME))

        created.append(add_circle(120.0, 41.5, 35.0, TEST_LAYER_NAME))
    finally:
        if previous_layer and rs.IsLayer(previous_layer):
            rs.CurrentLayer(previous_layer)

    created = [item for item in created if item]
    log("{} layer created: objects={}.".format(TEST_LAYER_NAME, len(created)))
    return len(created)


def copy_group_to_layer(group, layer_name):
    ensure_layer(layer_name)
    copied = []

    for item in group:
        duplicate = rs.CopyObject(item["id"])
        if duplicate:
            rs.ObjectLayer(duplicate, layer_name)
            copied.append(duplicate)

    return copied


def run():
    rs.EnableRedraw(False)
    try:
        join_source_curves()
        grid_containers = create_grid_containers()
        draw_grid_rectangles(grid_containers)
    finally:
        rs.EnableRedraw(True)

    curves = collect_closed_curves(include_locked=False)
    log("Closed curves found: {}".format(len(curves)))

    if not curves:
        log("DONE: no closed curves found.")
        return False

    groups = split_by_grid_containers(curves, grid_containers)

    if groups:
        log("Grid container groups found: {}".format(len(groups)))
    else:
        log("No grid container groups found. Using distance grouping.")
        groups = split_into_groups(curves, GROUP_GAP_MM)

    log("Groups found: {}".format(len(groups)))

    rs.EnableRedraw(False)
    try:
        all_copies = []
        for index, group_data in enumerate(groups, 1):
            if isinstance(group_data, dict):
                layer_name = group_data["name"]
                group = group_data["items"]
            else:
                layer_name = "{}_{}".format(TARGET_LAYER_PREFIX, index)
                group = group_data

            copied = copy_group_to_layer(group, layer_name)
            all_copies.extend(copied)

            bounds = union_bounds(group)
            log(
                "{}: source_objects={}, copied={}, x_min={:.3f}, x_max={:.3f}".format(
                    layer_name,
                    len(group),
                    len(copied),
                    bounds["min_x"],
                    bounds["max_x"],
                )
            )

        rs.UnselectAllObjects()
        if all_copies:
            rs.SelectObjects(all_copies)

        log(
            "DONE: copied {} objects to {} layers.".format(len(all_copies), len(groups))
        )
        create_test_layer()
        return True
    finally:
        rs.EnableRedraw(True)


run()

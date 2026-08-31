import rhinoscriptsyntax as rs


def all_curves():
    objects = rs.AllObjects() or []
    return [obj for obj in objects if rs.IsCurve(obj)]


def bounds(objects):
    points = []
    for obj in objects:
        bbox = rs.BoundingBox(obj)
        if bbox:
            points.extend(bbox)

    if not points:
        return None

    return {
        "min_x": min(point.X for point in points),
        "max_x": max(point.X for point in points),
        "min_y": min(point.Y for point in points),
        "max_y": max(point.Y for point in points),
        "min_z": min(point.Z for point in points),
        "max_z": max(point.Z for point in points),
    }


def describe(curve):
    curve_bounds = bounds([curve])
    return {
        "layer": rs.ObjectLayer(curve) or "Unnamed",
        "closed": rs.IsCurveClosed(curve),
        "planar": rs.IsCurvePlanar(curve),
        "z_min": curve_bounds["min_z"] if curve_bounds else None,
        "z_max": curve_bounds["max_z"] if curve_bounds else None,
    }

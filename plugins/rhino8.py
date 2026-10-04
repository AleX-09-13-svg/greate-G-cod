import os
import rhinoscriptsyntax as rs


def document_or_current_dir():
    doc_path = rs.DocumentPath()
    if doc_path:
        return doc_path
    return os.getcwd()


def script_dir(file_path):
    try:
        return os.path.dirname(os.path.abspath(file_path))
    except Exception:
        return document_or_current_dir()


def select_objects(objects):
    rs.UnselectAllObjects()
    for obj in objects:
        rs.SelectObject(obj)


def object_layer(obj):
    return rs.ObjectLayer(obj) or "Unnamed"


def layer_state_snapshot():
    return {
        "current": rs.CurrentLayer(),
        "visibility": {
            layer_name: rs.LayerVisible(layer_name)
            for layer_name in (rs.LayerNames() or [])
        },
    }


def isolate_layer(layer_name):
    if not rs.IsLayer(layer_name):
        return False

    if not rs.LayerVisible(layer_name):
        rs.LayerVisible(layer_name, True)
    rs.CurrentLayer(layer_name)

    for name in rs.LayerNames() or []:
        rs.LayerVisible(name, name == layer_name)

    return True


def restore_layer_state(snapshot):
    visibility = snapshot.get("visibility", {})
    current = snapshot.get("current")

    for layer_name, visible in visibility.items():
        if visible and rs.IsLayer(layer_name):
            rs.LayerVisible(layer_name, True)

    if current and rs.IsLayer(current):
        rs.CurrentLayer(current)
    else:
        for layer_name, visible in visibility.items():
            if visible and rs.IsLayer(layer_name):
                rs.CurrentLayer(layer_name)
                break

    for layer_name, visible in visibility.items():
        if rs.IsLayer(layer_name):
            rs.LayerVisible(layer_name, visible)


def clean_windows_filename(name):
    if not name:
        return "Unnamed"

    cleaned = name
    for char in '<>:"/\\|?*':
        cleaned = cleaned.replace(char, "_")
    return cleaned.strip(" ._") or "Unnamed"

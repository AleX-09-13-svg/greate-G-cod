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


def clean_windows_filename(name):
    if not name:
        return "Unnamed"

    cleaned = name
    for char in '<>:"/\\|?*':
        cleaned = cleaned.replace(char, "_")
    return cleaned.strip(" ._") or "Unnamed"

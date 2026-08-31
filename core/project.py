# -*- coding: utf-8 -*-
import os


DEFAULT_PROJECT_ROOT = "G:\\\u041c\u043e\u0439 \u0434\u0438\u0441\u043a\\\u0421\u043a\u0440\u0438\u043f\u0442\u044b python\\create _G_code"
PROJECT_MARKERS = (
    ("geometry", "curves.py"),
    ("plugins", "rhino8.py"),
    ("plugins", "rhinocam.py"),
    ("cam", "operations.py"),
)


def looks_like_project_root(path):
    return bool(path) and all(
        os.path.isfile(os.path.join(path, *marker)) for marker in PROJECT_MARKERS
    )


def candidate_parent_dirs(path):
    if not path:
        return

    current = os.path.abspath(path)
    if os.path.isfile(current):
        current = os.path.dirname(current)

    while True:
        yield current
        parent = os.path.dirname(current)
        if parent == current:
            break
        current = parent


def find_project_root(script_file=None):
    hints = [
        os.environ.get("RHINOCAM_PROJECT_ROOT"),
        script_file,
        os.getcwd(),
        DEFAULT_PROJECT_ROOT,
    ]

    try:
        import rhinoscriptsyntax as rs

        doc_path = rs.DocumentPath()
        if doc_path:
            hints.append(doc_path)
    except Exception:
        pass

    for hint in hints:
        for candidate in candidate_parent_dirs(hint):
            if looks_like_project_root(candidate):
                return candidate

    if script_file:
        return os.path.dirname(os.path.abspath(script_file))
    return os.getcwd()

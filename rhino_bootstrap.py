# -*- coding: utf-8 -*-
import importlib
import __main__
import os
import sys


DEFAULT_PROJECT_ROOTS = (
    "D:\\\u041a\u043e\u043f\u0438\u044f Google \u0434\u0438\u0441\u043a\u0430\\02_\u0421\u043a\u0440\u0438\u043f\u0442\u044b\\01_\u0421\u043a\u0440\u0438\u043f\u0442\u044b \u0434\u043b\u044f \u0440\u0430\u0431\u043e\u0442\u044b\\create _G_code",
    "G:\\\u041c\u043e\u0439 \u0434\u0438\u0441\u043a\\\u0421\u043a\u0440\u0438\u043f\u0442\u044b python\\create _G_code",
    r"D:\Копия Google диска\02_Скрипты\01_Скрипты для работы\create _G_code",
    r"G:\Мой диск\Скрипты python\create _G_code",
)

PROJECT_MARKERS = (
    ("geometry", "curves.py"),
    ("plugins", "rhino8.py"),
    ("plugins", "rhinocam.py"),
    ("cam", "operations.py"),
)


def script_file(default_name):
    try:
        return __main__.__file__
    except Exception:
        return os.path.abspath(default_name)


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


def rhino_document_path():
    try:
        import rhinoscriptsyntax as rs

        return rs.DocumentPath()
    except Exception:
        return None


def find_project_root(script_path=None, extra_hints=None):
    hints = [
        os.environ.get("RHINOCAM_PROJECT_ROOT"),
        script_path,
        os.getcwd(),
    ]
    hints.extend(DEFAULT_PROJECT_ROOTS)

    doc_path = rhino_document_path()
    if doc_path:
        hints.append(doc_path)

    if extra_hints:
        hints.extend(extra_hints)

    for hint in hints:
        for candidate in candidate_parent_dirs(hint):
            if looks_like_project_root(candidate):
                return candidate

    if script_path:
        return os.path.dirname(os.path.abspath(script_path))
    return os.getcwd()


def bootstrap(script_path=None, extra_hints=None):
    project_root = find_project_root(script_path, extra_hints)
    if project_root not in sys.path:
        sys.path.insert(0, project_root)

    try:
        from core.project import find_project_root as refined_project_root

        project_root = refined_project_root(script_path)
        if project_root not in sys.path:
            sys.path.insert(0, project_root)
    except Exception:
        pass

    try:
        importlib.invalidate_caches()
    except AttributeError:
        pass

    return project_root

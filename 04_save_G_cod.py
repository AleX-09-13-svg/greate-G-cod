# -*- coding: utf-8 -*-
import importlib
import os
import sys


SCRIPT_VERSION = "04_save_G_cod bootstrap 2026-10-06 02"

try:
    SCRIPT_FILE = __file__
except NameError:
    SCRIPT_FILE = os.path.abspath("04_save_G_cod.py")

print("{} from {}".format(SCRIPT_VERSION, SCRIPT_FILE))

def candidate_parent_dirs_for_bootstrap(path):
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


def load_rhino_bootstrap():
    hints = [
        os.environ.get("RHINOCAM_PROJECT_ROOT"),
        SCRIPT_FILE,
        os.getcwd(),
        "D:\\\u041a\u043e\u043f\u0438\u044f Google \u0434\u0438\u0441\u043a\u0430\\02_\u0421\u043a\u0440\u0438\u043f\u0442\u044b\\01_\u0421\u043a\u0440\u0438\u043f\u0442\u044b \u0434\u043b\u044f \u0440\u0430\u0431\u043e\u0442\u044b\\create _G_code",
        "G:\\\u041c\u043e\u0439 \u0434\u0438\u0441\u043a\\\u0421\u043a\u0440\u0438\u043f\u0442\u044b python\\create _G_code",
        r"D:\Копия Google диска\02_Скрипты\01_Скрипты для работы\create _G_code",
        r"G:\Мой диск\Скрипты python\create _G_code",
    ]

    try:
        import rhinoscriptsyntax as rs

        doc_path = rs.DocumentPath()
        if doc_path:
            hints.append(doc_path)
    except Exception:
        pass

    for hint in hints:
        for candidate in candidate_parent_dirs_for_bootstrap(hint):
            module_path = os.path.join(candidate, "rhino_bootstrap.py")
            if os.path.isfile(module_path):
                spec = importlib.util.spec_from_file_location(
                    "rhino_bootstrap", module_path
                )
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                return module

    raise ImportError("rhino_bootstrap.py not found")


PROJECT_ROOT = load_rhino_bootstrap().bootstrap(SCRIPT_FILE)

from core import files as core_files


GCODE_EXTENSIONS = (".nc", ".tap", ".cnc", ".gcode", ".txt")
_RHINOCAM_PLUGIN = None


def clean_windows_filename(name):
    if not name:
        return "Unnamed"

    cleaned = name
    for char in '<>:"/\\|?*':
        cleaned = cleaned.replace(char, "_")
    return cleaned.strip(" ._") or "Unnamed"


def rhinocam_plugin():
    global _RHINOCAM_PLUGIN
    if _RHINOCAM_PLUGIN is not None:
        return _RHINOCAM_PLUGIN

    from plugins import rhinocam

    try:
        _RHINOCAM_PLUGIN = importlib.reload(rhinocam)
    except AttributeError:
        from imp import reload as reload_module

        _RHINOCAM_PLUGIN = reload_module(rhinocam)
    except Exception:
        _RHINOCAM_PLUGIN = rhinocam

    return _RHINOCAM_PLUGIN


def choose_output_dir(default_dir):
    output_dir = default_dir
    try:
        import tkinter as tk
        from tkinter import filedialog

        root = tk.Tk()
        root.withdraw()
        root.attributes("-topmost", True)
        selected_dir = filedialog.askdirectory(
            title="Select G-code output folder",
            initialdir=default_dir,
            parent=root,
        )
        root.destroy()
        if selected_dir:
            output_dir = selected_dir
    except Exception:
        output_dir = default_dir

    if not os.path.isdir(output_dir):
        os.makedirs(output_dir)
    return output_dir


def setup_name(setup, fallback_name=None):
    for method_name in ("GetName", "Name"):
        getter = getattr(setup, method_name, None)
        if not getter:
            continue
        try:
            value = getter() if callable(getter) else getter
        except Exception:
            continue
        if value:
            return str(value)

    try:
        value = rhinocam_plugin().setup_name(setup)
    except Exception:
        value = None
    if value:
        return str(value)

    return fallback_name or "Setup"


def target_gcode_path(output_dir, setup, fallback_name=None):
    name = clean_windows_filename(setup_name(setup, fallback_name))
    return os.path.join(output_dir, "{}.nc".format(name))


def is_gcode_file(path):
    return os.path.splitext(path)[1].lower() in GCODE_EXTENSIONS


def latest_gcode_file(output_dir):
    candidates = []
    for name in os.listdir(output_dir):
        path = os.path.join(output_dir, name)
        if os.path.isfile(path) and is_gcode_file(path):
            candidates.append(path)
    if not candidates:
        return None
    return max(candidates, key=os.path.getmtime)


class GCodeSaver(object):
    def __init__(self, output_dir, log=None):
        self.output_dir = output_dir
        self.log = log or (lambda message: None)
        if not os.path.isdir(self.output_dir):
            os.makedirs(self.output_dir)

    def post_process_setup(self, setup, fallback_name=None):
        before_files = core_files.file_snapshot(self.output_dir)
        rhinocam = rhinocam_plugin()
        ok, method_name = rhinocam.post_process_setup(self.output_dir, setup)
        if not ok:
            self.log("ERROR: post-process failed.")
            return False

        changed_file = core_files.detect_changed_file(self.output_dir, before_files)
        if not changed_file:
            changed_file = latest_gcode_file(self.output_dir)
        if not changed_file:
            self.log("ERROR: post-process did not create a G-code file.")
            return False

        target_path = target_gcode_path(self.output_dir, setup, fallback_name)
        try:
            saved_path = core_files.rename_file(changed_file, target_path)
        except Exception as ex:
            self.log("ERROR: failed to rename G-code file: {}".format(ex))
            return False

        self.log(
            "G-code saved by {}: {}".format(
                method_name or "post-process",
                saved_path,
            )
        )
        return True


def save_existing_setups(output_dir=None, log=None):
    log = log or (lambda message: None)
    if output_dir is None:
        output_dir = choose_output_dir(os.path.join(PROJECT_ROOT, "GCode"))

    rhinocam = rhinocam_plugin()
    saver = GCodeSaver(output_dir, log)
    log("G-code output dir: {}".format(output_dir))
    rhinocam.sync_database()
    setups = rhinocam.all_setups()
    log("RhinoCAM setups found: {}".format(len(setups)))
    if not setups:
        method_names = rhinocam.mop_manager_method_names()
        log("ERROR: no RhinoCAM setups found.")
        try:
            log("Setup discovery: {}".format(rhinocam.setup_discovery_report()))
        except Exception as ex:
            log("Setup discovery failed: {}".format(ex))
        log("MOpManager methods: {}".format(", ".join(method_names)))
        return False

    had_errors = False
    for setup in setups:
        if not saver.post_process_setup(setup):
            had_errors = True
    return not had_errors


if __name__ == "__main__":
    def main_log(message):
        print(message)

    rhinocam = rhinocam_plugin()
    rhinocam.initialize_mill()
    try:
        if not save_existing_setups(log=main_log):
            print("ERROR: G-code save finished with errors.")
    finally:
        rhinocam.uninitialize()

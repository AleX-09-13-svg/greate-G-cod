#! python3
# -*- coding: utf-8 -*-
import importlib
import os
import sys


try:
    SCRIPT_FILE = __file__
except NameError:
    SCRIPT_FILE = os.path.abspath("03main.py")

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

from cam import job as cam_job

try:
    cam_job = importlib.reload(cam_job)
except AttributeError:
    from imp import reload as reload_module

    cam_job = reload_module(cam_job)


def ask_cut_depth(default_depth):
    try:
        import tkinter as tk
        from tkinter import messagebox
        from tkinter import simpledialog
    except Exception:
        return default_depth

    root = None
    try:
        root = tk.Tk()
        root.withdraw()
        root.attributes("-topmost", True)

        while True:
            value = simpledialog.askstring(
                "Глубина реза",
                "Введите глубину сквозного реза, мм:",
                initialvalue=str(default_depth),
                parent=root,
            )
            if value is None or value.strip() == "":
                return default_depth

            value = value.replace(",", ".").strip()
            try:
                depth = float(value)
            except ValueError:
                messagebox.showerror(
                    "Глубина реза",
                    "Введите число, например 17.2",
                    parent=root,
                )
                continue

            if depth <= 0:
                messagebox.showerror(
                    "Глубина реза",
                    "Глубина должна быть больше 0.",
                    parent=root,
                )
                continue

            return depth
    except Exception:
        return default_depth
    finally:
        if root is not None:
            try:
                root.destroy()
            except Exception:
                pass


default_cut_depth = cam_job.cam_config.STRATEGIES["skvoznoe"]["depth"]
cut_depth = ask_cut_depth(default_cut_depth)
cam_job.cam_config.STRATEGIES["skvoznoe"]["depth"] = cut_depth
cam_job.cam_config.STRATEGIES["raskroy"]["depth"] = cut_depth
cam_job.cam_config.DEFAULT_STOCK_ALLOWANCE_MM = 0.0
for strategy_settings in cam_job.cam_config.STRATEGIES.values():
    strategy_settings["stock_allowance"] = 0.0
cam_job.run(PROJECT_ROOT, save_gcode=True)

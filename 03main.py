#! python3
# -*- coding: utf-8 -*-
import importlib
import os
import sys


PROJECT_ROOT = "G:\\\u041c\u043e\u0439 \u0434\u0438\u0441\u043a\\\u0421\u043a\u0440\u0438\u043f\u0442\u044b python\\create _G_code"
if not os.path.isdir(PROJECT_ROOT):
    PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from core.project import find_project_root


PROJECT_ROOT = find_project_root(__file__)
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

try:
    importlib.invalidate_caches()
except AttributeError:
    pass

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

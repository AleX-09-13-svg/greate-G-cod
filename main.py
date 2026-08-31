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


cam_job.run(PROJECT_ROOT)

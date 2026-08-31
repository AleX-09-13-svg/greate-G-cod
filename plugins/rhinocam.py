import json
import os

from mecsoftcamapi import *

from MecSoftCAM.Managers import MOpManager
from MecSoftCAM.Managers import StockManager
from MecSoftCAM.Managers import ToolManager
from MecSoftCAM.Types import DrillToolType
from MecSoftCAM.Types import MillToolType
from MecSoftCAM.Types import ModuleType


MILL_TOOL_TYPES = {
    "MTOOL_FLAT": MillToolType.MTOOL_FLAT,
    "MTOOL_BALL": MillToolType.MTOOL_BALL,
}


def initialize_mill():
    MecSoftCAM.API.Initialize()
    MecSoftCAM.API.SetActiveModule(ModuleType.MILL)


def uninitialize():
    MecSoftCAM.API.Uninitialize()


def sync_database():
    MecSoftCAM.API.SyncDatabase()


def load_tool_config(path):
    with open(path, "r") as stream:
        return json.load(stream)


def create_mill_tool(tool_config):
    tool_type_name = tool_config.get("type", "MTOOL_FLAT")
    tool_type = MILL_TOOL_TYPES.get(tool_type_name, MillToolType.MTOOL_FLAT)
    tool = ToolManager.CreateMillTool(tool_type)
    if not tool:
        return None

    tool.SetDia(float(tool_config["diameter"]))
    tool.SetName(tool_config.get("name", "Flat mill"))
    tool.SetFluteLen(float(tool_config["flute_length"]))
    tool.SetLen(float(tool_config["length"]))
    tool.SetShankDia(float(tool_config.get("shank_diameter", tool_config["diameter"])))
    ToolManager.SetActiveTool(tool)
    return tool


def create_drill_tool(diameter, name=None):
    tool = ToolManager.CreateDrillTool(DrillToolType.DTOOL_DRILL)
    if not tool:
        return None

    tool.SetDia(float(diameter))
    tool.SetName(name or "Drill D{}".format(diameter))
    tool.SetFluteLen(float(diameter) * 4.0)
    tool.SetLen(float(diameter) * 8.0)
    ToolManager.SetActiveTool(tool)
    return tool


def create_mop_setup(name):
    setup = MOpManager.CreateMOpSetup()
    if not setup:
        return None

    set_name = getattr(setup, "SetName", None)
    if set_name:
        set_name(name)

    MOpManager.SetActiveSetup(setup)
    return setup


def activate_setup(setup):
    if not setup:
        return False
    try:
        MOpManager.SetActiveSetup(setup)
        MecSoftCAM.API.SyncDatabase()
        return True
    except Exception:
        return False


def create_box_stock(bounds, top_z, depth, xy_offset):
    min_x = bounds["min_x"] - xy_offset
    max_x = bounds["max_x"] + xy_offset
    min_y = bounds["min_y"] - xy_offset
    max_y = bounds["max_y"] + xy_offset
    bottom_z = top_z - depth

    StockManager.DeleteStock()
    return StockManager.CreateBoxStock(
        min_x,
        min_y,
        bottom_z,
        0,
        depth,
        max_y - min_y,
        max_x - min_x,
        False,
    )


def active_postprocessor():
    return MOpManager.GetPostProcessor()


def post_process_mop(output_dir, mop):
    if not os.path.isdir(output_dir):
        os.makedirs(output_dir)
    return MOpManager.PostProcessMOp(output_dir + os.sep, mop)


def post_process_setup(output_dir, setup):
    if not os.path.isdir(output_dir):
        os.makedirs(output_dir)

    for method_name in (
        "PostProcessMOpSetUp",
        "PostProcessMOpSetup",
        "PostProcessSetup",
        "PostProcessMOpSet",
        "PostProcessMOp",
    ):
        method = getattr(MOpManager, method_name, None)
        if method:
            try:
                return method(output_dir + os.sep, setup), method_name
            except Exception:
                continue

    return False, None

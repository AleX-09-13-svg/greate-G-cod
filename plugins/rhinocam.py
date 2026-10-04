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


def activate_setup(setup, sync=True):
    if not setup:
        return False
    try:
        MOpManager.SetActiveSetup(setup)
        if sync:
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


def mop_manager_method_names():
    keywords = (
        "active",
        "count",
        "list",
        "mop",
        "operation",
        "post",
        "process",
        "setup",
        "set",
    )
    names = []
    for name in dir(MOpManager):
        lower_name = name.lower()
        if name.startswith("_"):
            continue
        if any(keyword in lower_name for keyword in keywords):
            names.append(name)
    return sorted(set(names))


def setup_name(setup):
    if not setup:
        return None

    for method_name in ("GetName", "Name"):
        value = getattr(setup, method_name, None)
        if callable(value):
            try:
                return value()
            except Exception:
                continue
        if value:
            return value

    return str(setup)


def _list_items(collection):
    if not collection:
        return []

    try:
        return list(collection)
    except TypeError:
        pass

    count = getattr(collection, "Count", None)
    if callable(count):
        try:
            count = count()
        except Exception:
            count = None

    if count is None:
        return []

    items = []
    for index in range(int(count)):
        try:
            item = collection[index]
        except Exception:
            try:
                item = collection.Item(index)
            except Exception:
                try:
                    item = collection.Item(index + 1)
                except Exception:
                    continue
        if item:
            items.append(item)

    return items


def setup_mops(setup):
    if not setup:
        return []

    for method_name in (
        "GetMOps",
        "GetMOpList",
        "GetOperations",
        "GetOperationList",
        "GetChildren",
    ):
        method = getattr(setup, method_name, None)
        if not method:
            continue

        try:
            mops = method()
        except Exception:
            continue

        mop_list = _list_items(mops)
        if mop_list:
            return mop_list

    for count_method_name, item_method_name in (
        ("GetMOpCount", "GetMOp"),
        ("GetOperationCount", "GetOperation"),
        ("GetChildCount", "GetChild"),
        ("Count", "Item"),
    ):
        count_method = getattr(setup, count_method_name, None)
        item_method = getattr(setup, item_method_name, None)
        if not count_method or not item_method:
            continue

        try:
            count = int(count_method() if callable(count_method) else count_method)
        except Exception:
            continue

        mops = []
        for index in range(count):
            try:
                mop = item_method(index)
            except Exception:
                try:
                    mop = item_method(index + 1)
                except Exception:
                    continue
            if mop:
                mops.append(mop)

        if mops:
            return mops

    return []


def mop_name(mop):
    if not mop:
        return None

    for method_name in ("GetName", "Name"):
        value = getattr(mop, method_name, None)
        if callable(value):
            try:
                return value()
            except Exception:
                continue
        if value:
            return value

    return None


def setup_has_mop(setup, mop_name_to_find):
    for mop in setup_mops(setup):
        if (mop_name(mop) or "").lower() == (mop_name_to_find or "").lower():
            return True
    return False


def all_mops():
    mops = []
    seen = set()

    def add_mop(mop):
        if not mop:
            return
        key = str(mop)
        if key in seen:
            return
        seen.add(key)
        mops.append(mop)

    for setup in all_setups():
        for mop in setup_mops(setup):
            add_mop(mop)

    for method_name in (
        "GetMOps",
        "GetMOpList",
        "GetOperations",
        "GetOperationList",
        "GetAllMOps",
        "GetAllMops",
    ):
        method = getattr(MOpManager, method_name, None)
        if not method:
            continue

        try:
            items = method()
        except Exception:
            continue

        for mop in _list_items(items):
            add_mop(mop)

    for count_method_name, item_method_name in (
        ("GetMOpCount", "GetMOp"),
        ("GetOperationCount", "GetOperation"),
        ("Count", "Item"),
    ):
        count_method = getattr(MOpManager, count_method_name, None)
        item_method = getattr(MOpManager, item_method_name, None)
        if not count_method or not item_method:
            continue

        try:
            count = int(count_method() if callable(count_method) else count_method)
        except Exception:
            continue

        for index in range(count):
            try:
                mop = item_method(index)
            except Exception:
                try:
                    mop = item_method(index + 1)
                except Exception:
                    continue
            add_mop(mop)

    for method_name in ("GetActiveMOp", "GetActiveOperation"):
        method = getattr(MOpManager, method_name, None)
        if not method:
            continue
        try:
            add_mop(method())
        except Exception:
            continue

    return mops


def all_setups():
    for method_name in (
        "GetMOpSets",
        "GetMOpSetList",
        "GetMOpSetups",
        "GetMOpSetUps",
        "GetMOpSetUpList",
        "GetMOpSetupList",
        "GetSetups",
        "GetSetupList",
    ):
        method = getattr(MOpManager, method_name, None)
        if not method:
            continue

        try:
            setups = method()
        except Exception:
            continue

        setup_list = _list_items(setups)
        if setup_list:
            return setup_list

    for count_method_name, item_method_name in (
        ("GetMOpSetCount", "GetMOpSet"),
        ("GetMOpSetupCount", "GetMOpSetup"),
        ("GetMOpSetUpCount", "GetMOpSetUp"),
        ("GetSetupCount", "GetSetup"),
    ):
        count_method = getattr(MOpManager, count_method_name, None)
        item_method = getattr(MOpManager, item_method_name, None)
        if not count_method or not item_method:
            continue

        try:
            count = int(count_method())
        except Exception:
            continue

        setups = []
        for index in range(count):
            try:
                setup = item_method(index)
            except Exception:
                try:
                    setup = item_method(index + 1)
                except Exception:
                    continue
            if setup:
                setups.append(setup)

        if setups:
            return setups

    active_setup = getattr(MOpManager, "GetActiveSetup", None)
    if active_setup:
        try:
            setup = active_setup()
        except Exception:
            setup = None
        if setup:
            return [setup]

    active_setup = getattr(MOpManager, "GetActiveMOpSet", None)
    if active_setup:
        try:
            setup = active_setup()
        except Exception:
            setup = None
        if setup:
            return [setup]

    active_setup = getattr(MOpManager, "GetActiveMOpSetup", None)
    if active_setup:
        try:
            setup = active_setup()
        except Exception:
            setup = None
        if setup:
            return [setup]

    return []


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

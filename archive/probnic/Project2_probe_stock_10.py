#! python3
from mecsoftcamapi import *
import os
import rhinoscriptsyntax as rs

from MecSoftCAM.Managers import MOpManager
from MecSoftCAM.Managers import SelectionManager
from MecSoftCAM.Managers import StockManager
from MecSoftCAM.Managers import ToolManager
from MecSoftCAM.Types import ContourClearanceTransferType
from MecSoftCAM.Types import ContourClearanceType
from MecSoftCAM.Types import ContourCutDirection
from MecSoftCAM.Types import ContourCutSideType
from MecSoftCAM.Types import ContourEngRetType
from MecSoftCAM.Types import ContourEntryType
from MecSoftCAM.Types import ContourExitType
from MecSoftCAM.Types import MillToolType
from MecSoftCAM.Types import ModuleType


class Config(object):
    TOOL_DIAMETER = 3.0
    TOOL_FLUTE_LENGTH = 9.0
    TOOL_LENGTH = 24.0

    CUT_TOP_Z = 0.0
    CUT_DEPTH = 16.0
    STEP_DOWN = 4.0
    TOLERANCE = 0.01

    STOCK_XY_OFFSET = 1.0
    CUT_GEOM_LOCATION_TOP = 0

    CLEARANCE_Z = 5.0
    RETRACT_DISTANCE = 1.0

    PLUNGE_FEED = 300.0
    APPROACH_FEED = 400.0
    ENGAGE_FEED = 400.0
    CUT_FEED = 800.0
    RETRACT_FEED = 1000.0
    DEPARTURE_FEED = 1000.0

    OUTPUT_DIR_NAME = "GCode"


TOOL_DIAMETER = Config.TOOL_DIAMETER
CUT_TOP_Z = Config.CUT_TOP_Z
CUT_DEPTH = Config.CUT_DEPTH
STEP_DOWN = Config.STEP_DOWN
STOCK_XY_OFFSET = Config.STOCK_XY_OFFSET
CUT_GEOM_LOCATION_TOP = Config.CUT_GEOM_LOCATION_TOP


def log(message):
    print("[RhinoCAM refactor 10] " + message)


def set_param(name, setter, value):
    try:
        ok = setter(value)
    except Exception as ex:
        log("ERROR: {} raised {}".format(name, ex))
        return False
    if not ok:
        log("WARNING: {} was not accepted: {}".format(name, value))
    return ok


def clean_filename(name):
    if not name:
        return "Unnamed"
    cleaned = name
    for char in '<>:"/\\|?*':
        cleaned = cleaned.replace(char, "_")
    cleaned = cleaned.strip(" ._")
    return cleaned or "Unnamed"


def get_script_dir():
    try:
        return os.path.dirname(os.path.abspath(__file__))
    except Exception:
        doc_path = rs.DocumentPath()
        if doc_path:
            return doc_path
    return os.getcwd()


def get_gcode_dir():
    output_dir = os.path.join(get_script_dir(), Config.OUTPUT_DIR_NAME)
    if not os.path.isdir(output_dir):
        os.makedirs(output_dir)
    return output_dir


def get_layer_name(curves):
    if not curves:
        return "Unnamed"
    return rs.ObjectLayer(curves[0]) or "Unnamed"


def get_all_curves():
    all_objects = rs.AllObjects() or []
    curves = [obj for obj in all_objects if rs.IsCurve(obj)]
    log("Found curves: {}".format(len(curves)))
    for index, curve in enumerate(curves, 1):
        bbox = rs.BoundingBox(curve)
        z_values = [point.Z for point in bbox] if bbox else []
        log(
            "Curve {}: layer={}, closed={}, planar={}, z_min={}, z_max={}".format(
                index,
                rs.ObjectLayer(curve),
                rs.IsCurveClosed(curve),
                rs.IsCurvePlanar(curve),
                min(z_values) if z_values else None,
                max(z_values) if z_values else None,
            )
        )
    return curves


def get_bounds(objects):
    points = []
    for obj in objects:
        bbox = rs.BoundingBox(obj)
        if bbox:
            points.extend(bbox)
    if not points:
        return None
    return {
        "min_x": min(point.X for point in points),
        "max_x": max(point.X for point in points),
        "min_y": min(point.Y for point in points),
        "max_y": max(point.Y for point in points),
    }


def create_box_stock_from_curves(curves):
    bounds = get_bounds(curves)
    if not bounds:
        log("ERROR: cannot calculate stock bounds from curves.")
        return False

    min_x = bounds["min_x"] - Config.STOCK_XY_OFFSET
    max_x = bounds["max_x"] + Config.STOCK_XY_OFFSET
    min_y = bounds["min_y"] - Config.STOCK_XY_OFFSET
    max_y = bounds["max_y"] + Config.STOCK_XY_OFFSET
    bottom_z = Config.CUT_TOP_Z - Config.CUT_DEPTH

    StockManager.DeleteStock()
    ok = StockManager.CreateBoxStock(
        min_x,
        min_y,
        bottom_z,
        0,
        Config.CUT_DEPTH,
        max_y - min_y,
        max_x - min_x,
        False,
    )
    log("CreateBoxStock ok={}, expected stock Z={}..{}".format(ok, bottom_z, Config.CUT_TOP_Z))
    return ok


def create_flat_tool_d3():
    tool = ToolManager.CreateMillTool(MillToolType.MTOOL_FLAT)
    if not tool:
        log("ERROR: failed to create flat mill tool.")
        return None
    tool.SetDia(Config.TOOL_DIAMETER)
    tool.SetName("Flat mill D{} outside".format(Config.TOOL_DIAMETER))
    tool.SetFluteLen(Config.TOOL_FLUTE_LENGTH)
    tool.SetLen(Config.TOOL_LENGTH)
    tool.SetShankDia(Config.TOOL_DIAMETER)
    ToolManager.SetActiveTool(tool)
    log("Tool created: Flat mill D3.")
    return tool


def select_curves(curves):
    rs.UnselectAllObjects()
    for obj in curves:
        rs.SelectObject(obj)
    MecSoftCAM.API.SyncDatabase()
    log("Selected curves synced with RhinoCAM database.")


def apply_depth_params(mop):
    set_param("SetCutGeomLocation(raw TOP=0)", mop.SetCutGeomLocation, Config.CUT_GEOM_LOCATION_TOP)
    set_param("SetTopZ", mop.SetTopZ, Config.CUT_TOP_Z)
    set_param("SetTotalCutDepth", mop.SetTotalCutDepth, Config.CUT_DEPTH)
    set_param("SetRoughCutDepth", mop.SetRoughCutDepth, Config.CUT_DEPTH)
    set_param("SetFinishDepth", mop.SetFinishDepth, 0.0)
    set_param("SetRoughCutDepthPerCut", mop.SetRoughCutDepthPerCut, Config.STEP_DOWN)
    set_param("SetFinishDepthPerCut", mop.SetFinishDepthPerCut, 0.0)


def apply_cut_side_params(mop):
    set_param("SetUse3DModelForDepthDetection", mop.SetUse3DModelForDepthDetection, False)
    set_param("SetCutSideDetermineByModel", mop.SetCutSideDetermineByModel, False)
    set_param("SetCutSide", mop.SetCutSide, ContourCutSideType.CONTOUR_RIGHT)
    set_param("SetCutDir", mop.SetCutDir, ContourCutDirection.CONTOUR_CLIMB)


def apply_clearance_params(mop):
    set_param("SetClearanceType", mop.SetClearanceType, ContourClearanceType.CONTOUR_CLEARANCE_ABSOLUTE)
    set_param("SetClearanceAbsoluteZ", mop.SetClearanceAbsoluteZ, Config.CLEARANCE_Z)
    set_param(
        "SetClearanceTransferType",
        mop.SetClearanceTransferType,
        ContourClearanceTransferType.CONTOUR_TRANSFER_CLEARANCE,
    )
    set_param("SetMOpEntryTypeParam", mop.SetMOpEntryTypeParam, ContourEntryType.CONTOUR_ENTRY_NONE)
    set_param("SetMOpExitTypeParam", mop.SetMOpExitTypeParam, ContourExitType.CONTOUR_EXIT_NONE)
    set_param("SetRetractTypeParam", mop.SetRetractTypeParam, ContourEngRetType.CONTOUR_ENGRET_VERTICAL)
    set_param("SetRetractDistance", mop.SetRetractDistance, Config.RETRACT_DISTANCE)


def apply_feed_params(mop):
    mop.SetPlungeFeedParam(Config.PLUNGE_FEED)
    mop.SetApproachFeedParam(Config.APPROACH_FEED)
    mop.SetEngageFeedParam(Config.ENGAGE_FEED)
    mop.SetCutFeedParam(Config.CUT_FEED)
    mop.SetRetractFeedParam(Config.RETRACT_FEED)
    mop.SetDepartureFeedParam(Config.DEPARTURE_FEED)


def add_selected_geometry(mop):
    added = mop.AddSelectedGeometryToMOp()
    if not added:
        added = SelectionManager.PopulateMOpWithSelectedGeometry(mop)
    log("Geometry added to MOp: {}".format(added))
    return added


def create_profiling_mop(curves, tool):
    select_curves(curves)
    mop = MOpManager.Create2AProfilingMOp()
    if not mop:
        log("ERROR: failed to create 2 Axis Profiling MOp.")
        return None

    layer_name = get_layer_name(curves)
    set_param("SetName", mop.SetName, layer_name)
    mop.Tool = tool
    set_param("SetTolerance", mop.SetTolerance, Config.TOLERANCE)
    apply_depth_params(mop)
    apply_cut_side_params(mop)

    if not add_selected_geometry(mop):
        return None

    MecSoftCAM.API.SyncDatabase()
    apply_depth_params(mop)
    apply_cut_side_params(mop)
    set_param("SetName after geometry", mop.SetName, layer_name)
    apply_clearance_params(mop)
    apply_feed_params(mop)

    log(
        "Before regenerate: Name={}, TopZ={}, TotalDepth={}, RoughStep={}".format(
            mop.GetName(),
            mop.GetTopZ(),
            mop.GetTotalCutDepth(),
            mop.GetRoughCutDepthPerCut(),
        )
    )
    if not MOpManager.RegenerateMOp(mop):
        log("ERROR: toolpath regeneration failed.")
        return None
    log("Outside profiling MOp created and regenerated.")
    return mop


def detect_created_file(output_dir, before_files):
    after_files = set(os.listdir(output_dir))
    created = sorted(after_files - before_files)
    if not created:
        return None
    return os.path.join(output_dir, created[-1])


def rename_gcode_file(source_path, layer_name):
    if not source_path:
        log("No new file detected in output dir.")
        return None

    output_dir = os.path.dirname(source_path)
    source_name = os.path.basename(source_path)
    _, extension = os.path.splitext(source_name)
    if not extension:
        extension = ".nc"

    target_name = clean_filename(layer_name) + extension
    target_path = os.path.join(output_dir, target_name)
    if os.path.abspath(source_path) != os.path.abspath(target_path):
        if os.path.exists(target_path):
            os.remove(target_path)
        os.rename(source_path, target_path)

    log("G-code file: {}".format(target_path))
    return target_path


def post_process_mop(mop, layer_name):
    output_dir = get_gcode_dir()

    active_post = MOpManager.GetPostProcessor()
    log("Active postprocessor: {}".format(active_post))
    log("G-code output dir: {}".format(output_dir))

    before_files = set(os.listdir(output_dir))
    ok = MOpManager.PostProcessMOp(output_dir + os.sep, mop)
    log("PostProcessMOp ok={}".format(ok))
    if not ok:
        return None

    created_file = detect_created_file(output_dir, before_files)
    return rename_gcode_file(created_file, layer_name)


def main():
    MecSoftCAM.API.Initialize()
    try:
        MecSoftCAM.API.SetActiveModule(ModuleType.MILL)
        curves = get_all_curves()
        if not curves:
            log("DONE: no curves to process.")
            return

        layer_name = get_layer_name(curves)
        log("Layer name for MOp and G-code: {}".format(layer_name))

        tool = create_flat_tool_d3()
        if not tool:
            return

        if create_box_stock_from_curves(curves):
            log("Stock created from explicit curve box.")
        else:
            log("WARNING: explicit box stock was not created.")

        mop = create_profiling_mop(curves, tool)
        if mop:
            post_process_mop(mop, layer_name)
            log("DONE: test script finished successfully.")
        else:
            log("DONE: test script finished with errors.")
    finally:
        MecSoftCAM.API.Uninitialize()
        log("API uninitialized.")


main()

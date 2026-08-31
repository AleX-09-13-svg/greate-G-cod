#! python3
from mecsoftcamapi import *
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


TOOL_DIAMETER = 3.0
CUT_TOP_Z = 0.0
CUT_DEPTH = 16.0
STEP_DOWN = 4.0
STOCK_XY_OFFSET = 1.0
CUT_GEOM_LOCATION_TOP = 0


def log(message):
    print("[RhinoCAM stock probe 7] " + message)


def set_param(name, setter, value):
    try:
        ok = setter(value)
    except Exception as ex:
        log("ERROR: {} raised {}".format(name, ex))
        return False

    if not ok:
        log("WARNING: {} was not accepted: {}".format(name, value))
    return ok


def get_mop_name_from_layer(curves):
    if not curves:
        return "Profiling"

    layer_name = rs.ObjectLayer(curves[0])
    if not layer_name:
        return "Profiling"

    return "Profiling - {}".format(layer_name)


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

    min_x = bounds["min_x"] - STOCK_XY_OFFSET
    max_x = bounds["max_x"] + STOCK_XY_OFFSET
    min_y = bounds["min_y"] - STOCK_XY_OFFSET
    max_y = bounds["max_y"] + STOCK_XY_OFFSET
    bottom_z = CUT_TOP_Z - CUT_DEPTH

    StockManager.DeleteStock()
    ok = StockManager.CreateBoxStock(
        min_x,
        min_y,
        bottom_z,
        0,
        CUT_DEPTH,
        max_y - min_y,
        max_x - min_x,
        False,
    )
    log("CreateBoxStock ok={}, expected stock Z={}..{}".format(ok, bottom_z, CUT_TOP_Z))
    return ok


def create_flat_tool_d3():
    tool = ToolManager.CreateMillTool(MillToolType.MTOOL_FLAT)
    if not tool:
        log("ERROR: failed to create flat mill tool.")
        return None

    tool.SetDia(TOOL_DIAMETER)
    tool.SetName("Flat mill D3 outside probe 7")
    tool.SetFluteLen(9.0)
    tool.SetLen(24.0)
    tool.SetShankDia(TOOL_DIAMETER)
    ToolManager.SetActiveTool(tool)
    log("Tool created: Flat mill D3.")
    return tool


def select_curves(curves):
    rs.UnselectAllObjects()
    for obj in curves:
        rs.SelectObject(obj)
    MecSoftCAM.API.SyncDatabase()
    log("Selected curves synced with RhinoCAM database.")


def apply_cut_params(mop, label):
    log("Applying cut params: {}".format(label))
    set_param("SetCutGeomLocation(raw TOP=0)", mop.SetCutGeomLocation, CUT_GEOM_LOCATION_TOP)
    set_param("SetTopZ", mop.SetTopZ, CUT_TOP_Z)
    set_param("SetTotalCutDepth", mop.SetTotalCutDepth, CUT_DEPTH)
    set_param("SetRoughCutDepth", mop.SetRoughCutDepth, CUT_DEPTH)
    set_param("SetFinishDepth", mop.SetFinishDepth, 0.0)
    set_param("SetRoughCutDepthPerCut", mop.SetRoughCutDepthPerCut, STEP_DOWN)
    set_param("SetFinishDepthPerCut", mop.SetFinishDepthPerCut, 0.0)
    set_param("SetUse3DModelForDepthDetection", mop.SetUse3DModelForDepthDetection, False)
    set_param("SetCutSideDetermineByModel", mop.SetCutSideDetermineByModel, False)
    set_param("SetCutSide", mop.SetCutSide, ContourCutSideType.CONTOUR_RIGHT)
    set_param("SetCutDir", mop.SetCutDir, ContourCutDirection.CONTOUR_CLIMB)


def create_profiling_mop(curves, tool):
    select_curves(curves)

    mop = MOpManager.Create2AProfilingMOp()
    if not mop:
        log("ERROR: failed to create 2 Axis Profiling MOp.")
        return None

    mop_name = get_mop_name_from_layer(curves)
    set_param("SetName", mop.SetName, mop_name)
    log("MOp name requested: {}".format(mop_name))

    mop.Tool = tool
    set_param("SetTolerance", mop.SetTolerance, 0.01)
    apply_cut_params(mop, "before geometry")

    added = mop.AddSelectedGeometryToMOp()
    if not added:
        added = SelectionManager.PopulateMOpWithSelectedGeometry(mop)
    log("Geometry added to MOp: {}".format(added))
    if not added:
        log("ERROR: selected geometry was not added to MOp.")
        return None

    MecSoftCAM.API.SyncDatabase()
    apply_cut_params(mop, "after geometry")

    set_param("SetName after geometry", mop.SetName, mop_name)
    set_param("SetClearanceType", mop.SetClearanceType, ContourClearanceType.CONTOUR_CLEARANCE_ABSOLUTE)
    set_param("SetClearanceAbsoluteZ", mop.SetClearanceAbsoluteZ, 5.0)
    set_param(
        "SetClearanceTransferType",
        mop.SetClearanceTransferType,
        ContourClearanceTransferType.CONTOUR_TRANSFER_CLEARANCE,
    )
    set_param("SetMOpEntryTypeParam", mop.SetMOpEntryTypeParam, ContourEntryType.CONTOUR_ENTRY_NONE)
    set_param("SetMOpExitTypeParam", mop.SetMOpExitTypeParam, ContourExitType.CONTOUR_EXIT_NONE)
    set_param("SetRetractTypeParam", mop.SetRetractTypeParam, ContourEngRetType.CONTOUR_ENGRET_VERTICAL)
    set_param("SetRetractDistance", mop.SetRetractDistance, 1.0)

    mop.SetPlungeFeedParam(300.0)
    mop.SetApproachFeedParam(400.0)
    mop.SetEngageFeedParam(400.0)
    mop.SetCutFeedParam(800.0)
    mop.SetRetractFeedParam(1000.0)
    mop.SetDepartureFeedParam(1000.0)

    log(
        "Before regenerate: Name={}, CutGeomLocation={}, CutSide={}, TopZ={}, TotalDepth={}, RoughDepth={}, FinishDepth={}, RoughStep={}, FinishStep={}".format(
            mop.GetName(),
            mop.GetCutGeomLocation(),
            mop.GetCutSide(),
            mop.GetTopZ(),
            mop.GetTotalCutDepth(),
            mop.GetRoughCutDepth(),
            mop.GetFinishDepth(),
            mop.GetRoughCutDepthPerCut(),
            mop.GetFinishDepthPerCut(),
        )
    )

    if not MOpManager.RegenerateMOp(mop):
        log("ERROR: toolpath regeneration failed.")
        return None

    log("Outside profiling MOp created and regenerated.")
    return mop


def main():
    MecSoftCAM.API.Initialize()
    try:
        MecSoftCAM.API.SetActiveModule(ModuleType.MILL)

        curves = get_all_curves()
        if not curves:
            log("DONE: no curves to process.")
            return

        tool = create_flat_tool_d3()
        if not tool:
            return

        if create_box_stock_from_curves(curves):
            log("Stock created from explicit curve box.")
        else:
            log("WARNING: explicit box stock was not created.")

        mop = create_profiling_mop(curves, tool)
        if mop:
            log("DONE: test script finished successfully.")
        else:
            log("DONE: test script finished with errors.")
    finally:
        MecSoftCAM.API.Uninitialize()
        log("API uninitialized.")


main()

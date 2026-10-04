from mecsoftcamapi import *

from MecSoftCAM.Managers import MOpManager
from MecSoftCAM.Managers import SelectionManager
from MecSoftCAM.Types import ContourClearanceTransferType
from MecSoftCAM.Types import ContourClearanceType
from MecSoftCAM.Types import ContourCutDirection
from MecSoftCAM.Types import ContourCutSideType
from MecSoftCAM.Types import ContourEngRetType
from MecSoftCAM.Types import ContourEntryType
from MecSoftCAM.Types import ContourExitType
from MecSoftCAM.Types import ContourStartPointType
from MecSoftCAM.Types import ContourStepType
from MecSoftCAM.Types import CornerCleanupType
from MecSoftCAM.Types import CutType
from MecSoftCAM.Types import PocketOffsetType
from MecSoftCAM.Types import TraversalCutType


class ProfilingConfig(object):
    CUT_GEOM_LOCATION_TOP = 0

    def __init__(self):
        self.top_z = 0.0
        self.depth = 16.0
        self.step_down = 4.0
        self.tolerance = 0.01
        self.clearance_z = 5.0
        self.retract_distance = 1.0
        self.plunge_feed = 300.0
        self.approach_feed = 400.0
        self.engage_feed = 400.0
        self.cut_feed = 800.0
        self.retract_feed = 1000.0
        self.departure_feed = 1000.0
        self.stock_allowance = 0.0
        self.spindle_rpm = 18000.0
        self.cut_direction = "climb"
        self.cut_angle = None
        self.stepover_angle = None
        self.stepover_distance = None
        self.start_point = None
        self.cleanup_pass = None
        self.corner_cleanup = None
        self.pocket_offset_type = None
        self.force_parallel_pocket = False


def set_param(log, name, setter, value):
    try:
        ok = setter(value)
    except Exception as ex:
        log("ERROR: {} raised {}".format(name, ex))
        return False
    if not ok:
        log("WARNING: {} was not accepted: {}".format(name, value))
    return ok


def set_optional_param(log, target, method_names, value):
    for method_name in method_names:
        setter = getattr(target, method_name, None)
        if setter:
            return set_param(log, method_name, setter, value)
    log("WARNING: none of optional methods found: {}".format(", ".join(method_names)))
    return False


def apply_depth_params(log, mop, config):
    set_param(log, "SetCutGeomLocation(raw TOP=0)", mop.SetCutGeomLocation, config.CUT_GEOM_LOCATION_TOP)
    set_param(log, "SetTopZ", mop.SetTopZ, config.top_z)
    set_param(log, "SetTotalCutDepth", mop.SetTotalCutDepth, config.depth)
    set_param(log, "SetRoughCutDepth", mop.SetRoughCutDepth, config.depth)
    set_param(log, "SetFinishDepth", mop.SetFinishDepth, 0.0)
    set_param(log, "SetRoughCutDepthPerCut", mop.SetRoughCutDepthPerCut, config.step_down)
    set_param(log, "SetFinishDepthPerCut", mop.SetFinishDepthPerCut, 0.0)


def apply_cut_side_params(log, mop):
    apply_profiling_cut_side_params(log, mop, ContourCutSideType.CONTOUR_RIGHT)


def cut_direction_value(cut_direction):
    normalized = (cut_direction or "climb").lower()
    if normalized in ("mixed", "both", "climbconventional", "climb_conventional"):
        return getattr(
            ContourCutDirection,
            "CONTOUR_CLIMBCONVENTIONAL",
            ContourCutDirection.CONTOUR_CLIMB,
        )
    if normalized in ("conventional", "against", "upcut"):
        return getattr(
            ContourCutDirection,
            "CONTOUR_CONVENTIONAL",
            ContourCutDirection.CONTOUR_CLIMB,
        )
    return ContourCutDirection.CONTOUR_CLIMB


def apply_profiling_cut_side_params(log, mop, cut_side, cut_direction="climb"):
    set_param(log, "SetUse3DModelForDepthDetection", mop.SetUse3DModelForDepthDetection, False)
    set_param(log, "SetCutSideDetermineByModel", mop.SetCutSideDetermineByModel, False)
    set_param(log, "SetCutSide", mop.SetCutSide, cut_side)
    set_param(log, "SetCutDir", mop.SetCutDir, cut_direction_value(cut_direction))


def apply_clearance_params(log, mop, config):
    set_param(log, "SetClearanceType", mop.SetClearanceType, ContourClearanceType.CONTOUR_CLEARANCE_ABSOLUTE)
    set_param(log, "SetClearanceAbsoluteZ", mop.SetClearanceAbsoluteZ, config.clearance_z)
    set_param(
        log,
        "SetClearanceTransferType",
        mop.SetClearanceTransferType,
        ContourClearanceTransferType.CONTOUR_TRANSFER_CLEARANCE,
    )
    set_param(log, "SetMOpEntryTypeParam", mop.SetMOpEntryTypeParam, ContourEntryType.CONTOUR_ENTRY_NONE)
    set_param(log, "SetMOpExitTypeParam", mop.SetMOpExitTypeParam, ContourExitType.CONTOUR_EXIT_NONE)
    set_param(log, "SetRetractTypeParam", mop.SetRetractTypeParam, ContourEngRetType.CONTOUR_ENGRET_VERTICAL)
    set_param(log, "SetRetractDistance", mop.SetRetractDistance, config.retract_distance)


def apply_feed_params(mop, config):
    mop.SetPlungeFeedParam(config.plunge_feed)
    mop.SetApproachFeedParam(config.approach_feed)
    mop.SetEngageFeedParam(config.engage_feed)
    mop.SetCutFeedParam(config.cut_feed)
    mop.SetRetractFeedParam(config.retract_feed)
    mop.SetDepartureFeedParam(config.departure_feed)


def apply_stock_allowance_params(log, mop, config):
    method_names = [
        "SetStock",
        "SetStockParam",
        "SetStockAllowance",
        "SetStockAllowanceParam",
        "SetStockToLeave",
        "SetStockToLeaveParam",
        "SetXYStock",
        "SetXYStockParam",
        "SetXYStockAllowance",
        "SetXYStockAllowanceParam",
        "SetPartStock",
        "SetPartStockParam",
        "SetCutStock",
        "SetCutStockParam",
        "SetOffsetStock",
        "SetOffsetStockParam",
        "SetRegionStock",
        "SetRegionStockParam",
        "SetGlobalStock",
        "SetGlobalStockParam",
        "SetMOpStock",
        "SetMOpStockParam",
    ]
    for method_name in method_names:
        setter = getattr(mop, method_name, None)
        if not setter:
            continue

        try:
            ok = setter(config.stock_allowance)
        except Exception as ex:
            log("ERROR: {} raised {}".format(method_name, ex))
            continue

        if ok is not False:
            log("{} set to {}".format(method_name, config.stock_allowance))
            return True
        log("WARNING: {} was not accepted: {}".format(method_name, config.stock_allowance))

    property_names = [
        "Stock",
        "StockParam",
        "StockAllowance",
        "StockToLeave",
        "XYStock",
        "XYStockAllowance",
        "PartStock",
        "CutStock",
        "OffsetStock",
        "RegionStock",
        "GlobalStock",
    ]
    for property_name in property_names:
        if not hasattr(mop, property_name):
            continue
        try:
            setattr(mop, property_name, config.stock_allowance)
        except Exception as ex:
            log("ERROR: {} property raised {}".format(property_name, ex))
            continue
        log("{} property set to {}".format(property_name, config.stock_allowance))
        return True

    log(
        "WARNING: stock allowance was not set. Matching methods: {}".format(
            ", ".join(available_method_names(mop, ["stock", "allowance"]))
            or "none"
        )
    )
    return False


def apply_spindle_params(log, mop, config):
    return set_optional_param(
        log,
        mop,
        [
            "SetSpindleSpeedParam",
            "SetSpindleSpeed",
            "SetSpindleRPM",
            "SetRPM",
            "SetSpeed",
        ],
        config.spindle_rpm,
    )


def add_selected_geometry(log, mop):
    added = mop.AddSelectedGeometryToMOp()
    if not added:
        added = SelectionManager.PopulateMOpWithSelectedGeometry(mop)
    log("Geometry added to MOp: {}".format(added))
    return added


def create_mop_from_candidates(log, method_names):
    for method_name in method_names:
        factory = getattr(MOpManager, method_name, None)
        if not factory:
            continue

        mop = factory()
        if mop:
            log("Created MOp using {}".format(method_name))
            return mop

    log("WARNING: none of MOp factories worked: {}".format(", ".join(method_names)))
    return None


def apply_drill_params(log, mop, config):
    set_optional_param(log, mop, ["SetTopZ", "SetCutStartZ"], config.top_z)
    set_optional_param(
        log,
        mop,
        ["SetCutDepth", "SetDrillDepth", "SetTotalCutDepth", "SetDepth"],
        config.depth,
    )
    set_optional_param(
        log,
        mop,
        ["SetClearanceAbsoluteZ", "SetClearanceZ", "SetClearancePlaneZ"],
        config.clearance_z,
    )
    set_optional_param(log, mop, ["SetRetractDistance", "SetRetractZ"], config.retract_distance)
    set_optional_param(log, mop, ["SetPlungeFeedParam", "SetCutFeedParam"], config.plunge_feed)
    apply_spindle_params(log, mop, config)


def apply_pocket_params(log, mop, config):
    set_optional_param(log, mop, ["SetTolerance"], config.tolerance)
    set_optional_param(log, mop, ["SetCutGeomLocation"], config.CUT_GEOM_LOCATION_TOP)
    set_optional_param(log, mop, ["SetTopZ", "SetCutStartZ"], config.top_z)
    set_optional_param(
        log,
        mop,
        ["SetTotalCutDepth", "SetCutDepth", "SetPocketDepth", "SetDepth"],
        config.depth,
    )
    set_optional_param(log, mop, ["SetRoughCutDepth"], config.depth)
    set_optional_param(log, mop, ["SetFinishDepth"], 0.0)
    set_optional_param(log, mop, ["SetRoughCutDepthPerCut", "SetStepDown"], config.step_down)
    set_optional_param(log, mop, ["SetFinishDepthPerCut"], 0.0)
    set_optional_param(
        log,
        mop,
        ["SetClearanceAbsoluteZ", "SetClearanceZ", "SetClearancePlaneZ"],
        config.clearance_z,
    )
    set_optional_param(log, mop, ["SetRetractDistance", "SetRetractZ"], config.retract_distance)
    set_optional_param(log, mop, ["SetPlungeFeedParam"], config.plunge_feed)
    set_optional_param(log, mop, ["SetApproachFeedParam"], config.approach_feed)
    set_optional_param(log, mop, ["SetEngageFeedParam"], config.engage_feed)
    set_optional_param(log, mop, ["SetCutFeedParam"], config.cut_feed)
    set_optional_param(log, mop, ["SetRetractFeedParam"], config.retract_feed)
    set_optional_param(log, mop, ["SetDepartureFeedParam"], config.departure_feed)
    set_optional_param(
        log,
        mop,
        ["SetCutDir", "SetCutDirection"],
        cut_direction_value(config.cut_direction),
    )
    if config.force_parallel_pocket:
        apply_parallel_pocket_params(log, mop)
    if config.cut_angle is not None:
        set_optional_param(
            log,
            mop,
            [
                "SetCutAngle",
                "SetCutPatternAngle",
                "SetPocketCutAngle",
                "SetRasterAngle",
                "SetParallelCutAngle",
            ],
            config.cut_angle,
        )
    if config.stepover_angle is not None:
        set_optional_param(
            log,
            mop,
            [
                "SetStepOverAngle",
                "SetStepoverAngle",
                "SetLaceAngle",
                "SetScanAngle",
                "SetPathSpacingAngle",
                "SetPocketStepOverAngle",
                "SetPocketStepoverAngle",
                "SetPocketLaceAngle",
                "SetPocketScanAngle",
            ],
            config.stepover_angle,
        )
    if config.stepover_distance is not None:
        set_first_optional_value(
            log,
            mop,
            ["SetStepoverType"],
            enum_or_values(
                ContourStepType,
                ["STEPDIST", "CONTOUR_STEPDIST"],
                [1, 0, 2],
            ),
        )
        set_optional_param(
            log,
            mop,
            [
                "SetStepDistance",
                "SetStepoverDistance",
                "SetStepOverDistance",
                "SetPocketStepDistance",
                "SetPocketStepoverDistance",
            ],
            config.stepover_distance,
        )
    if config.start_point == "bottom":
        set_optional_param(
            log,
            mop,
            ["SetStartPoint", "SetStartPointParam", "SetMOpStartPointParam"],
            ContourStartPointType.CONTOUR_START_BOTTOM,
        )
    if config.cleanup_pass is not None:
        set_optional_param(
            log,
            mop,
            ["SetMOpCleanupPassParam", "SetCleanupPass", "SetCleanupPassParam"],
            config.cleanup_pass,
        )
    if config.corner_cleanup == "none":
        set_optional_param(
            log,
            mop,
            ["SetMOpCornerCleanupParam", "SetCornerCleanup", "SetCornerCleanupParam"],
            CornerCleanupType.CLEANUP_NONE,
        )
    if config.pocket_offset_type == "inside":
        set_optional_param(
            log,
            mop,
            ["SetPocketOffsetType"],
            PocketOffsetType.CONTOUR_START_INSIDE,
        )
    elif config.pocket_offset_type == "outside":
        set_optional_param(
            log,
            mop,
            ["SetPocketOffsetType"],
            PocketOffsetType.CONTOUR_START_OUTSIDE,
        )
    apply_stock_allowance_params(log, mop, config)
    apply_spindle_params(log, mop, config)


def available_method_names(target, patterns):
    names = []
    for name in dir(target):
        lower_name = name.lower()
        if any(pattern in lower_name for pattern in patterns):
            names.append(name)
    return sorted(names)


def set_first_optional_value(log, target, method_names, values):
    for method_name in method_names:
        setter = getattr(target, method_name, None)
        if not setter:
            continue

        for value in values:
            try:
                ok = setter(value)
            except Exception:
                continue
            if ok is not False:
                log("{} accepted value {}".format(method_name, value))
                return True

    return False


def enum_or_values(enum_type, names, fallback_values):
    values = []
    for name in names:
        value = getattr(enum_type, name, None)
        if value is not None:
            values.append(value)
    values.extend(fallback_values)
    return values


def apply_parallel_pocket_params(log, mop):
    applied = False

    if set_first_optional_value(
        log,
        mop,
        ["SetMOpCutTypeParam"],
        enum_or_values(
            CutType,
            ["CONTOUR_LINEAR", "CUTTYPE_LINEAR", "LINEAR"],
            [1, 0, 2],
        ),
    ):
        applied = True

    if set_first_optional_value(
        log,
        mop,
        ["SetTraversalCutType"],
        enum_or_values(
            TraversalCutType,
            ["ZIGZAG", "ZIG"],
            [0, 1],
        ),
    ):
        applied = True

    if set_first_optional_value(
        log,
        mop,
        ["SetStepoverType"],
        enum_or_values(
            ContourStepType,
            ["STEPDIST", "CONTOUR_STEPDIST"],
            [1, 0, 2],
        ),
    ):
        applied = True

    if applied:
        return True

    if set_first_optional_value(
        log,
        mop,
        [
            "SetCutPattern",
            "SetCutPatternType",
            "SetPocketCutPattern",
            "SetPocketCutPatternType",
            "SetMachiningPattern",
            "SetMachiningPatternType",
            "SetCutMethod",
            "SetPocketCutMethod",
            "SetPocketingMethod",
            "SetPocketingType",
            "SetToolpathPattern",
            "SetToolpathPatternType",
        ],
        [
            "parallel",
            "Parallel",
            "PARALLEL",
            "linear",
            "Linear",
            "LINEAR",
            "raster",
            "Raster",
            "RASTER",
            1,
            2,
            3,
        ],
    ):
        return True

    log(
        "WARNING: parallel pocket pattern was not accepted. Matching methods: {}".format(
            ", ".join(
                available_method_names(
                    mop,
                    ["pattern", "pocket", "raster", "parallel", "method", "type"],
                )
            )
            or "none"
        )
    )
    return False


def create_drilling(log, sync_database, mop_name, tool, config):
    mop = MOpManager.CreateDrillMOp()
    if not mop:
        log("ERROR: failed to create Drill MOp.")
        return None

    set_param(log, "SetName", mop.SetName, mop_name)
    mop.Tool = tool
    apply_drill_params(log, mop, config)

    if not add_selected_geometry(log, mop):
        return None

    sync_database()
    apply_drill_params(log, mop, config)
    set_param(log, "SetName after geometry", mop.SetName, mop_name)

    if not MOpManager.RegenerateMOp(mop):
        log("ERROR: drill toolpath regeneration failed.")
        return None

    log("Drill MOp created and regenerated.")
    return mop


def create_outside_profiling(log, sync_database, mop_name, tool, config):
    return create_profiling(log, sync_database, mop_name, tool, config, ContourCutSideType.CONTOUR_RIGHT)


def create_inside_profiling(log, sync_database, mop_name, tool, config):
    return create_profiling(log, sync_database, mop_name, tool, config, ContourCutSideType.CONTOUR_LEFT)


def create_pocket_profiling(log, sync_database, mop_name, tool, config):
    mop = create_mop_from_candidates(
        log,
        [
            "Create2APocketingMOp",
            "Create2AxPocketingMOp",
            "Create2_5AxPocketingMOp",
        ],
    )
    if not mop:
        log("Pocketing MOp is unavailable; using inside profiling fallback.")
        return create_inside_profiling(log, sync_database, mop_name, tool, config)

    set_param(log, "SetName", mop.SetName, mop_name)
    mop.Tool = tool
    apply_pocket_params(log, mop, config)

    if not add_selected_geometry(log, mop):
        return None

    sync_database()
    apply_pocket_params(log, mop, config)
    set_param(log, "SetName after geometry", mop.SetName, mop_name)

    if not MOpManager.RegenerateMOp(mop):
        log("ERROR: pocket toolpath regeneration failed.")
        return None

    log("Pocket MOp created and regenerated.")
    return mop


def create_2_5_pocketing(log, sync_database, mop_name, tool, config):
    mop = create_mop_from_candidates(
        log,
        [
            "Create2AxPocketingMOp",
        ],
    )
    if not mop:
        log("ERROR: 2 Axis Pocketing MOp is unavailable.")
        return None

    set_param(log, "SetName", mop.SetName, mop_name)
    mop.Tool = tool
    apply_pocket_params(log, mop, config)

    if not add_selected_geometry(log, mop):
        return None

    sync_database()
    apply_pocket_params(log, mop, config)
    set_param(log, "SetName after geometry", mop.SetName, mop_name)

    if not MOpManager.RegenerateMOp(mop):
        log("ERROR: 2 Axis Pocketing toolpath regeneration failed.")
        return None

    log("2 Axis Pocketing MOp created and regenerated.")
    return mop


def create_profiling(log, sync_database, mop_name, tool, config, cut_side):
    mop = MOpManager.Create2AProfilingMOp()
    if not mop:
        log("ERROR: failed to create 2 Axis Profiling MOp.")
        return None

    set_param(log, "SetName", mop.SetName, mop_name)
    mop.Tool = tool
    set_param(log, "SetTolerance", mop.SetTolerance, config.tolerance)
    apply_depth_params(log, mop, config)
    apply_profiling_cut_side_params(log, mop, cut_side, config.cut_direction)

    if not add_selected_geometry(log, mop):
        return None

    sync_database()
    apply_depth_params(log, mop, config)
    apply_profiling_cut_side_params(log, mop, cut_side, config.cut_direction)
    apply_clearance_params(log, mop, config)
    apply_feed_params(mop, config)
    apply_stock_allowance_params(log, mop, config)
    apply_spindle_params(log, mop, config)
    set_param(log, "SetName after geometry", mop.SetName, mop_name)

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

    log("Profiling MOp created and regenerated.")
    return mop

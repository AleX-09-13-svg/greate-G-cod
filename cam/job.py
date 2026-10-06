# -*- coding: utf-8 -*-
import importlib
import importlib.util
import os

from cam import config as cam_config
from cam import classification as cam_classification
from cam import operations as cam_operations
from core import layers as core_layers
from core.logging_utils import FileLogger
from geometry import curves as curve_utils
from plugins import rhino8
from plugins import rhinocam


try:
    reload_module = importlib.reload
except AttributeError:
    from imp import reload as reload_module

try:
    importlib.invalidate_caches()
except AttributeError:
    pass

reload_module(rhino8)
reload_module(rhinocam)
core_layers = reload_module(core_layers)
cam_config = reload_module(cam_config)
cam_classification = reload_module(cam_classification)
cam_operations = reload_module(cam_operations)

classify_curves = cam_classification.classify_curves
curves_by_layer = cam_classification.curves_by_layer
is_cam_curve = cam_classification.is_cam_curve
long_side_angle_degrees = cam_classification.long_side_angle_degrees
ordered_layer_names = core_layers.ordered_layer_names
setup_creation_layer_names = core_layers.setup_creation_layer_names
ProfilingConfig = cam_operations.ProfilingConfig
create_drilling = cam_operations.create_drilling
create_2_5_pocketing = cam_operations.create_2_5_pocketing
create_inside_profiling = cam_operations.create_inside_profiling
create_outside_profiling = cam_operations.create_outside_profiling
create_pocket_profiling = cam_operations.create_pocket_profiling


class RhinoCamJob(object):
    def __init__(self, project_root, save_gcode=False, output_dir=None):
        self.project_root = project_root
        self.save_gcode = save_gcode
        self.output_dir = output_dir
        self.tool_file = cam_config.mill_tool_file(project_root)
        self.logger = FileLogger(
            "[RhinoCAM main] ",
            os.path.join(project_root, "rhinocam_main.log"),
        )

    def log(self, message):
        self.logger.log(message)

    def load_save_module(self):
        module_path = os.path.join(self.project_root, "04_save_G_cod.py")
        spec = importlib.util.spec_from_file_location("save_g_code", module_path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module

    def reset_log(self):
        self.logger.reset()

    def copy_config(self, base_config):
        config = ProfilingConfig()
        config.top_z = base_config.top_z
        config.depth = base_config.depth
        config.step_down = base_config.step_down
        config.tolerance = base_config.tolerance
        config.clearance_z = base_config.clearance_z
        config.retract_distance = base_config.retract_distance
        config.plunge_feed = base_config.plunge_feed
        config.approach_feed = base_config.approach_feed
        config.engage_feed = base_config.engage_feed
        config.cut_feed = base_config.cut_feed
        config.retract_feed = base_config.retract_feed
        config.departure_feed = base_config.departure_feed
        config.transfer_feed = base_config.transfer_feed
        config.stock_allowance = base_config.stock_allowance
        config.spindle_rpm = base_config.spindle_rpm
        config.cut_direction = base_config.cut_direction
        config.cut_angle = base_config.cut_angle
        config.stepover_angle = base_config.stepover_angle
        config.stepover_distance = base_config.stepover_distance
        config.start_point = base_config.start_point
        config.cleanup_pass = base_config.cleanup_pass
        config.corner_cleanup = base_config.corner_cleanup
        config.pocket_offset_type = base_config.pocket_offset_type
        config.force_parallel_pocket = base_config.force_parallel_pocket
        return config

    def strategy_config(self, layer_name, base_config, strategy_name):
        settings = cam_config.strategy_settings(strategy_name)
        config = self.copy_config(base_config)
        config.depth = settings["depth"]
        config.step_down = min(settings["step_down"], config.depth)
        config.stock_allowance = cam_config.stock_allowance_for(layer_name, strategy_name)
        config.cut_direction = settings["cut_direction"]
        config.plunge_feed = settings["plunge_feed"]
        config.approach_feed = settings["approach_feed"]
        config.engage_feed = settings["engage_feed"]
        config.cut_feed = settings["cut_feed"]
        config.retract_feed = settings["retract_feed"]
        config.departure_feed = settings["departure_feed"]
        config.transfer_feed = settings["transfer_feed"]
        return config

    def perpendicular_angle(self, angle):
        if angle is None:
            return None
        value = angle + 90.0
        while value >= 180.0:
            value -= 180.0
        return value

    def create_layer_operation(
        self, setup, operation_name, curves, tool, config, operation_factory
    ):
        if not curves:
            return None

        if rhinocam.setup_has_mop(setup, operation_name):
            self.log(
                "MOp {} already exists in setup; skipped duplicate.".format(
                    operation_name
                )
            )
            return "existing"

        def sync_current_setup():
            rhinocam.sync_database()
            rhinocam.activate_setup(setup, sync=False)

        self.log("Creating MOp {}: curves={}".format(operation_name, len(curves)))
        if not rhinocam.activate_setup(setup, sync=False):
            self.log(
                "WARNING: active setup was not changed before {}.".format(
                    operation_name
                )
            )
        rhino8.select_objects(curves)
        rhinocam.sync_database()
        self.log("Selected operation curves synced with RhinoCAM database.")
        if not rhinocam.activate_setup(setup, sync=False):
            self.log(
                "WARNING: active setup was not changed after selection for {}.".format(
                    operation_name
                )
            )
        return operation_factory(
            self.log, sync_current_setup, operation_name, tool, config
        )

    def operation_plan(self, layer_name, strategy_curves, base_config, mill_tool):
        skvosn_curves = (
            strategy_curves["through_holes"] + strategy_curves["hole_marks"]
        )
        operations = [
            (
                "Nacolca_GL_2",
                strategy_curves["hole_marks"],
                self.strategy_config(layer_name, base_config, "nacolka"),
                mill_tool,
                create_drilling,
            ),
            (
                "Skvosn_GL_17_2",
                skvosn_curves,
                self.strategy_config(layer_name, base_config, "skvoznoe"),
                mill_tool,
                create_inside_profiling,
            ),
            (
                "Vyborka_D_35_15_5_GL_13",
                strategy_curves["pockets_35_15_5"],
                self.strategy_config(layer_name, base_config, "vyborka_35_15_5"),
                mill_tool,
                create_pocket_profiling,
            ),
            (
                "Vyborka_D_35_15_5_GL_13_2",
                strategy_curves["pockets_35_15_5"],
                self.strategy_config(layer_name, base_config, "vyborka_35_15_5"),
                mill_tool,
                create_inside_profiling,
            ),
            (
                "Vyborka_D_8_GL_10",
                strategy_curves["pockets_8"],
                self.strategy_config(layer_name, base_config, "vyborka_8"),
                mill_tool,
                create_pocket_profiling,
            ),
            (
                "Vyborka_D_8_GL_10_2",
                strategy_curves["pockets_8"],
                self.strategy_config(layer_name, base_config, "vyborka_8"),
                mill_tool,
                create_inside_profiling,
            ),
        ]

        paz_curves = strategy_curves["paz_dno_zadnst"]
        if paz_curves:
            config = self.strategy_config(layer_name, base_config, "paz_dno_zadnst")
            config.tolerance = 0.1
            config.stock_allowance = 0.0
            config.cut_direction = "mixed"
            config.cut_angle = 90.0
            config.stepover_distance = 3.175
            config.start_point = "bottom"
            config.cleanup_pass = False
            config.corner_cleanup = "none"
            config.pocket_offset_type = "inside"
            config.force_parallel_pocket = True
            operations.append(
                (
                    "Paz_Dno_ZadnSt",
                    paz_curves,
                    config,
                    mill_tool,
                    create_2_5_pocketing,
                )
            )

        operations.append(
            (
                "Kontur",
                strategy_curves["perimeters"],
                self.strategy_config(layer_name, base_config, "raskroy"),
                mill_tool,
                create_outside_profiling,
            )
        )

        return operations

    def log_curve_summary(self, curves):
        for index, curve in enumerate(curves, 1):
            data = curve_utils.describe(curve)
            self.log(
                "Curve {}: layer={}, closed={}, planar={}, z_min={}, z_max={}".format(
                    index,
                    data["layer"],
                    data["closed"],
                    data["planar"],
                    data["z_min"],
                    data["z_max"],
                )
            )

    def has_strategy_curves(self, strategy_curves):
        return any(strategy_curves[name] for name in strategy_curves)

    def run_layer(self, layer_name, curves, base_config, mill_tool, gcode_saver=None):
        strategy_curves, skipped_curves = classify_curves(curves)
        self.log(
            "Layer {} strategies: marks_3={}, holes_4_9={}, pockets_35_15_5={}, pockets_8={}, paz_dno_zadnst={}, perimeters={}, skipped={}".format(
                layer_name,
                len(strategy_curves["hole_marks"]),
                len(strategy_curves["through_holes"]),
                len(strategy_curves["pockets_35_15_5"]),
                len(strategy_curves["pockets_8"]),
                len(strategy_curves["paz_dno_zadnst"]),
                len(strategy_curves["perimeters"]),
                len(skipped_curves),
            )
        )
        if not self.has_strategy_curves(strategy_curves):
            self.log(
                "Layer {} skipped: no matching strategy geometry.".format(layer_name)
            )
            return True

        setup = rhinocam.create_mop_setup(layer_name)
        if not setup:
            self.log("DONE: setup creation failed for layer {}.".format(layer_name))
            return False
        self.log("Setup created and activated: {}".format(layer_name))

        bounds = curve_utils.bounds(curves)
        if bounds and rhinocam.create_box_stock(
            bounds, base_config.top_z, base_config.depth, 1.0
        ):
            self.log("Layer {} stock created from curve box.".format(layer_name))
        else:
            self.log(
                "WARNING: layer {} explicit box stock was not created.".format(
                    layer_name
                )
            )

        created_mops = []
        for (
            operation_name,
            operation_curves,
            operation_config,
            operation_tool,
            operation_factory,
        ) in self.operation_plan(layer_name, strategy_curves, base_config, mill_tool):
            self.log(
                "{}_{} params: allowance={}, step_down={}, cut_dir={}, cut_angle={}, stepover_angle={}, spindle_rpm={}".format(
                    layer_name,
                    operation_name,
                    operation_config.stock_allowance,
                    operation_config.step_down,
                    operation_config.cut_direction,
                    operation_config.cut_angle,
                    operation_config.stepover_angle,
                    operation_config.spindle_rpm,
                )
            )
            mop = self.create_layer_operation(
                setup,
                operation_name,
                operation_curves,
                operation_tool,
                operation_config,
                operation_factory,
            )
            if not mop:
                if operation_curves:
                    self.log(
                        "ERROR: operation {} was not created; skipped.".format(
                            "{}_{}".format(layer_name, operation_name)
                        )
                    )
                continue

            created_mops.append(mop)

        if not created_mops:
            self.log("ERROR: no operations were created for {}.".format(layer_name))
            return False

        self.log("Setup {} operations created.".format(layer_name))
        if gcode_saver:
            if not rhinocam.activate_setup(setup):
                self.log(
                    "WARNING: active setup was not changed before saving {}.".format(
                        layer_name
                    )
                )
            rhinocam.sync_database()
            if not gcode_saver.post_process_setup(setup, layer_name):
                self.log("ERROR: G-code save failed for {}.".format(layer_name))
                return False
        else:
            self.log("G-code not saved by 03main.py.")

        return True

    def run(self):
        self.reset_log()
        self.log("Project root: {}".format(self.project_root))
        self.log("Tool file: {}".format(self.tool_file))
        rhinocam.initialize_mill()
        try:
            all_curves = curve_utils.all_curves()
            all_layers = sorted(set(rhino8.object_layer(curve) for curve in all_curves))
            self.log("All curves in document: {}".format(len(all_curves)))
            self.log(
                "Curve layers: {}".format(
                    ", ".join(all_layers) if all_layers else "none"
                )
            )
            selected_curves = [curve for curve in all_curves if is_cam_curve(curve)]
            ignored_count = len(all_curves) - len(selected_curves)
            self.log("Found curves: {}".format(len(selected_curves)))
            if ignored_count:
                self.log("Ignored guide curves: {}".format(ignored_count))
            if not selected_curves:
                self.log("DONE: no curves to process.")
                return False

            if cam_config.LOG_CURVE_SUMMARY:
                self.log_curve_summary(selected_curves)

            layer_curves = curves_by_layer(selected_curves)
            self.log("Found layers: {}".format(len(layer_curves)))
            ordered_layers = ordered_layer_names(layer_curves)
            self.log("Setup order: {}".format(", ".join(ordered_layers)))
            self.log(
                "Setup creation order: {}".format(
                    ", ".join(setup_creation_layer_names(layer_curves))
                )
            )
            for layer_name in ordered_layers:
                self.log(
                    "Layer {}: curves={}".format(
                        layer_name, len(layer_curves[layer_name])
                    )
                )

            mill_tool = rhinocam.create_mill_tool(
                rhinocam.load_tool_config(self.tool_file)
            )
            if not mill_tool:
                self.log("ERROR: tool was not created.")
                return False
            self.log("Mill tool created from: {}".format(self.tool_file))
            self.log("Using D3 mill tool for all strategies.")

            base_config = ProfilingConfig()
            base_config.stock_allowance = cam_config.DEFAULT_STOCK_ALLOWANCE_MM
            base_config.spindle_rpm = cam_config.SPINDLE_RPM
            self.log("Default stock allowance: {}".format(base_config.stock_allowance))
            self.log("Spindle RPM: {}".format(base_config.spindle_rpm))

            gcode_saver = None
            if self.save_gcode:
                save_module = self.load_save_module()
                output_dir = self.output_dir
                if not output_dir:
                    output_dir = save_module.choose_output_dir(
                        cam_config.gcode_dir(self.project_root)
                    )
                gcode_saver = save_module.GCodeSaver(output_dir, self.log)

            had_errors = False
            layer_state = rhino8.layer_state_snapshot()
            try:
                for layer_name in setup_creation_layer_names(layer_curves):
                    if rhino8.isolate_layer(layer_name):
                        self.log("Only layer {} is visible.".format(layer_name))
                        rhinocam.sync_database()
                    else:
                        self.log(
                            "WARNING: layer {} was not isolated.".format(layer_name)
                        )

                    if not self.run_layer(
                        layer_name,
                        layer_curves[layer_name],
                        base_config,
                        mill_tool,
                        gcode_saver,
                    ):
                        had_errors = True
            finally:
                rhino8.restore_layer_state(layer_state)
                self.log("Layer visibility restored.")

            if had_errors:
                self.log("DONE: script finished with errors.")
                return False

            self.log("DONE: script finished successfully.")
            return True
        finally:
            rhinocam.uninitialize()
            self.log("API uninitialized.")


def run(project_root, save_gcode=False, output_dir=None):
    return RhinoCamJob(
        project_root, save_gcode=save_gcode, output_dir=output_dir
    ).run()

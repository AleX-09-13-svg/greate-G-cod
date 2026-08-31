# -*- coding: utf-8 -*-
import importlib
import os

from cam import config as cam_config
from cam import operations as cam_operations
from cam.classification import classify_curves
from cam.classification import curves_by_layer
from cam.classification import is_cam_curve
from core.files import detect_changed_file
from core.files import file_snapshot
from core.files import rename_file
from core.layers import ordered_layer_names
from core.layers import setup_creation_layer_names
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
cam_operations = reload_module(cam_operations)

ProfilingConfig = cam_operations.ProfilingConfig
create_drilling = cam_operations.create_drilling
create_inside_profiling = cam_operations.create_inside_profiling
create_outside_profiling = cam_operations.create_outside_profiling
create_pocket_profiling = cam_operations.create_pocket_profiling


class RhinoCamJob(object):
    def __init__(self, project_root):
        self.project_root = project_root
        self.tool_file = cam_config.mill_tool_file(project_root)
        self.output_dir = cam_config.gcode_dir(project_root)
        self.logger = FileLogger(
            "[RhinoCAM main] ",
            os.path.join(project_root, "rhinocam_main.log"),
        )

    def log(self, message):
        self.logger.log(message)

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
        config.stock_allowance = base_config.stock_allowance
        config.spindle_rpm = base_config.spindle_rpm
        config.cut_direction = base_config.cut_direction
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
        return config

    def create_layer_operation(
        self, setup, operation_name, curves, tool, config, operation_factory
    ):
        if not curves:
            return None

        def sync_current_setup():
            rhinocam.sync_database()
            rhinocam.activate_setup(setup)

        self.log("Creating MOp {}: curves={}".format(operation_name, len(curves)))
        if not rhinocam.activate_setup(setup):
            self.log(
                "WARNING: active setup was not changed before {}.".format(
                    operation_name
                )
            )
        rhino8.select_objects(curves)
        rhinocam.sync_database()
        self.log("Selected operation curves synced with RhinoCAM database.")
        if not rhinocam.activate_setup(setup):
            self.log(
                "WARNING: active setup was not changed after selection for {}.".format(
                    operation_name
                )
            )
        return operation_factory(
            self.log, sync_current_setup, operation_name, tool, config
        )

    def rename_gcode_file(self, source_path, layer_name):
        if not source_path:
            self.log("No new file detected in output dir.")
            return None

        _, extension = os.path.splitext(source_path)
        if not extension:
            extension = ".nc"

        target_path = os.path.join(
            self.output_dir, rhino8.clean_windows_filename(layer_name) + extension
        )
        rename_file(source_path, target_path)

        self.log("G-code file: {}".format(target_path))
        return target_path

    def post_process_setup(self, setup, layer_name):
        if not os.path.isdir(self.output_dir):
            os.makedirs(self.output_dir)

        before_files = file_snapshot(self.output_dir)
        self.log("Active postprocessor: {}".format(rhinocam.active_postprocessor()))
        self.log("G-code output dir: {}".format(self.output_dir))

        ok, method_name = rhinocam.post_process_setup(self.output_dir, setup)
        self.log("PostProcessSetup method={} ok={}".format(method_name, ok))
        if not ok:
            return None

        return self.rename_gcode_file(
            detect_changed_file(self.output_dir, before_files), layer_name
        )

    def operation_plan(self, layer_name, strategy_curves, base_config, mill_tool):
        return [
            (
                "Nacolka",
                strategy_curves["hole_marks"],
                self.strategy_config(layer_name, base_config, "nacolka"),
                mill_tool,
                create_drilling,
            ),
            (
                "Skvoz_D5",
                strategy_curves["through_holes"],
                self.strategy_config(layer_name, base_config, "skvoznoe"),
                mill_tool,
                create_inside_profiling,
            ),
            (
                "Vyborka_D8_D9_D35_Z13",
                strategy_curves["pockets"],
                self.strategy_config(layer_name, base_config, "vyborka"),
                mill_tool,
                create_pocket_profiling,
            ),
            (
                "Vyborka_Inside_Kontur_Z13",
                strategy_curves["pockets"],
                self.strategy_config(layer_name, base_config, "vyborka"),
                mill_tool,
                create_inside_profiling,
            ),
            (
                "Kontur",
                strategy_curves["perimeters"],
                self.strategy_config(layer_name, base_config, "raskroy"),
                mill_tool,
                create_outside_profiling,
            ),
        ]

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

    def run_layer(self, layer_name, curves, base_config, mill_tool):
        strategy_curves, skipped_curves = classify_curves(curves)
        self.log(
            "Layer {} strategies: marks_3={}, holes_5={}, pockets_8_9_35={}, perimeters={}, skipped={}".format(
                layer_name,
                len(strategy_curves["hole_marks"]),
                len(strategy_curves["through_holes"]),
                len(strategy_curves["pockets"]),
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

        created_mops = []
        for (
            operation_name,
            operation_curves,
            operation_config,
            operation_tool,
            operation_factory,
        ) in self.operation_plan(layer_name, strategy_curves, base_config, mill_tool):
            self.log(
                "{}_{} params: allowance={}, step_down={}, cut_dir={}, spindle_rpm={}".format(
                    layer_name,
                    operation_name,
                    operation_config.stock_allowance,
                    operation_config.step_down,
                    operation_config.cut_direction,
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
                        "ERROR: operation {} was not created; continuing with next operation.".format(
                            "{}_{}".format(layer_name, operation_name)
                        )
                    )
                    return False
                continue

            created_mops.append(mop)

        if not created_mops:
            self.log("ERROR: no operations were created for {}.".format(layer_name))
            return False

        if not rhinocam.activate_setup(setup):
            self.log(
                "WARNING: active setup was not changed before postprocessing {}.".format(
                    layer_name
                )
            )
        if not self.post_process_setup(setup, layer_name):
            self.log(
                "ERROR: setup postprocessing failed for {}; continuing with next setup.".format(
                    layer_name
                )
            )
            return False

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
            bounds = curve_utils.bounds(selected_curves)
            if rhinocam.create_box_stock(bounds, base_config.top_z, base_config.depth, 1.0):
                self.log("Stock created from explicit curve box.")
            else:
                self.log("WARNING: explicit box stock was not created.")

            had_errors = False
            for layer_name in setup_creation_layer_names(layer_curves):
                if not self.run_layer(
                    layer_name, layer_curves[layer_name], base_config, mill_tool
                ):
                    had_errors = True

            if had_errors:
                self.log("DONE: script finished with errors.")
                return False

            self.log("DONE: script finished successfully.")
            return True
        finally:
            rhinocam.uninitialize()
            self.log("API uninitialized.")


def run(project_root):
    return RhinoCamJob(project_root).run()

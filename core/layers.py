# -*- coding: utf-8 -*-
import re


CAM_LAYER_PATTERN = re.compile(r"^(List_\d+|test)$", re.IGNORECASE)


def is_cam_layer(layer_name):
    return CAM_LAYER_PATTERN.match(layer_name or "") is not None


def layer_sort_key(layer_name):
    match = re.match(r"^List_(\d+)$", layer_name or "")
    if match:
        return (0, int(match.group(1)))
    if (layer_name or "").lower() == "test":
        return (0, 0)
    return (1, layer_name or "")


def ordered_layer_names(layer_curves):
    return sorted(layer_curves, key=layer_sort_key)


def setup_creation_layer_names(layer_curves):
    ordered = ordered_layer_names(layer_curves)
    if len(ordered) <= 2:
        return ordered

    return [ordered[0]] + list(reversed(ordered[1:]))

# Project Structure

```text
.
|-- main.py                  Short RhinoCAM entry point.
|-- Geometry to layers.py    Rhino entry point: prepares List_* layers from source geometry.
|-- core/                    Shared pure-Python helpers.
|   |-- project.py           Project root detection for RhinoCode staging runs.
|   |-- logging_utils.py     Terminal and file logging.
|   |-- files.py             Output file detection and renaming.
|   `-- layers.py            List_* layer filtering and ordering.
|-- geometry/                Rhino geometry queries and curve descriptions.
|-- cam/                     CAM scenario, classification, operation builders and tool configs.
|   |-- job.py               Creates setups, operations and one G-code file per List_* layer.
|   |-- classification.py    Sorts curves into marks, holes, pockets and perimeters.
|   |-- config.py            Shared CAM sizes, depths and project output paths.
|   |-- operations.py
|   `-- tools/
|-- plugins/                 Thin wrappers around Rhino and RhinoCAM APIs.
|-- data/models/             Source Rhino models.
|-- GCode/                   Generated output.
|-- archive/probnic/         Older probe/refactor scripts kept for reference.
|-- examples/                Reference G-code examples and archives.
`-- tools/                   Local helper scripts.
```

## Rhino Entry Points

Keep `main.py` and `Geometry to layers.py` in the project root. RhinoCode may run scripts from a temporary staging folder, so `main.py` bootstraps the project path before importing local packages.

## Generated Files

`GCode/` and `rhinocam_main.log` are runtime outputs. They can be deleted before a clean test run.

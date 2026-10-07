# Дерево Для `03main.py`

Это дерево показывает, какие внутренние файлы подключаются при запуске `03main.py`. Внешние модули Python, Rhino и RhinoCAM скрыты.

## Визуальная Схема

```mermaid
flowchart LR
    root["03main.py"]

    bootstrap["rhino_bootstrap.py"]
    cam_job["cam/job.py"]

    core_project["core/project.py"]

    cam_config["cam/config.py"]
    cam_classification["cam/classification.py"]
    cam_operations["cam/operations.py"]

    core_layers["core/layers.py"]
    core_logging["core/logging_utils.py"]

    geometry_curves["geometry/curves.py"]

    plugin_rhino8["plugins/rhino8.py"]
    plugin_rhinocam["plugins/rhinocam.py"]

    save_gcode["04_save_G_cod.py"]
    core_files["core/files.py"]

    root --> bootstrap
    root --> cam_job

    bootstrap --> core_project

    cam_job --> cam_config
    cam_job --> cam_classification
    cam_job --> cam_operations
    cam_job --> core_layers
    cam_job --> core_logging
    cam_job --> geometry_curves
    cam_job --> plugin_rhino8
    cam_job --> plugin_rhinocam
    cam_job -. save_gcode=True .-> save_gcode

    cam_classification --> cam_config
    cam_classification --> core_layers
    cam_classification --> geometry_curves
    cam_classification --> plugin_rhino8

    save_gcode --> core_files
    save_gcode --> plugin_rhinocam
    save_gcode -. bootstrap .-> bootstrap
```

## То Же Самое Как Дерево

```text
03main.py
|-- rhino_bootstrap.py
|   `-- core/project.py
|
`-- cam/job.py
    |-- cam/config.py
    |-- cam/classification.py
    |   |-- cam/config.py
    |   |-- core/layers.py
    |   |-- geometry/curves.py
    |   `-- plugins/rhino8.py
    |
    |-- cam/operations.py
    |-- core/layers.py
    |-- core/logging_utils.py
    |-- geometry/curves.py
    |-- plugins/rhino8.py
    |-- plugins/rhinocam.py
    |
    `-- 04_save_G_cod.py
        |-- rhino_bootstrap.py
        |   `-- core/project.py
        |-- core/files.py
        `-- plugins/rhinocam.py
```

## Как Читать

- Сплошная стрелка означает обычную зависимость файла от файла.
- Пунктирная стрелка означает динамическую загрузку через `importlib` или запуск только при определенном сценарии.
- `04_save_G_cod.py` появляется в дереве, потому что `03main.py` запускает `cam_job.run(PROJECT_ROOT, save_gcode=True)`.

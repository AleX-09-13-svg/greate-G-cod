# Карта Зависимостей Файлов

Ниже показаны внутренние зависимости Python-файлов проекта. Внешние библиотеки и API Rhino/RhinoCAM не включены, чтобы схема оставалась читаемой.

Обычное дерево файлов проекта лежит отдельно: [FILE_TREE.md](FILE_TREE.md).

```mermaid
flowchart LR
    main["03main.py"]
    save["04_save_G_cod.py"]
    bootstrap["rhino_bootstrap.py"]

    subgraph cam_pkg["cam/"]
        cam_job["job.py"]
        cam_classification["classification.py"]
        cam_config["config.py"]
        cam_operations["operations.py"]
    end

    subgraph core_pkg["core/"]
        core_files["files.py"]
        core_layers["layers.py"]
        core_logging["logging_utils.py"]
        core_project["project.py"]
    end

    subgraph geometry_pkg["geometry/"]
        geometry_curves["curves.py"]
    end

    subgraph plugins_pkg["plugins/"]
        plugin_rhino8["rhino8.py"]
        plugin_rhinocam["rhinocam.py"]
    end

    main --> cam_job
    main -. dynamic import .-> bootstrap

    save --> core_files
    save --> plugin_rhinocam
    save -. dynamic import .-> bootstrap

    bootstrap --> core_project

    cam_job --> cam_config
    cam_job --> cam_classification
    cam_job --> cam_operations
    cam_job --> core_layers
    cam_job --> core_logging
    cam_job --> geometry_curves
    cam_job --> plugin_rhino8
    cam_job --> plugin_rhinocam
    cam_job -. dynamic load .-> save

    cam_classification --> cam_config
    cam_classification --> core_layers
    cam_classification --> geometry_curves
    cam_classification --> plugin_rhino8
```

## Основной Поток

```text
03main.py
  -> rhino_bootstrap.py
  -> cam/job.py
       -> cam/config.py
       -> cam/classification.py
       -> cam/operations.py
       -> core/layers.py
       -> core/logging_utils.py
       -> geometry/curves.py
       -> plugins/rhino8.py
       -> plugins/rhinocam.py
       -> 04_save_G_cod.py
            -> core/files.py
            -> plugins/rhinocam.py
```

## Центральные Файлы

- `03main.py` - основная точка входа из RhinoCode.
- `rhino_bootstrap.py` - находит корень проекта и добавляет его в `sys.path`.
- `cam/job.py` - главный сценарий: создает setup, классифицирует кривые, добавляет операции, запускает сохранение G-code.
- `cam/operations.py` - сборка и настройка RhinoCAM-операций.
- `cam/classification.py` - распределение кривых по типам обработки.
- `04_save_G_cod.py` - отдельный модуль сохранения готовых setup в файлы G-code.

## Примечание

Пунктирные стрелки обозначают связи через `importlib` или загрузку модуля по пути, а не обычный `import`.

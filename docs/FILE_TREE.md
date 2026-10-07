# Дерево Файлов Проекта

Компактная карта структуры проекта. Служебные папки `.git/`, `__pycache__/` и временные файлы не раскрыты.

Для дерева зависимостей конкретно от `03main.py` смотри [03MAIN_TREE.md](03MAIN_TREE.md).

```text
create _G_code/
|-- 01Geometry to layers.py
|-- 02GeometryToZerro.py
|-- 03main.py
|-- 04_save_G_cod.py
|-- README.md
|-- rhino_bootstrap.py
|-- rhinocam_main.log
|
|-- cam/
|   |-- __init__.py
|   |-- classification.py
|   |-- config.py
|   |-- job.py
|   |-- operations.py
|   `-- tools/
|       `-- tool_D3.json
|
|-- core/
|   |-- __init__.py
|   |-- files.py
|   |-- layers.py
|   |-- logging_utils.py
|   `-- project.py
|
|-- geometry/
|   |-- __init__.py
|   `-- curves.py
|
|-- plugins/
|   |-- __init__.py
|   |-- rhino8.py
|   `-- rhinocam.py
|
|-- docs/
|   |-- DEPENDENCY_MAP.md
|   |-- FILES_AND_FOLDERS.md
|   |-- FILE_TREE.md
|   `-- PROJECT_STRUCTURE.md
|
|-- data/
|   `-- models/
|       |-- Probnic.3dm
|       |-- МДФ 19 в проекте.3dm
|       `-- МДФ 19 в проекте.3dmbak
|
|-- GCode/
|   |-- List_1.nc
|   |-- List_2.nc
|   |-- List_3.nc
|   |-- List_4.nc
|   |-- List_5.nc
|   `-- Test.nc
|
|-- examples/
|   `-- МДФ_УП_пример/
|       |-- MDF_16_L1.nc ... MDF_16_L13.nc
|       |-- MDF_19_L1.nc ... MDF_19_L3.nc
|       `-- МДФ_УП.rar
|
|-- archive/
|   `-- probnic/
|       |-- Project2.py
|       |-- Project2_probe.py
|       |-- Project2_probe_stock.py
|       `-- Project2_probe_stock_2.py ... Project2_probe_stock_10.py
|
|-- tools/
|   `-- tmp_read_sdk_pdf.py
|
`-- tmp/
    |-- pdf_source/
    |   |-- bedside_tables.pdf
    |   |-- cabinets.pdf
    |   `-- toilet_table.pdf
    `-- pdfs/
        |-- tumba_1.png
        |-- tumba_2.png
        `-- tumba_3.png
```

## Быстрая Навигация

```text
Точка входа RhinoCode       -> 03main.py
Bootstrap проекта           -> rhino_bootstrap.py
Главный CAM-сценарий        -> cam/job.py
Классификация кривых        -> cam/classification.py
Создание операций RhinoCAM  -> cam/operations.py
Настройки CAM               -> cam/config.py
Сохранение G-code           -> 04_save_G_cod.py
Обертки Rhino/RhinoCAM      -> plugins/
Общие утилиты               -> core/
Геометрия Rhino             -> geometry/
Готовые УП                  -> GCode/
Примеры УП                  -> examples/
```

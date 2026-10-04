# -*- coding: utf-8 -*-
import os


# Минимальный размер детали, которую считаем внешним контуром раскроя.
MIN_CAM_SIZE_MM = 37.0

# Допуск сравнения размеров. Должен отличать 4.9 мм от 5.0 мм.
SIZE_TOLERANCE_MM = 0.05

# Квадрат/окружность 3 мм считается наколкой.
HOLE_MARK_SIZE_MM = 3.0

# Квадрат/окружность 4.9 мм считается сквозным отверстием.
THROUGH_HOLE_SIZE_MM = 4.9

# Квадраты/окружности этих размеров считаются выборками.
POCKET_35_15_5_SIZES_MM = (35.0, 15.0, 5.0)
POCKET_8_SIZES_MM = (8.0,)

# Прямоугольник, у которого одна сторона 6 или 7 мм, считается пазом дна/задней стенки.
PAZ_DNO_ZADNST_SIDE_SIZES_MM = (6.0, 7.0)

# Припуск по умолчанию, если ниже не задано другое значение.
# 0.0 - идти точно по геометрии.
# 0.1 - оставить 0.1 мм материала.
# -0.1 - снять на 0.1 мм больше.
DEFAULT_STOCK_ALLOWANCE_MM = 0.0

# Обороты шпинделя. Параметр общий для всех УП и всех стратегий.
SPINDLE_RPM = 18000.0

# Подробный лог каждой кривой замедляет запуск на больших файлах.
LOG_CURVE_SUMMARY = False

# Основные настройки обработки. Обычно редактировать нужно только этот блок.
#
# Названия стратегий:
#   nacolka          - наколка 3 мм
#   vyborka_35_15_5  - выборка 35/15/5 мм
#   vyborka_8        - выборка 8 мм
#   paz_dno_zadnst   - паз дна/задней стенки
#   skvoznoe         - сквозное отверстие 4.9 мм
#   raskroy          - внешний раскрой
#
# cut_direction:
#   "climb"        - движение по часовой стрелке
#   "conventional" - движение против часовой стрелки
STRATEGIES = {
    "nacolka": {
        "depth": 2.0,              # Общая глубина обработки, мм.
        "step_down": 2.0,          # Съем по Z за один проход, мм.
        "stock_allowance": 0.0,    # Припуск для этой стратегии, мм.
        "cut_direction": "climb",  # Направление фрезерования.
        "plunge_feed": 300.0,      # Подача врезания вниз по Z.
        "approach_feed": 400.0,    # Подача подхода к началу реза.
        "engage_feed": 400.0,      # Подача входа в материал.
        "cut_feed": 800.0,         # Рабочая подача резания.
        "retract_feed": 1000.0,    # Подача отвода инструмента.
        "departure_feed": 1000.0,  # Подача выхода из реза.
    },
    "vyborka_35_15_5": {
        "depth": 13.0,             # Общая глубина выборки, мм.
        "step_down": 4.0,          # Съем по Z за один проход, мм.
        "stock_allowance": 0.0,    # Припуск для выборки, мм.
        "cut_direction": "climb",  # Направление фрезерования.
        "plunge_feed": 300.0,      # Подача врезания вниз по Z.
        "approach_feed": 400.0,    # Подача подхода к началу реза.
        "engage_feed": 400.0,      # Подача входа в материал.
        "cut_feed": 800.0,         # Рабочая подача резания.
        "retract_feed": 1000.0,    # Подача отвода инструмента.
        "departure_feed": 1000.0,  # Подача выхода из реза.
    },
    "vyborka_8": {
        "depth": 10.0,             # Общая глубина выборки, мм.
        "step_down": 4.0,          # Съем по Z за один проход, мм.
        "stock_allowance": 0.0,    # Припуск для выборки, мм.
        "cut_direction": "climb",  # Направление фрезерования.
        "plunge_feed": 300.0,      # Подача врезания вниз по Z.
        "approach_feed": 400.0,    # Подача подхода к началу реза.
        "engage_feed": 400.0,      # Подача входа в материал.
        "cut_feed": 800.0,         # Рабочая подача резания.
        "retract_feed": 1000.0,    # Подача отвода инструмента.
        "departure_feed": 1000.0,  # Подача выхода из реза.
    },
    "paz_dno_zadnst": {
        "depth": 8.0,              # Общая глубина паза, мм.
        "step_down": 4.0,          # Съем по Z за один проход, мм.
        "stock_allowance": 0.0,    # Припуск для паза, мм.
        "cut_direction": "climb",  # Направление фрезерования.
        "plunge_feed": 300.0,      # Подача врезания вниз по Z.
        "approach_feed": 400.0,    # Подача подхода к началу реза.
        "engage_feed": 400.0,      # Подача входа в материал.
        "cut_feed": 800.0,         # Рабочая подача резания.
        "retract_feed": 1000.0,    # Подача отвода инструмента.
        "departure_feed": 1000.0,  # Подача выхода из реза.
    },
    "skvoznoe": {
        "depth": 17.2,             # Общая глубина сквозного реза, мм.
        "step_down": 4.0,          # Съем по Z за один проход, мм.
        "stock_allowance": 0.0,    # Припуск для сквозной операции, мм.
        "cut_direction": "climb",  # Направление фрезерования.
        "plunge_feed": 300.0,      # Подача врезания вниз по Z.
        "approach_feed": 400.0,    # Подача подхода к началу реза.
        "engage_feed": 400.0,      # Подача входа в материал.
        "cut_feed": 800.0,         # Рабочая подача резания.
        "retract_feed": 1000.0,    # Подача отвода инструмента.
        "departure_feed": 1000.0,  # Подача выхода из реза.
    },
    "raskroy": {
        "depth": 16.0,             # Общая глубина раскроя, мм.
        "step_down": 4.0,          # Съем по Z за один проход, мм.
        "stock_allowance": 0.0,    # Припуск для раскроя, мм.
        "cut_direction": "climb",  # Направление фрезерования.
        "plunge_feed": 300.0,      # Подача врезания вниз по Z.
        "approach_feed": 400.0,    # Подача подхода к началу реза.
        "engage_feed": 400.0,      # Подача входа в материал.
        "cut_feed": 800.0,         # Рабочая подача резания.
        "retract_feed": 1000.0,    # Подача отвода инструмента.
        "departure_feed": 1000.0,  # Подача выхода из реза.
    },
}

# Припуск для всей конкретной УП.
# Например: {"List_1": 0.1, "List_2": -0.1}
STOCK_ALLOWANCE_BY_UP = {}

# Припуск для конкретной стратегии внутри конкретной УП.
# Например: {("List_1", "raskroy"): 0.1, ("List_2", "vyborka"): -0.1}
STOCK_ALLOWANCE_BY_UP_AND_STRATEGY = {}


def strategy_settings(strategy_name):
    return STRATEGIES[strategy_name].copy()


def stock_allowance_for(up_name, strategy_name):
    setup_strategy_key = (up_name, strategy_name)
    if setup_strategy_key in STOCK_ALLOWANCE_BY_UP_AND_STRATEGY:
        return STOCK_ALLOWANCE_BY_UP_AND_STRATEGY[setup_strategy_key]

    if up_name in STOCK_ALLOWANCE_BY_UP:
        return STOCK_ALLOWANCE_BY_UP[up_name]

    return strategy_settings(strategy_name)["stock_allowance"]


def mill_tool_file(project_root):
    return os.path.join(project_root, "cam", "tools", "tool_D3.json")


def gcode_dir(project_root):
    return os.path.join(project_root, "GCode")

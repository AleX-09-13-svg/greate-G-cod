#! python3
from mecsoftcamapi import *
import rhinoscriptsyntax as rs

from MecSoftCAM.Managers import ToolManager
from MecSoftCAM.Managers import StockManager
from MecSoftCAM.Managers import MOpManager
from MecSoftCAM.Types import ModuleType
from MecSoftCAM.Types import MillToolType

MecSoftCAM.API.Initialize()
MecSoftCAM.API.SetActiveModule(ModuleType.MILL)


# --- Берем вектора в Rhino ---
all_objects = rs.AllObjects()
all_curves = [obj for obj in all_objects if rs.IsCurve(obj)]
print("Найдено кривых:", len(all_curves))
   

# --- 2. Создание инструмента D3 ---
tool = ToolManager.CreateMillTool(MillToolType.MTOOL_FLAT)
if not tool:
    print("Ошибка: не удалось создать фрезу.")
    MecSoftCAM.API.Uninitialize()
    exit()

tool.SetDia(3.0)
tool.SetName("Фреза прямая D3")
tool.SetFluteLen(9.0)
tool.SetLen(24.0)
tool.SetShankDia(3.0)
ToolManager.SetActiveTool(tool)
print("Фреза D3 создана.")

# --- 3. Создание заготовки (обязательно!) ---
StockManager.CreatePartBoundingBoxStock()
print("Заготовка создана.")

# --- 4. Функция создания MOP Profiling с переданной геометрией ---
def create_profiling_mop(curves, tool, depth=16.0):
    """
    Создаёт операцию 2.5 Axis Profiling для переданных кривых.
    
    Аргументы:
        curves: список GUID кривых (из Rhino)
        tool: объект инструмента (Tool)
        depth: глубина резания в мм (положительное число, будет преобразовано в отрицательное)
    
    Возвращает:
        объект MOP или None при ошибке.
    """
    # --- Выделяем все переданные кривые (для добавления в MOP) ---
    rs.UnselectAllObjects()
    for obj in curves:
        rs.SelectObject(obj)
    MecSoftCAM.API.SyncDatabase()   # синхронизация базы данных RhinoCAM

    # --- Создание операции ---
    mop = MOpManager.Create2AProfilingMOp()
    if not mop:
        print("Ошибка: не удалось создать MOP.")
        return None

    # --- Настройка ---
    mop.Tool = tool
    mop.SetTotalCutDepth(16.0)   # глубина отрицательная (ось Z направлена вверх)

    if not  mop.AddSelectedGeometryToMOp():					
     SelectionManager.PopulateMOpWithSelectedGeometry(mop)					
    MecSoftCAM.API.SyncDatabase()

      # --- Подачи ---
    mop.SetPlungeFeedParam(300.0)
    mop.SetApproachFeedParam(400.0)
    mop.SetEngageFeedParam(400.0)
    mop.SetCutFeedParam(800.0)
    mop.SetRetractFeedParam(1000.0)
    mop.SetDepartureFeedParam(1000.0)

    # --- Регенерация ---
    if MOpManager.RegenerateMOp(mop):
     print("Траектория успешно пересчитана.")
   
    else:
     print("Ошибка при регенерации траектории.")

# --- Добавление геометрии (пробуем разные варианты метода) ---
				
					






    


# --- 5. Вызов функции с полученными кривыми ---
profMOp = create_profiling_mop(all_curves, tool, depth=16.0)

if profMOp:
    print("Операция Profiling создана и готова.")
else:
    print("Создание операции не удалось.")

# --- Завершение ---
MecSoftCAM.API.Uninitialize()
print("Скрипт завершён.")
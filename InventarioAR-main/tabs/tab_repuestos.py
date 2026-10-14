"""
Pestaña:   Stock de Repuestos
Versión:  5.0 - DATOS REALES DE LA BASE + EXPORTAR SQL (provisorio)
Fecha:  2026-08-10
Autor:  Lucas E Goitea Juarez
Descripción:
    Centro de control de cantidad de repuestos.
    Cada repuesto está vinculado a uno o varios modelos de equipo.

    ESTADOS DE CADA REPUESTO (conteo, sin identificar por serie):
      • EN STOCK        -> disponibles, por taller (Aeroparque / Ezeiza)
      • EN USO          -> instalados/en uso. Conteo GENERAL (no distingue
                           escala ni equipo). Ej: cuántas fuentes Yedro 13,8V
                           están en uso en total.
      • FUERA DE SERVICIO -> a reparar, por taller. Es un CONTADOR: el detalle
                           (de dónde vino / falla) va en una etiqueta física
                           que imprime el usuario; el sistema solo cuenta.
      TOTAL = en stock + en uso + fuera de servicio.

    CICLO DE ESTADOS:
        📥 Ingreso           -> + stock (taller)
        🔧 Usar en equipo    -> stock (taller)  →  en uso (general)
        🔴 Fuera de servicio -> en uso (general) → fuera de servicio (taller)
        ♻️ Reparar           -> fuera de servicio (taller) → stock (taller)
        🗑️ Descartar         -> - fuera de servicio (taller)  (baja definitiva)

    El HISTORIAL es únicamente del EQUIPO (lo maneja tab_taller / inventario),
    NO del repuesto.

    ─────────────────────────────────────────────────────────────
    INTEGRACIÓN con ingreso / modificación de equipo
    ─────────────────────────────────────────────────────────────
    Cuando ingresás o modificás un equipo y marcás qué repuestos usás,
    esa pantalla debe llamar a `aplicar_uso_por_equipo([(id_repuesto, cant), ...])`
    (o al endpoint equivalente). Eso descuenta stock y suma "en uso" GENERAL.
    En esta tab, el botón "🔧 Usar en equipo" hace exactamente esa operación
    para probar la lógica de forma aislada.

    ─────────────────────────────────────────────────────────────
    MODO STANDALONE / PRUEBA   ->   python tab_stock_repuestos.py
    ─────────────────────────────────────────────────────────────
    Integración en main.py:
        from tabs.tab_stock_repuestos import StockRepuestosTab
        self.stock_repuestos_tab = StockRepuestosTab(self.api)
        self.tabs.addTab(self.stock_repuestos_tab, "🔧 Stock de Repuestos")

    ─────────────────────────────────────────────────────────────
    NOTA BASE DE DATOS (para cuando enchufes el backend)
    ─────────────────────────────────────────────────────────────
    Ya existen: `talleres`, `modelo_repuesto`.

        ALTER TABLE `repuestos`
            ADD COLUMN `numero_parte`  VARCHAR(60) NULL AFTER `id_repuesto`,
            ADD COLUMN `stock_inicial` INT(11) NOT NULL DEFAULT 0 AFTER `descripcion`,
            ADD COLUMN `en_uso`        INT(11) NOT NULL DEFAULT 0;  -- conteo general

        CREATE TABLE `repuesto_stock` (
            `id_repuesto`     INT(11) NOT NULL,
            `id_taller`       INT(11) NOT NULL,
            `stock_actual`    INT(11) NOT NULL DEFAULT 0,   -- en stock (disponible)
            `fuera_servicio`  INT(11) NOT NULL DEFAULT 0,   -- contador a reparar
            `fecha_ingreso`   DATETIME NULL,
            PRIMARY KEY (`id_repuesto`, `id_taller`),
            FOREIGN KEY (`id_repuesto`) REFERENCES `repuestos`(`id_repuesto`),
            FOREIGN KEY (`id_taller`)   REFERENCES `talleres`(`id_taller`)
        );

    Endpoints sugeridos:
        ingreso_repuesto.php   -> +stock_actual, fecha_ingreso = ahora
        usar_repuesto.php      -> -stock_actual, +en_uso   (desde ingreso/modif equipo)
        fuera_servicio.php     -> -en_uso, +fuera_servicio
        reparar_repuesto.php   -> -fuera_servicio, +stock_actual
        descartar_repuesto.php -> -fuera_servicio
"""

import sys
from datetime import datetime
from base_tab import ApiTab
from api_client import ApiError, SesionExpirada
from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QFrame, QComboBox, QTableWidget, QTableWidgetItem,
    QHeaderView, QMessageBox, QAbstractItemView, QGridLayout, QMenu,
    QSpinBox, QListWidget, QListWidgetItem, QDialog, QFileDialog, QScrollArea
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QColor, QBrush, QAction


# ═══════════════════════════════════════════════════════════
#  CONFIGURACIÓN
# ═══════════════════════════════════════════════════════════
TALLERES = ["Aeroparque", "Ezeiza"]

NOMBRES_TALLER_REAL = {
    "Aeroparque": "Aeroparque",
    "Ezeiza": "Ezeiza",
}

UMBRAL_BAJO = 10

# id_taller REALES de la base (para exportar SQL de migración).
# Compatibilidad: los identificadores de tablas/columnas van en minúscula, como en el dump.
TALLER_ID = {"Aeroparque": 1, "Ezeiza": 2}          # 1=Taller de radio AEP, 2=Taller de radio EZE
IDS_ORIGINALES_BD = set(range(1, 73))               # repuestos 1..72 ya existentes en la base


# ═══════════════════════════════════════════════════════════
#  DATOS DE EJEMPLO (modo standalone / prueba)
# ═══════════════════════════════════════════════════════════
MODELOS_EJEMPLO = [
    (78, "CARABAJAL LOG PERIODICA HF"),
    (35, "CUBIC LCR 2000"),
    (34, "CUBIC PA 5050 A"),
    (33, "CUBIC PS-7130 A-1"),
    (36, "CUBIC T 4150"),
    (30, "DRAFT EP-815"),
    (31, "EIFFEL COLINEAL DE TUBO"),
    (75, "EIFFEL HI-POWER FM RINGO"),
    (83, "EIFFEL MAGNETICA PORTATIL U"),
    (76, "EIFFEL MAGNETICA PORTATIL V"),
    (74, "EIFFEL VHFO-AERO RINGO"),
    (60, "ICOM HM-12"),
    (52, "ICOM HM-176"),
    (54, "ICOM HM-216"),
    (3, "ICOM IC-A110"),
    (4, "ICOM IC-A120"),
    (5, "ICOM IC-A14"),
    (1, "ICOM IC-A200"),
    (2, "ICOM IC-A210"),
    (6, "ICOM IC-V80"),
    (27, "ICOM MB-53"),
    (58, "ICOM SM-25"),
    (10, "KENWOOD TK-90"),
    (79, "MFJ G5-RV HF"),
    (56, "MOTOROLA 4013A"),
    (59, "MOTOROLA 4025C"),
    (21, "MOTOROLA DEM300"),
    (22, "MOTOROLA DEP450"),
    (42, "MOTOROLA DGM6100"),
    (23, "MOTOROLA EM200"),
    (26, "MOTOROLA EM400"),
    (25, "MOTOROLA EP450"),
    (43, "MOTOROLA GM300"),
    (47, "MOTOROLA HL-N8096A"),
    (53, "MOTOROLA HMN31748"),
    (48, "MOTOROLA HMN3596A"),
    (29, "MOTOROLA JACKBOX"),
    (40, "MOTOROLA MIP 5000"),
    (57, "MOTOROLA PIE"),
    (55, "MOTOROLA PMMN4090A"),
    (46, "MOTOROLA PRO2150"),
    (41, "MOTOROLA PRO3100"),
    (32, "MOTOROLA PRO3150"),
    (24, "MOTOROLA PRO5100"),
    (9, "MOTOROLA R2"),
    (50, "MOTOROLA RLN4008E"),
    (49, "MOTOROLA RMN5065A"),
    (51, "MOTOROLA RMN5068A"),
    (69, "PLANE FINDER ADS-B / MLAT RADAR"),
    (81, "PLANE FINDER HIGH PERFORMANCE ADSB"),
    (73, "PLUS GAIN COLINEAL DX-9 DB"),
    (82, "PLUS GAIN OA-4 PARAGUITA"),
    (72, "PLUS GAIN SLIM JIM"),
    (80, "TAMECO HILO LARGO HF"),
    (77, "TAMECO TROMBON AERONAUTICA"),
    (62, "UBIQUITI AIRFIBER 5X"),
    (66, "UBIQUITI LITEBEAM 5AC"),
    (63, "UBIQUITI LTU LITE"),
    (20, "UBIQUITI LTU LR"),
    (61, "UBIQUITI NANOBEAM 5AC"),
    (67, "UBIQUITI NANOSTATION 5AC LOCO"),
    (64, "UBIQUITI POWERBEAM 5AC"),
    (65, "UBIQUITI POWERBEAM M5 400"),
    (68, "UBIQUITI PRISMSTATION"),
    (45, "UNIDEN BC340CRS"),
    (11, "UNIDEN BC355N"),
    (12, "UNIDEN BC365CRS"),
    (13, "UNIDEN UBC860XLT"),
    (71, "WALMAR SR-150 RINGO"),
    (70, "WALMAR SR-2 AERO"),
    (39, "YEDRO YCF27SEC"),
    (38, "ZURICH RPS-1305"),
    (37, "ZURICH RPS-1315"),
    (44, "ZURICH YCF17E"),
    (84, "ÉLO "),
    (28, "ÉLO E292567"),
]


def _taller(stock, fuera_servicio, fecha):
    return {"stock": stock, "fuera_servicio": fuera_servicio, "fecha_ingreso": fecha}


# Marca y modelo (corto) por id_modelo, para armar la compatibilidad agrupada.
MODELO_MARCA = {
    1: "ICOM",
    2: "ICOM",
    3: "ICOM",
    4: "ICOM",
    5: "ICOM",
    6: "ICOM",
    9: "MOTOROLA",
    10: "KENWOOD",
    11: "UNIDEN",
    12: "UNIDEN",
    13: "UNIDEN",
    20: "UBIQUITI",
    21: "MOTOROLA",
    22: "MOTOROLA",
    23: "MOTOROLA",
    24: "MOTOROLA",
    25: "MOTOROLA",
    26: "MOTOROLA",
    27: "ICOM",
    28: "ÉLO",
    29: "MOTOROLA",
    30: "DRAFT",
    31: "EIFFEL",
    32: "MOTOROLA",
    33: "CUBIC",
    34: "CUBIC",
    35: "CUBIC",
    36: "CUBIC",
    37: "ZURICH",
    38: "ZURICH",
    39: "YEDRO",
    40: "MOTOROLA",
    41: "MOTOROLA",
    42: "MOTOROLA",
    43: "MOTOROLA",
    44: "ZURICH",
    45: "UNIDEN",
    46: "MOTOROLA",
    47: "MOTOROLA",
    48: "MOTOROLA",
    49: "MOTOROLA",
    50: "MOTOROLA",
    51: "MOTOROLA",
    52: "ICOM",
    53: "MOTOROLA",
    54: "ICOM",
    55: "MOTOROLA",
    56: "MOTOROLA",
    57: "MOTOROLA",
    58: "ICOM",
    59: "MOTOROLA",
    60: "ICOM",
    61: "UBIQUITI",
    62: "UBIQUITI",
    63: "UBIQUITI",
    64: "UBIQUITI",
    65: "UBIQUITI",
    66: "UBIQUITI",
    67: "UBIQUITI",
    68: "UBIQUITI",
    69: "PLANE FINDER",
    70: "WALMAR",
    71: "WALMAR",
    72: "PLUS GAIN",
    73: "PLUS GAIN",
    74: "EIFFEL",
    75: "EIFFEL",
    76: "EIFFEL",
    77: "TAMECO",
    78: "CARABAJAL",
    79: "MFJ",
    80: "TAMECO",
    81: "PLANE FINDER",
    82: "PLUS GAIN",
    83: "EIFFEL",
    84: "ÉLO",
}
MODELO_CORTO = {
    1: "IC-A200",
    2: "IC-A210",
    3: "IC-A110",
    4: "IC-A120",
    5: "IC-A14",
    6: "IC-V80",
    9: "R2",
    10: "TK-90",
    11: "BC355N",
    12: "BC365CRS",
    13: "UBC860XLT",
    20: "LTU LR",
    21: "DEM300",
    22: "DEP450",
    23: "EM200",
    24: "PRO5100",
    25: "EP450",
    26: "EM400",
    27: "MB-53",
    28: "E292567",
    29: "JACKBOX",
    30: "EP-815",
    31: "COLINEAL DE TUBO",
    32: "PRO3150",
    33: "PS-7130 A-1",
    34: "PA 5050 A",
    35: "LCR 2000",
    36: "T 4150",
    37: "RPS-1315",
    38: "RPS-1305",
    39: "YCF27SEC",
    40: "MIP 5000",
    41: "PRO3100",
    42: "DGM6100",
    43: "GM300",
    44: "YCF17E",
    45: "BC340CRS",
    46: "PRO2150",
    47: "HL-N8096A",
    48: "HMN3596A",
    49: "RMN5065A",
    50: "RLN4008E",
    51: "RMN5068A",
    52: "HM-176",
    53: "HMN31748",
    54: "HM-216",
    55: "PMMN4090A",
    56: "4013A",
    57: "PIE",
    58: "SM-25",
    59: "4025C",
    60: "HM-12",
    61: "NANOBEAM 5AC",
    62: "AIRFIBER 5X",
    63: "LTU LITE",
    64: "POWERBEAM 5AC",
    65: "POWERBEAM M5 400",
    66: "LITEBEAM 5AC",
    67: "NANOSTATION 5AC LOCO",
    68: "PRISMSTATION",
    69: "ADS-B / MLAT RADAR",
    70: "SR-2 AERO",
    71: "SR-150 RINGO",
    72: "SLIM JIM",
    73: "COLINEAL DX-9 DB",
    74: "VHFO-AERO RINGO",
    75: "HI-POWER FM RINGO",
    76: "MAGNETICA PORTATIL V",
    77: "TROMBON AERONAUTICA",
    78: "LOG PERIODICA HF",
    79: "G5-RV HF",
    80: "HILO LARGO HF",
    81: "HIGH PERFORMANCE ADSB",
    82: "OA-4 PARAGUITA",
    83: "MAGNETICA PORTATIL U",
    84: "",
}


REPUESTOS_EJEMPLO = [
    {"id_repuesto": 1, "numero_parte": "", "nombre": "POTENCIOMETRO", "descripcion": "Motorola EP450/DEP450", "stock_inicial": 100, "modelos": [22, 25], "en_uso": 0, "talleres": {"Aeroparque": _taller(0, 0, None), "Ezeiza": _taller(0, 0, None)}},
    {"id_repuesto": 2, "numero_parte": "", "nombre": "ANTENA", "descripcion": "Motorola EP450/DEP450", "stock_inicial": 100, "modelos": [22, 25], "en_uso": 0, "talleres": {"Aeroparque": _taller(0, 0, None), "Ezeiza": _taller(0, 0, None)}},
    {"id_repuesto": 3, "numero_parte": "", "nombre": "CARCAZA", "descripcion": "Motorola EP450/DEP450", "stock_inicial": 100, "modelos": [22, 25], "en_uso": 0, "talleres": {"Aeroparque": _taller(0, 0, None), "Ezeiza": _taller(0, 0, None)}},
    {"id_repuesto": 4, "numero_parte": "", "nombre": "BATERIA", "descripcion": "Motorola EP450/DEP450", "stock_inicial": 100, "modelos": [22, 25], "en_uso": 0, "talleres": {"Aeroparque": _taller(0, 0, None), "Ezeiza": _taller(0, 0, None)}},
    {"id_repuesto": 5, "numero_parte": "", "nombre": "SWITCH PTT", "descripcion": "Motorola EP450/DEP450", "stock_inicial": 100, "modelos": [22, 25], "en_uso": 0, "talleres": {"Aeroparque": _taller(0, 0, None), "Ezeiza": _taller(0, 0, None)}},
    {"id_repuesto": 6, "numero_parte": "", "nombre": "GOMA PTT", "descripcion": "Motorola EP450/DEP450", "stock_inicial": 100, "modelos": [22, 25], "en_uso": 0, "talleres": {"Aeroparque": _taller(0, 0, None), "Ezeiza": _taller(0, 0, None)}},
    {"id_repuesto": 7, "numero_parte": "", "nombre": "PLASTICO/BISEL PTT", "descripcion": "Motorola EP450/DEP450", "stock_inicial": 100, "modelos": [22, 25], "en_uso": 0, "talleres": {"Aeroparque": _taller(0, 0, None), "Ezeiza": _taller(0, 0, None)}},
    {"id_repuesto": 8, "numero_parte": "", "nombre": "CLIP DE CINTURA", "descripcion": "Motorola EP450/DEP450", "stock_inicial": 100, "modelos": [22, 25], "en_uso": 0, "talleres": {"Aeroparque": _taller(0, 0, None), "Ezeiza": _taller(0, 0, None)}},
    {"id_repuesto": 9, "numero_parte": "", "nombre": "PARLANTE", "descripcion": "Motorola EP450/DEP450", "stock_inicial": 100, "modelos": [22, 25], "en_uso": 0, "talleres": {"Aeroparque": _taller(0, 0, None), "Ezeiza": _taller(0, 0, None)}},
    {"id_repuesto": 10, "numero_parte": "", "nombre": "MICROFONO", "descripcion": "Motorola EP450/DEP450", "stock_inicial": 100, "modelos": [22, 25], "en_uso": 0, "talleres": {"Aeroparque": _taller(0, 0, None), "Ezeiza": _taller(0, 0, None)}},
    {"id_repuesto": 11, "numero_parte": "", "nombre": "DISPLAY", "descripcion": "Motorola EP450/DEP450", "stock_inicial": 100, "modelos": [22, 25], "en_uso": 0, "talleres": {"Aeroparque": _taller(0, 0, None), "Ezeiza": _taller(0, 0, None)}},
    {"id_repuesto": 12, "numero_parte": "", "nombre": "CONECTOR RF", "descripcion": "Motorola EP450/DEP450", "stock_inicial": 100, "modelos": [22, 25], "en_uso": 0, "talleres": {"Aeroparque": _taller(0, 0, None), "Ezeiza": _taller(0, 0, None)}},
    {"id_repuesto": 13, "numero_parte": "", "nombre": "POTENCIOMETRO", "descripcion": "Motorola R2", "stock_inicial": 100, "modelos": [9], "en_uso": 0, "talleres": {"Aeroparque": _taller(0, 0, None), "Ezeiza": _taller(0, 0, None)}},
    {"id_repuesto": 14, "numero_parte": "", "nombre": "ANTENA", "descripcion": "Motorola R2", "stock_inicial": 100, "modelos": [9], "en_uso": 0, "talleres": {"Aeroparque": _taller(0, 0, None), "Ezeiza": _taller(0, 0, None)}},
    {"id_repuesto": 15, "numero_parte": "", "nombre": "CARCAZA", "descripcion": "Motorola R2", "stock_inicial": 100, "modelos": [9], "en_uso": 0, "talleres": {"Aeroparque": _taller(0, 0, None), "Ezeiza": _taller(0, 0, None)}},
    {"id_repuesto": 16, "numero_parte": "", "nombre": "BATERIA", "descripcion": "Motorola R2", "stock_inicial": 100, "modelos": [9], "en_uso": 0, "talleres": {"Aeroparque": _taller(0, 0, None), "Ezeiza": _taller(0, 0, None)}},
    {"id_repuesto": 17, "numero_parte": "", "nombre": "SWITCH PTT", "descripcion": "Motorola R2", "stock_inicial": 100, "modelos": [9], "en_uso": 0, "talleres": {"Aeroparque": _taller(0, 0, None), "Ezeiza": _taller(0, 0, None)}},
    {"id_repuesto": 18, "numero_parte": "", "nombre": "GOMA PTT", "descripcion": "Motorola R2", "stock_inicial": 100, "modelos": [9], "en_uso": 0, "talleres": {"Aeroparque": _taller(0, 0, None), "Ezeiza": _taller(0, 0, None)}},
    {"id_repuesto": 19, "numero_parte": "", "nombre": "PLASTICO/BISEL PTT", "descripcion": "Motorola R2", "stock_inicial": 100, "modelos": [9], "en_uso": 0, "talleres": {"Aeroparque": _taller(0, 0, None), "Ezeiza": _taller(0, 0, None)}},
    {"id_repuesto": 20, "numero_parte": "", "nombre": "CLIP DE CINTURA", "descripcion": "Motorola R2", "stock_inicial": 100, "modelos": [9], "en_uso": 0, "talleres": {"Aeroparque": _taller(0, 0, None), "Ezeiza": _taller(0, 0, None)}},
    {"id_repuesto": 21, "numero_parte": "", "nombre": "PARLANTE", "descripcion": "Motorola R2", "stock_inicial": 100, "modelos": [9], "en_uso": 0, "talleres": {"Aeroparque": _taller(0, 0, None), "Ezeiza": _taller(0, 0, None)}},
    {"id_repuesto": 22, "numero_parte": "", "nombre": "MICROFONO", "descripcion": "Motorola R2", "stock_inicial": 100, "modelos": [9], "en_uso": 0, "talleres": {"Aeroparque": _taller(0, 0, None), "Ezeiza": _taller(0, 0, None)}},
    {"id_repuesto": 23, "numero_parte": "", "nombre": "DISPLAY", "descripcion": "Motorola R2", "stock_inicial": 100, "modelos": [9], "en_uso": 0, "talleres": {"Aeroparque": _taller(0, 0, None), "Ezeiza": _taller(0, 0, None)}},
    {"id_repuesto": 24, "numero_parte": "", "nombre": "CONECTOR RF", "descripcion": "Motorola R2", "stock_inicial": 100, "modelos": [9], "en_uso": 0, "talleres": {"Aeroparque": _taller(0, 0, None), "Ezeiza": _taller(0, 0, None)}},
    {"id_repuesto": 25, "numero_parte": "", "nombre": "POTENCIOMETRO", "descripcion": "ICOM IC-A210", "stock_inicial": 100, "modelos": [2], "en_uso": 0, "talleres": {"Aeroparque": _taller(0, 0, None), "Ezeiza": _taller(0, 0, None)}},
    {"id_repuesto": 26, "numero_parte": "", "nombre": "ANTENA", "descripcion": "ICOM IC-A210", "stock_inicial": 100, "modelos": [2], "en_uso": 0, "talleres": {"Aeroparque": _taller(0, 0, None), "Ezeiza": _taller(0, 0, None)}},
    {"id_repuesto": 27, "numero_parte": "", "nombre": "CARCAZA", "descripcion": "ICOM IC-A210", "stock_inicial": 97, "modelos": [2], "en_uso": 0, "talleres": {"Aeroparque": _taller(0, 0, None), "Ezeiza": _taller(0, 0, None)}},
    {"id_repuesto": 28, "numero_parte": "", "nombre": "BATERIA", "descripcion": "ICOM IC-A210", "stock_inicial": 100, "modelos": [2], "en_uso": 0, "talleres": {"Aeroparque": _taller(0, 0, None), "Ezeiza": _taller(0, 0, None)}},
    {"id_repuesto": 29, "numero_parte": "", "nombre": "SWITCH PTT", "descripcion": "ICOM IC-A210", "stock_inicial": 97, "modelos": [2], "en_uso": 0, "talleres": {"Aeroparque": _taller(0, 0, None), "Ezeiza": _taller(0, 0, None)}},
    {"id_repuesto": 30, "numero_parte": "", "nombre": "GOMA PTT", "descripcion": "ICOM IC-A210", "stock_inicial": 100, "modelos": [2], "en_uso": 0, "talleres": {"Aeroparque": _taller(0, 0, None), "Ezeiza": _taller(0, 0, None)}},
    {"id_repuesto": 31, "numero_parte": "", "nombre": "PLASTICO/BISEL PTT", "descripcion": "ICOM IC-A210", "stock_inicial": 99, "modelos": [2], "en_uso": 0, "talleres": {"Aeroparque": _taller(0, 0, None), "Ezeiza": _taller(0, 0, None)}},
    {"id_repuesto": 32, "numero_parte": "", "nombre": "CLIP DE CINTURA", "descripcion": "ICOM IC-A210", "stock_inicial": 100, "modelos": [2], "en_uso": 0, "talleres": {"Aeroparque": _taller(0, 0, None), "Ezeiza": _taller(0, 0, None)}},
    {"id_repuesto": 33, "numero_parte": "", "nombre": "PARLANTE", "descripcion": "ICOM IC-A210", "stock_inicial": 100, "modelos": [2], "en_uso": 0, "talleres": {"Aeroparque": _taller(0, 0, None), "Ezeiza": _taller(0, 0, None)}},
    {"id_repuesto": 34, "numero_parte": "", "nombre": "MICROFONO", "descripcion": "ICOM IC-A210", "stock_inicial": 100, "modelos": [2], "en_uso": 0, "talleres": {"Aeroparque": _taller(0, 0, None), "Ezeiza": _taller(0, 0, None)}},
    {"id_repuesto": 35, "numero_parte": "", "nombre": "DISPLAY", "descripcion": "ICOM IC-A210", "stock_inicial": 100, "modelos": [2], "en_uso": 0, "talleres": {"Aeroparque": _taller(0, 0, None), "Ezeiza": _taller(0, 0, None)}},
    {"id_repuesto": 36, "numero_parte": "", "nombre": "CONECTOR RF", "descripcion": "ICOM IC-A210", "stock_inicial": 100, "modelos": [2], "en_uso": 0, "talleres": {"Aeroparque": _taller(0, 0, None), "Ezeiza": _taller(0, 0, None)}},
    {"id_repuesto": 37, "numero_parte": "", "nombre": "POTENCIOMETRO", "descripcion": "ICOM IC-A200", "stock_inicial": 100, "modelos": [1], "en_uso": 0, "talleres": {"Aeroparque": _taller(0, 0, None), "Ezeiza": _taller(0, 0, None)}},
    {"id_repuesto": 38, "numero_parte": "", "nombre": "ANTENA", "descripcion": "ICOM IC-A200", "stock_inicial": 100, "modelos": [1], "en_uso": 0, "talleres": {"Aeroparque": _taller(0, 0, None), "Ezeiza": _taller(0, 0, None)}},
    {"id_repuesto": 39, "numero_parte": "", "nombre": "CARCAZA", "descripcion": "ICOM IC-A200", "stock_inicial": 100, "modelos": [1], "en_uso": 0, "talleres": {"Aeroparque": _taller(0, 0, None), "Ezeiza": _taller(0, 0, None)}},
    {"id_repuesto": 40, "numero_parte": "", "nombre": "BATERIA", "descripcion": "ICOM IC-A200", "stock_inicial": 100, "modelos": [1], "en_uso": 0, "talleres": {"Aeroparque": _taller(0, 0, None), "Ezeiza": _taller(0, 0, None)}},
    {"id_repuesto": 41, "numero_parte": "", "nombre": "SWTICH PTT", "descripcion": "ICOM IC-A200", "stock_inicial": 100, "modelos": [1], "en_uso": 0, "talleres": {"Aeroparque": _taller(0, 0, None), "Ezeiza": _taller(0, 0, None)}},
    {"id_repuesto": 42, "numero_parte": "", "nombre": "GOMA PTT", "descripcion": "ICOM IC-A200", "stock_inicial": 100, "modelos": [1], "en_uso": 0, "talleres": {"Aeroparque": _taller(0, 0, None), "Ezeiza": _taller(0, 0, None)}},
    {"id_repuesto": 43, "numero_parte": "", "nombre": "PLASTICO/BISEL PTT", "descripcion": "ICOM IC-A200", "stock_inicial": 100, "modelos": [1], "en_uso": 0, "talleres": {"Aeroparque": _taller(0, 0, None), "Ezeiza": _taller(0, 0, None)}},
    {"id_repuesto": 44, "numero_parte": "", "nombre": "CLIP DE CINTURA", "descripcion": "ICOM IC-A200", "stock_inicial": 100, "modelos": [1], "en_uso": 0, "talleres": {"Aeroparque": _taller(0, 0, None), "Ezeiza": _taller(0, 0, None)}},
    {"id_repuesto": 45, "numero_parte": "", "nombre": "PARLANTE", "descripcion": "ICOM IC-A200", "stock_inicial": 100, "modelos": [1], "en_uso": 0, "talleres": {"Aeroparque": _taller(0, 0, None), "Ezeiza": _taller(0, 0, None)}},
    {"id_repuesto": 46, "numero_parte": "", "nombre": "MICROFONO", "descripcion": "ICOM IC-A200", "stock_inicial": 100, "modelos": [1], "en_uso": 0, "talleres": {"Aeroparque": _taller(0, 0, None), "Ezeiza": _taller(0, 0, None)}},
    {"id_repuesto": 47, "numero_parte": "", "nombre": "DISPLAY", "descripcion": "ICOM IC-A200", "stock_inicial": 100, "modelos": [1], "en_uso": 0, "talleres": {"Aeroparque": _taller(0, 0, None), "Ezeiza": _taller(0, 0, None)}},
    {"id_repuesto": 48, "numero_parte": "", "nombre": "CONECTOR RF", "descripcion": "ICOM IC-A200", "stock_inicial": 100, "modelos": [1], "en_uso": 0, "talleres": {"Aeroparque": _taller(0, 0, None), "Ezeiza": _taller(0, 0, None)}},
    {"id_repuesto": 49, "numero_parte": "", "nombre": "POTENCIOMETRO", "descripcion": "Motorola EM-200", "stock_inicial": 100, "modelos": [23], "en_uso": 0, "talleres": {"Aeroparque": _taller(0, 0, None), "Ezeiza": _taller(0, 0, None)}},
    {"id_repuesto": 50, "numero_parte": "", "nombre": "ANTENA", "descripcion": "Motorola EM-200", "stock_inicial": 100, "modelos": [23], "en_uso": 0, "talleres": {"Aeroparque": _taller(0, 0, None), "Ezeiza": _taller(0, 0, None)}},
    {"id_repuesto": 51, "numero_parte": "", "nombre": "CARCAZA", "descripcion": "Motorola EM-200", "stock_inicial": 100, "modelos": [23], "en_uso": 0, "talleres": {"Aeroparque": _taller(0, 0, None), "Ezeiza": _taller(0, 0, None)}},
    {"id_repuesto": 52, "numero_parte": "", "nombre": "BATERIA", "descripcion": "Motorola EM-200", "stock_inicial": 100, "modelos": [23], "en_uso": 0, "talleres": {"Aeroparque": _taller(0, 0, None), "Ezeiza": _taller(0, 0, None)}},
    {"id_repuesto": 53, "numero_parte": "", "nombre": "SWITCH PTT", "descripcion": "Motorola EM-200", "stock_inicial": 100, "modelos": [23], "en_uso": 0, "talleres": {"Aeroparque": _taller(0, 0, None), "Ezeiza": _taller(0, 0, None)}},
    {"id_repuesto": 54, "numero_parte": "", "nombre": "GOMA PTT", "descripcion": "Motorola EM-200", "stock_inicial": 100, "modelos": [23], "en_uso": 0, "talleres": {"Aeroparque": _taller(0, 0, None), "Ezeiza": _taller(0, 0, None)}},
    {"id_repuesto": 55, "numero_parte": "", "nombre": "PLASTICO/BISEL PTT", "descripcion": "Motorola EM-200", "stock_inicial": 100, "modelos": [23], "en_uso": 0, "talleres": {"Aeroparque": _taller(0, 0, None), "Ezeiza": _taller(0, 0, None)}},
    {"id_repuesto": 56, "numero_parte": "", "nombre": "CLIP DE CINTURA", "descripcion": "Motorola EM-200", "stock_inicial": 100, "modelos": [23], "en_uso": 0, "talleres": {"Aeroparque": _taller(0, 0, None), "Ezeiza": _taller(0, 0, None)}},
    {"id_repuesto": 57, "numero_parte": "", "nombre": "PARLANTE", "descripcion": "Motorola EM-200", "stock_inicial": 100, "modelos": [23], "en_uso": 0, "talleres": {"Aeroparque": _taller(0, 0, None), "Ezeiza": _taller(0, 0, None)}},
    {"id_repuesto": 58, "numero_parte": "", "nombre": "MICROFONO", "descripcion": "Motorola EM-200", "stock_inicial": 100, "modelos": [23], "en_uso": 0, "talleres": {"Aeroparque": _taller(0, 0, None), "Ezeiza": _taller(0, 0, None)}},
    {"id_repuesto": 59, "numero_parte": "", "nombre": "DISPLAY", "descripcion": "Motorola EM-200", "stock_inicial": 100, "modelos": [23], "en_uso": 0, "talleres": {"Aeroparque": _taller(0, 0, None), "Ezeiza": _taller(0, 0, None)}},
    {"id_repuesto": 60, "numero_parte": "", "nombre": "CONECTOR RF", "descripcion": "Motorola EM-200", "stock_inicial": 100, "modelos": [23], "en_uso": 0, "talleres": {"Aeroparque": _taller(0, 0, None), "Ezeiza": _taller(0, 0, None)}},
    {"id_repuesto": 61, "numero_parte": "", "nombre": "POTENCIOMETRO", "descripcion": "Motorola PRO5100", "stock_inicial": 100, "modelos": [24], "en_uso": 0, "talleres": {"Aeroparque": _taller(0, 0, None), "Ezeiza": _taller(0, 0, None)}},
    {"id_repuesto": 62, "numero_parte": "", "nombre": "ANTENA", "descripcion": "Motorola PRO5100", "stock_inicial": 100, "modelos": [24], "en_uso": 0, "talleres": {"Aeroparque": _taller(0, 0, None), "Ezeiza": _taller(0, 0, None)}},
    {"id_repuesto": 63, "numero_parte": "", "nombre": "CARCAZA", "descripcion": "Motorola PRO5100", "stock_inicial": 100, "modelos": [24], "en_uso": 0, "talleres": {"Aeroparque": _taller(0, 0, None), "Ezeiza": _taller(0, 0, None)}},
    {"id_repuesto": 64, "numero_parte": "", "nombre": "BATERIA", "descripcion": "Motorola PRO5100", "stock_inicial": 100, "modelos": [24], "en_uso": 0, "talleres": {"Aeroparque": _taller(0, 0, None), "Ezeiza": _taller(0, 0, None)}},
    {"id_repuesto": 65, "numero_parte": "", "nombre": "SWITCH PTT", "descripcion": "Motorola PRO5100", "stock_inicial": 100, "modelos": [24], "en_uso": 0, "talleres": {"Aeroparque": _taller(0, 0, None), "Ezeiza": _taller(0, 0, None)}},
    {"id_repuesto": 66, "numero_parte": "", "nombre": "GOMA PTT", "descripcion": "Motorola PRO5100", "stock_inicial": 100, "modelos": [24], "en_uso": 0, "talleres": {"Aeroparque": _taller(0, 0, None), "Ezeiza": _taller(0, 0, None)}},
    {"id_repuesto": 67, "numero_parte": "", "nombre": "PLASTICO/BISEL PTT", "descripcion": "Motorola PRO5100", "stock_inicial": 100, "modelos": [24], "en_uso": 0, "talleres": {"Aeroparque": _taller(0, 0, None), "Ezeiza": _taller(0, 0, None)}},
    {"id_repuesto": 68, "numero_parte": "", "nombre": "CLIP DE CINTURA", "descripcion": "Motorola PRO5100", "stock_inicial": 100, "modelos": [24], "en_uso": 0, "talleres": {"Aeroparque": _taller(0, 0, None), "Ezeiza": _taller(0, 0, None)}},
    {"id_repuesto": 69, "numero_parte": "", "nombre": "PARLANTE", "descripcion": "Motorola PRO5100", "stock_inicial": 100, "modelos": [24], "en_uso": 0, "talleres": {"Aeroparque": _taller(0, 0, None), "Ezeiza": _taller(0, 0, None)}},
    {"id_repuesto": 70, "numero_parte": "", "nombre": "MICROFONO", "descripcion": "Motorola PRO5100", "stock_inicial": 100, "modelos": [24], "en_uso": 0, "talleres": {"Aeroparque": _taller(0, 0, None), "Ezeiza": _taller(0, 0, None)}},
    {"id_repuesto": 71, "numero_parte": "", "nombre": "DISPLAY", "descripcion": "Motorola PRO5100", "stock_inicial": 100, "modelos": [24], "en_uso": 0, "talleres": {"Aeroparque": _taller(0, 0, None), "Ezeiza": _taller(0, 0, None)}},
    {"id_repuesto": 72, "numero_parte": "", "nombre": "CONECTOR RF", "descripcion": "Motorola PRO5100", "stock_inicial": 100, "modelos": [24], "en_uso": 0, "talleres": {"Aeroparque": _taller(0, 0, None), "Ezeiza": _taller(0, 0, None)}},
]


# ═══════════════════════════════════════════════════════════
#  DIÁLOGO DE CANTIDAD (propio -> siempre visible)
# ═══════════════════════════════════════════════════════════
_ESTILO_DIALOGO = """
    QDialog { background-color: #eceff1; }
    QLabel { color: #263238; font-size: 11pt; }
    QSpinBox {
        border: 2px solid #cfd8dc; border-radius: 6px; padding: 6px;
        background-color: white; color: black; font-size: 12pt; min-height: 24px; }
    QSpinBox:focus { border: 2px solid #1976d2; }
"""


class DialogoCantidad(QDialog):
    """Pide una cantidad. Texto y botones siempre visibles."""

    def __init__(self, titulo, etiqueta, maximo=999999, color="#1976d2", parent=None):
        super().__init__(parent)
        self.setWindowTitle(titulo)
        self.setModal(True)
        self.setMinimumWidth(400)
        self.setStyleSheet(_ESTILO_DIALOGO)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(14)

        lbl = QLabel(etiqueta)
        lbl.setWordWrap(True)
        lbl.setFont(QFont("Arial", 11, QFont.Weight.Bold))
        layout.addWidget(lbl)

        self.spin = QSpinBox()
        self.spin.setRange(1, max(1, maximo))
        self.spin.setValue(1)
        self.spin.setFont(QFont("Arial", 13, QFont.Weight.Bold))
        self.spin.setFixedHeight(44)
        layout.addWidget(self.spin)

        fila = QHBoxLayout()
        fila.setSpacing(12)

        btn_cancelar = QPushButton("Cancelar")
        btn_cancelar.setFixedHeight(42)
        btn_cancelar.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_cancelar.setStyleSheet("""
            QPushButton { background-color: #757575; color: white; border: none;
                          border-radius: 8px; padding: 0 24px; font-weight: bold; font-size: 11pt; }
            QPushButton:hover { background-color: #616161; }
        """)
        btn_cancelar.clicked.connect(self.reject)
        fila.addWidget(btn_cancelar)

        btn_aceptar = QPushButton("Aceptar")
        btn_aceptar.setFixedHeight(42)
        btn_aceptar.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_aceptar.setDefault(True)
        btn_aceptar.setStyleSheet(f"""
            QPushButton {{ background-color: {color}; color: white; border: none;
                           border-radius: 8px; padding: 0 24px; font-weight: bold; font-size: 11pt; }}
            QPushButton:hover {{ background-color: #0d47a1; }}
        """)
        btn_aceptar.clicked.connect(self.accept)
        fila.addWidget(btn_aceptar)
        layout.addLayout(fila)

    def valor(self):
        return self.spin.value()


class DialogoAjusteStock(QDialog):
    """Forzar a mano el stock y fuera de servicio de cada taller + en uso."""

    def __init__(self, rep, parent=None):
        super().__init__(parent)
        self.setWindowTitle("✏️ Ajustar stock (forzar)")
        self.setModal(True)
        self.setMinimumWidth(440)
        self.setStyleSheet(_ESTILO_DIALOGO)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)

        titulo = QLabel(f"Ajuste manual de '{rep.get('nombre','')}'")
        titulo.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        titulo.setWordWrap(True)
        layout.addWidget(titulo)

        nota = QLabel("Escribí los valores exactos. Se guardan tal cual (forzado).")
        nota.setStyleSheet("color: #607d8b; font-size: 9pt;")
        layout.addWidget(nota)

        grid = QGridLayout()
        grid.setSpacing(8)
        for c, txt in enumerate(["Taller", "🟢 En stock", "🔴 Fuera de servicio"]):
            h = QLabel(txt)
            h.setFont(QFont("Arial", 10, QFont.Weight.Bold))
            grid.addWidget(h, 0, c)

        self.spins = {}   # taller -> (spin_stock, spin_fs)
        for fila, taller in enumerate(NOMBRES_TALLER_REAL, 1):
            lbl = QLabel(taller)
            lbl.setFont(QFont("Arial", 10, QFont.Weight.Bold))
            grid.addWidget(lbl, fila, 0)
            st = rep.get("talleres", {}).get(taller, {"stock_actual": 0, "fuera_servicio": 0})
            sp_s = QSpinBox(); sp_s.setRange(0, 999999); sp_s.setValue(int(st.get("stock_actual", 0) or 0))
            sp_f = QSpinBox(); sp_f.setRange(0, 999999); sp_f.setValue(int(st.get("fuera_servicio", 0) or 0))
            grid.addWidget(sp_s, fila, 1)
            grid.addWidget(sp_f, fila, 2)
            self.spins[taller] = (sp_s, sp_f)
        layout.addLayout(grid)

        fila_eu = QHBoxLayout()
        lbl_eu = QLabel("🔵 En uso (general):")
        lbl_eu.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        fila_eu.addWidget(lbl_eu)
        self.spin_en_uso = QSpinBox(); self.spin_en_uso.setRange(0, 999999)
        self.spin_en_uso.setValue(int(rep.get("en_uso", 0) or 0))
        fila_eu.addWidget(self.spin_en_uso, 1)
        layout.addLayout(fila_eu)

        botones = QHBoxLayout()
        botones.setSpacing(12)
        btn_c = QPushButton("Cancelar")
        btn_c.setFixedHeight(42)
        btn_c.setStyleSheet("QPushButton { background: #757575; color: white; border: none;"
                            " border-radius: 8px; padding: 0 24px; font-weight: bold; font-size: 11pt; }"
                            "QPushButton:hover { background: #616161; }")
        btn_c.clicked.connect(self.reject)
        botones.addWidget(btn_c)
        btn_a = QPushButton("Guardar ajuste")
        btn_a.setFixedHeight(42)
        btn_a.setDefault(True)
        btn_a.setStyleSheet("QPushButton { background: #1976d2; color: white; border: none;"
                            " border-radius: 8px; padding: 0 24px; font-weight: bold; font-size: 11pt; }"
                            "QPushButton:hover { background: #0d47a1; }")
        btn_a.clicked.connect(self.accept)
        botones.addWidget(btn_a)
        layout.addLayout(botones)

    def valores(self):
        """Devuelve ({taller: {'stock':x, 'fuera_servicio':y}}, en_uso)."""
        out = {}
        for taller, (sp_s, sp_f) in self.spins.items():
            out[taller] = {"stock": sp_s.value(), "fuera_servicio": sp_f.value()}
        return out, self.spin_en_uso.value()


# ═══════════════════════════════════════════════════════════
#  PESTAÑA
# ═══════════════════════════════════════════════════════════
class StockRepuestosTab(ApiTab):
    """Pestaña de Stock de Repuestos - AISLADA, estilo del sistema."""

    def __init__(self, api=None):
        super().__init__(api)
        self.api = api
        self.datos_completos = []
        self.datos_filtrados = []
        self.modelos = []
        self.repuesto_en_edicion = None

        self.crear_interfaz()
        self.cargar_datos()

    # ─────────────────────────────────────────────────────────
    #  CARGA DE DATOS
    # ─────────────────────────────────────────────────────────
    def cargar_datos(self):
        # Con backend: self.modelos = [(m['id_modelo'], f"{m['marca']} {m['modelo_equipo']}") ...]
        #self.modelos = list(MODELOS_EJEMPLO)
        try:
            datos = self.api.get("modelo_con_marca.php")
            self.modelos = [(m["id_modelo"], m["modelo_equipo"]) for m in datos]
            self.llenar_combo_modelos()
            self.llenar_lista_modelos()
        except SesionExpirada:
            # Este método corre dentro del __init__, cuando la ventana
            # principal todavía no existe. Por eso avisamos acá en vez
            # de delegar en self.window().
            QMessageBox.warning(self, "Sesión expirada",
                "Tu sesión venció. Cerrá y volvé a iniciar sesión.")
                
        except ApiError as e:
            QMessageBox.warning(self, "Error",
                f"No se pudieron cargar los datos de modelos:\n{e}")

        try:
            # Con backend: self.datos_completos = self.api.get("repuestos.php")
            #self.datos_completos = [self._clonar_repuesto(r) for r in REPUESTOS_EJEMPLO]
            self.datos_completos = []
            self.datos_completos = self.api.get("repuestos.php")
            #print(self.datos_completos)
            self.datos_filtrados = list(self.datos_completos)
            self.cargar_tabla()
        except SesionExpirada:
            # Este método corre dentro del __init__, cuando la ventana
            # principal todavía no existe. Por eso avisamos acá en vez
            # de delegar en self.window().
            QMessageBox.warning(self, "Sesión expirada",
                "Tu sesión venció. Cerrá y volvé a iniciar sesión.")
            self.datos_completos = []
            self.datos_filtrados = []
        
        except ApiError as e:
            QMessageBox.warning(self, "Error",
                f"No se pudieron cargar los datos de repuestos:\n{e}")
            self.datos_completos = []
            self.datos_filtrados = []

    def _clonar_repuesto(self, r):
        return {**r, "modelos": list(r["modelos"]),
                "talleres": {t: dict(v) for t, v in r["talleres"].items()}}

    # ─────────────────────────────────────────────────────────
    #  HELPERS
    # ─────────────────────────────────────────────────────────
    def _st(self, rep, taller):
        return rep.get("talleres", {}).get(
            taller, {"stock_actual": 0, "fuera_servicio": 0, "fecha_ingreso": None})

    def _total_stock(self, rep):
        talleres = rep.get("talleres", {})
        return sum(int(datos.get("stock_actual") or 0) for datos in talleres.values())

    def _total_fs(self, rep):
        talleres = rep.get("talleres", {})
        return sum(int(datos.get("fuera_servicio") or 0) for datos in talleres.values())

    def _en_uso(self, rep):
        return int(rep.get("en_uso", 0) or 0)

    def _total_general(self, rep):
        return self._total_stock(rep) + self._en_uso(rep) + self._total_fs(rep)

    def _ultima_fecha(self, rep):
        talleres = rep.get("talleres", {})
        fechas = [datos.get("fecha_ingreso") for datos in talleres.values()]
        fechas = [f for f in fechas if f]
        return max(fechas) if fechas else None

    def _nombre_modelo(self, id_modelo):
        for _id, nombre in self.modelos:
            if _id == id_modelo:
                return nombre
        return str(id_modelo)

    def _compat_text(self, ids):
        """Compatibilidad agrupada por marca: 'MOTOROLA DEP450, EP450 · ICOM IC-A120, IC-A110'."""
        grupos = {}
        orden = []
        for mid in ids or []:
            marca = MODELO_MARCA.get(mid, "")
            corto = MODELO_CORTO.get(mid) or self._nombre_modelo(mid)
            if marca not in grupos:
                grupos[marca] = []
                orden.append(marca)
            grupos[marca].append(corto)
        partes = [f"{m} " + ", ".join(grupos[m]) if m else ", ".join(grupos[m])
                  for m in orden]
        return "  ·  ".join(partes)

    def _actualizar_compat_form(self):
        """Refresca la etiqueta 'Compatible con' según los modelos tildados."""
        txt = self._compat_text(self._modelos_marcados())
        self.lbl_compat.setText("🔗 Compatible con: " + (txt if txt else "—"))

    def _nombre_real_taller(self, taller_corto):
        """Traduce 'Aeroparque'/'Ezeiza' al nombre real que usa la base."""
        return NOMBRES_TALLER_REAL.get(taller_corto, taller_corto)

    # ─────────────────────────────────────────────────────────
    #  INTERFAZ
    # ─────────────────────────────────────────────────────────
    def crear_interfaz(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(8)

        header = QLabel("🔧 STOCK DE REPUESTOS")
        header.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        header.setAlignment(Qt.AlignmentFlag.AlignCenter)
        header.setFixedHeight(38)
        header.setStyleSheet("""
            QLabel { background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                        stop:0 #1565c0, stop:1 #1976d2);
                     color: white; padding: 5px; border-radius: 8px;
                     border: 2px solid #0d47a1; }
        """)
        layout.addWidget(header)

        contenido = QHBoxLayout()
        contenido.setSpacing(10)
        contenido.addWidget(self.crear_columna_izquierda(), 42)
        contenido.addWidget(self.crear_columna_derecha(), 58)
        layout.addLayout(contenido, 1)
        self.setLayout(layout)

    # ---------- Columna izquierda ----------
    def crear_columna_izquierda(self):
        col_frame = QFrame()
        col_frame.setStyleSheet("""
            QFrame { background-color: white; border-radius: 10px;
                     border: 2px solid #cfd8dc; color: black; }
        """)
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(6)

        estilo_input = """
            QLineEdit, QComboBox, QSpinBox {
                border: 2px solid #cfd8dc; border-radius: 5px; padding: 3px;
                min-height: 22px; font-size: 9pt; background-color: white; color: black; }
            QLineEdit:focus, QComboBox:focus, QSpinBox:focus { border: 2px solid #1976d2; }
            QComboBox::drop-down { border: none; width: 30px; }
            QComboBox::down-arrow { image: none; border-left: 5px solid transparent;
                border-right: 5px solid transparent; border-top: 7px solid #37474f;
                margin-right: 8px; }
        """
        estilo_label = "color: #37474f; font-weight: bold; font-size: 9pt;"

        titulo = QLabel("🔧 Datos del Repuesto")
        titulo.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        titulo.setStyleSheet("color: #1976d2;")
        main_layout.addWidget(titulo)

        campos_frame = QFrame()
        campos_frame.setStyleSheet("""
            QFrame { background-color: #fafafa; border: 2px solid #e0e0e0;
                     border-radius: 8px; padding: 5px; }
        """)
        grid = QGridLayout()
        grid.setSpacing(4)
        grid.setColumnStretch(1, 1)

        lbl_np = QLabel("🔩 N° de parte:")
        lbl_np.setStyleSheet(estilo_label)
        grid.addWidget(lbl_np, 0, 0)
        self.input_numero_parte = QLineEdit()
        self.input_numero_parte.setPlaceholderText("Ej: FUE-YED-138")
        self.input_numero_parte.setStyleSheet(estilo_input)
        grid.addWidget(self.input_numero_parte, 0, 1)

        lbl_nom = QLabel("🏷️ Nombre:")
        lbl_nom.setStyleSheet(estilo_label)
        grid.addWidget(lbl_nom, 1, 0)
        self.input_nombre = QLineEdit()
        self.input_nombre.setPlaceholderText("Ej: FUENTE YEDRO 13,8V")
        self.input_nombre.setStyleSheet(estilo_input)
        grid.addWidget(self.input_nombre, 1, 1)

        lbl_ini = QLabel("📦 Stock inicial Aerop.:")
        lbl_ini.setStyleSheet(estilo_label)
        grid.addWidget(lbl_ini, 2, 0)
        self.spin_stock_aep = QSpinBox()
        self.spin_stock_aep.setRange(0, 999999)
        self.spin_stock_aep.setStyleSheet(estilo_input)
        grid.addWidget(self.spin_stock_aep, 2, 1)

        lbl_ini2 = QLabel("📦 Stock inicial Ezeiza:")
        lbl_ini2.setStyleSheet(estilo_label)
        grid.addWidget(lbl_ini2, 3, 0)
        self.spin_stock_eze = QSpinBox()
        self.spin_stock_eze.setRange(0, 999999)
        self.spin_stock_eze.setStyleSheet(estilo_input)
        grid.addWidget(self.spin_stock_eze, 3, 1)

        campos_frame.setLayout(grid)
        main_layout.addWidget(campos_frame)

        # ── Modelos vinculados ──
        titulo_mod = QLabel("📻 Modelos vinculados")
        titulo_mod.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        titulo_mod.setStyleSheet("color: #1976d2;")
        main_layout.addWidget(titulo_mod)

        self.lista_modelos = QListWidget()
        self.lista_modelos.setStyleSheet("""
            QListWidget { border: 2px solid #cfd8dc; border-radius: 8px;
                          background-color: white; font-size: 9pt; color: black; }
            QListWidget::item { padding: 3px; }
            QListWidget::item:selected { background-color: #bbdefb; color: #0d47a1; }
            QListWidget::indicator {
                width: 16px; height: 16px; border: 2px solid #90a4ae;
                border-radius: 3px; background-color: white; }
            QListWidget::indicator:hover { border: 2px solid #1976d2; }
            QListWidget::indicator:checked {
                background-color: #1976d2; border: 2px solid #1976d2; }
        """)
        # Selección múltiple para borrar varios modelos de una (Ctrl/Shift + clic)
        self.lista_modelos.setSelectionMode(
            QAbstractItemView.SelectionMode.ExtendedSelection)
        # Alto mínimo para que la lista siga siendo usable dentro del scroll (1366x768)
        self.lista_modelos.setMinimumHeight(140)
        main_layout.addWidget(self.lista_modelos, 2)

        # Botones provisorios sobre la lista de modelos
        fila_mod = QHBoxLayout()
        fila_mod.setSpacing(4)
        btn_act_modelos = self._boton("🔄 Actualizar lista", "#1976d2", "#1565c0")
        btn_act_modelos.clicked.connect(self.actualizar_modelos)
        fila_mod.addWidget(btn_act_modelos)
        btn_borrar_modelo = self._boton("🗑️ Borrar seleccionados", "#8d6e63", "#6d4c41")
        btn_borrar_modelo.clicked.connect(self.borrar_modelo_lista)
        fila_mod.addWidget(btn_borrar_modelo)
        main_layout.addLayout(fila_mod)

        # Compatibilidad (auto): marca una vez + sus modelos. Reemplaza a la descripción.
        self.lbl_compat = QLabel("🔗 Compatible con: —")
        self.lbl_compat.setWordWrap(True)
        self.lbl_compat.setStyleSheet(
            "color: #37474f; background: #e8f5e9; border: 1px solid #a5d6a7;"
            " border-radius: 6px; padding: 5px; font-size: 9pt;")
        main_layout.addWidget(self.lbl_compat)
        self.lista_modelos.itemChanged.connect(lambda *_: self._actualizar_compat_form())

        # ── Estado del repuesto seleccionado ──
        titulo_stock = QLabel("📊 Estado (repuesto seleccionado)")
        titulo_stock.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        titulo_stock.setStyleSheet("color: #1976d2;")
        main_layout.addWidget(titulo_stock)

        self.frame_estado = QFrame()
        self.frame_estado.setStyleSheet("""
            QFrame { background-color: #fafafa; border: 2px solid #e0e0e0;
                     border-radius: 8px; padding: 6px; }
        """)
        estado_grid = QGridLayout()
        estado_grid.setSpacing(4)
        for c, txt in enumerate(["Taller", "🟢 En stock", "🔴 Fuera serv.", "📅 Últ. ingreso"]):
            h = QLabel(txt)
            h.setFont(QFont("Arial", 8, QFont.Weight.Bold))
            h.setStyleSheet("color: #37474f;")
            estado_grid.addWidget(h, 0, c)

        self.lbls_taller = {}
        for fila, taller in enumerate(TALLERES, 1):
            lbl_t = QLabel(taller)
            lbl_t.setFont(QFont("Arial", 9, QFont.Weight.Bold))
            lbl_t.setStyleSheet("color: #1565c0;")
            estado_grid.addWidget(lbl_t, fila, 0)

            lbl_s = QLabel("-")
            lbl_s.setFont(QFont("Arial", 11, QFont.Weight.Bold))
            lbl_s.setStyleSheet("color: #2e7d32;")
            lbl_s.setAlignment(Qt.AlignmentFlag.AlignCenter)
            estado_grid.addWidget(lbl_s, fila, 1)

            lbl_fs = QLabel("-")
            lbl_fs.setFont(QFont("Arial", 11, QFont.Weight.Bold))
            lbl_fs.setStyleSheet("color: #c62828;")
            lbl_fs.setAlignment(Qt.AlignmentFlag.AlignCenter)
            estado_grid.addWidget(lbl_fs, fila, 2)

            lbl_f = QLabel("-")
            lbl_f.setFont(QFont("Arial", 8))
            lbl_f.setStyleSheet("color: #546e7a;")
            estado_grid.addWidget(lbl_f, fila, 3)
            self.lbls_taller[taller] = (lbl_s, lbl_fs, lbl_f)

        self.frame_estado.setLayout(estado_grid)
        main_layout.addWidget(self.frame_estado)

        # Totales generales (en uso + total)
        self.lbl_totales = QLabel("🔵 En uso: -    •    Σ Total: -")
        self.lbl_totales.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        self.lbl_totales.setStyleSheet("color: #0d47a1;")
        self.lbl_totales.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(self.lbl_totales)

        # ── Operaciones ──
        oper_layout = QHBoxLayout()
        lbl_op_taller = QLabel("Operar en taller:")
        lbl_op_taller.setStyleSheet(estilo_label)
        oper_layout.addWidget(lbl_op_taller)
        self.combo_taller_oper = QComboBox()
        self.combo_taller_oper.addItems(NOMBRES_TALLER_REAL)
        self.combo_taller_oper.setStyleSheet(estilo_input)
        oper_layout.addWidget(self.combo_taller_oper, 1)
        main_layout.addLayout(oper_layout)

        oper_grid = QGridLayout()
        oper_grid.setSpacing(4)
        btn_ingreso = self._boton("📥 Registrar ingreso", "#f57c00", "#e65100")
        btn_ingreso.clicked.connect(self.registrar_ingreso)
        oper_grid.addWidget(btn_ingreso, 0, 0)

        btn_usar = self._boton("🔧 Usar en equipo", "#1976d2", "#1565c0")
        btn_usar.clicked.connect(self.usar_en_equipo)
        oper_grid.addWidget(btn_usar, 0, 1)

        btn_fs = self._boton("🔴 Fuera de servicio", "#8e24aa", "#6a1b9a")
        btn_fs.clicked.connect(self.marcar_fuera_servicio)
        oper_grid.addWidget(btn_fs, 1, 0)

        btn_reparar = self._boton("♻️ Reparar (vuelve a stock)", "#00897b", "#00695c")
        btn_reparar.clicked.connect(self.reparar_repuesto)
        oper_grid.addWidget(btn_reparar, 1, 1)

        btn_descartar = self._boton("🗑️ Descartar F/S", "#546e7a", "#37474f")
        btn_descartar.clicked.connect(self.descartar_fuera_servicio)
        oper_grid.addWidget(btn_descartar, 2, 0)

        btn_ajustar = self._boton("✏️ Ajustar stock (forzar)", "#5e35b1", "#4527a0")
        btn_ajustar.clicked.connect(self.ajustar_stock)
        oper_grid.addWidget(btn_ajustar, 2, 1)
        main_layout.addLayout(oper_grid)

        # ── Catálogo ──
        cat_grid = QGridLayout()
        cat_grid.setSpacing(4)
        btn_guardar = self._boton("💾 Guardar nuevo", "#27ae60", "#1e8449")
        btn_guardar.clicked.connect(self.guardar_repuesto)
        cat_grid.addWidget(btn_guardar, 0, 0)

        btn_modificar = self._boton("📝 Modificar", "#1976d2", "#1565c0")
        btn_modificar.clicked.connect(self.modificar_repuesto)
        cat_grid.addWidget(btn_modificar, 0, 1)

        btn_borrar = self._boton("🧹 Borrar campos", "#757575", "#616161")
        btn_borrar.clicked.connect(self.borrar_campos)
        cat_grid.addWidget(btn_borrar, 1, 0)

        btn_baja = self._boton("❌ Dar de baja", "#c62828", "#b71c1c")
        btn_baja.clicked.connect(self.baja_repuesto)
        cat_grid.addWidget(btn_baja, 1, 1)
        main_layout.addLayout(cat_grid)

        btn_exportar = self._boton("📤 Exportar a SQL (migración)", "#00695c", "#004d40")
        btn_exportar.clicked.connect(self.exportar_sql)
        main_layout.addWidget(btn_exportar)

        # Botón provisorio: borrar TODOS los repuestos para empezar de cero
        btn_borrar_todos = self._boton("🧨 Borrar TODOS los repuestos (empezar de 0)",
                                       "#b71c1c", "#8e0000")
        btn_borrar_todos.clicked.connect(self.borrar_todos_repuestos)
        main_layout.addWidget(btn_borrar_todos)

        col_frame.setLayout(main_layout)

        # En 1366x768 la columna izquierda es más alta que la pantalla, así que
        # la metemos en un scroll vertical para que TODOS los combos, casilleros
        # y botones sean accesibles (bajando con la rueda / barra).
        scroll_izq = QScrollArea()
        scroll_izq.setWidgetResizable(True)
        scroll_izq.setFrameShape(QFrame.Shape.NoFrame)
        scroll_izq.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll_izq.setStyleSheet("""
            QScrollArea { background: transparent; border: none; }
            QScrollBar:vertical { border: none; background: #eceff1; width: 12px;
                                  margin: 0; border-radius: 6px; }
            QScrollBar::handle:vertical { background: #78909c; min-height: 30px; border-radius: 6px; }
            QScrollBar::handle:vertical:hover { background: #1976d2; }
            QScrollBar::sub-line:vertical, QScrollBar::add-line:vertical { height: 0; }
        """)
        scroll_izq.setWidget(col_frame)
        return scroll_izq

    def _boton(self, texto, color, color_hover):
        btn = QPushButton(texto)
        btn.setFixedHeight(30)
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.setStyleSheet(f"""
            QPushButton {{ background-color: {color}; color: white; border-radius: 5px;
                           padding: 0 8px; font-weight: bold; font-size: 8pt; }}
            QPushButton:hover {{ background-color: {color_hover}; }}
            QPushButton:disabled {{ background-color: #cfd8dc; color: #90a4ae; }}
        """)
        return btn

    # ---------- Columna derecha TABLA REPUESTOS (VISTA) ----------
    def crear_columna_derecha(self):
        col_frame = QFrame()
        col_frame.setStyleSheet("""
            QFrame { background-color: white; border-radius: 10px;
                     border: 2px solid #cfd8dc; color: black; }
        """)
        layout = QVBoxLayout()
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(8)

        titulo_tabla = QLabel("📋 Repuestos Registrados")
        titulo_tabla.setFont(QFont("Arial", 13, QFont.Weight.Bold))
        titulo_tabla.setStyleSheet("color: #1976d2;")
        layout.addWidget(titulo_tabla)

        # Búsqueda
        busqueda_layout = QHBoxLayout()
        lbl_buscar = QLabel("🔍 Buscar:")
        lbl_buscar.setFont(QFont("Arial", 9, QFont.Weight.Bold))
        lbl_buscar.setStyleSheet("color: #37474f;")
        busqueda_layout.addWidget(lbl_buscar)

        self.input_buscar = QLineEdit()
        self.input_buscar.setPlaceholderText("N° de parte, nombre o descripción...")
        self.input_buscar.setFixedHeight(30)
        self.input_buscar.setStyleSheet("""
            QLineEdit { border: 2px solid #cfd8dc; border-radius: 6px; padding: 5px;
                        background-color: white; color: black; }
            QLineEdit:focus { border: 2px solid #1976d2; }
        """)
        self.input_buscar.textChanged.connect(self.aplicar_filtros)
        busqueda_layout.addWidget(self.input_buscar)

        btn_limpiar = QPushButton("🗑️ Limpiar")
        btn_limpiar.setFixedHeight(30)
        btn_limpiar.setStyleSheet("""
            QPushButton { background-color: #757575; color: white; border-radius: 6px;
                          padding: 0 12px; font-weight: bold; font-size: 9pt; }
            QPushButton:hover { background-color: #616161; }
        """)
        btn_limpiar.clicked.connect(self.limpiar_filtros)
        busqueda_layout.addWidget(btn_limpiar)
        layout.addLayout(busqueda_layout)

        # Filtros
        filtros_layout = QHBoxLayout()
        lbl_filtros = QLabel("Filtros:")
        lbl_filtros.setFont(QFont("Arial", 9, QFont.Weight.Bold))
        lbl_filtros.setStyleSheet("color: black;")
        filtros_layout.addWidget(lbl_filtros)

        estilo_combo = """
            QComboBox { border: 2px solid #cfd8dc; border-radius: 5px; padding: 4px;
                        min-width: 90px; background-color: white; font-size: 9pt; color: black; }
            QComboBox:hover { border: 2px solid #1976d2; }
        """

        lbl_tall = QLabel("Taller:")
        lbl_tall.setStyleSheet("color: black;")
        filtros_layout.addWidget(lbl_tall)
        self.combo_filtro_taller = QComboBox()
        self.combo_filtro_taller.addItem("Ambos")
        self.combo_filtro_taller.addItems(NOMBRES_TALLER_REAL)
        self.combo_filtro_taller.setFixedHeight(26)
        self.combo_filtro_taller.setStyleSheet(estilo_combo)
        self.combo_filtro_taller.currentTextChanged.connect(self.aplicar_filtros)
        filtros_layout.addWidget(self.combo_filtro_taller)

        lbl_mod = QLabel("Modelo:")
        lbl_mod.setStyleSheet("color: black;")
        filtros_layout.addWidget(lbl_mod)
        self.combo_filtro_modelo = QComboBox()
        self.combo_filtro_modelo.setFixedHeight(26)
        self.combo_filtro_modelo.setStyleSheet(estilo_combo)
        self.combo_filtro_modelo.currentTextChanged.connect(self.aplicar_filtros)
        filtros_layout.addWidget(self.combo_filtro_modelo)

        lbl_stock = QLabel("Estado:")
        lbl_stock.setStyleSheet("color: black;")
        filtros_layout.addWidget(lbl_stock)
        self.combo_filtro_stock = QComboBox()
        self.combo_filtro_stock.addItems(
            ["Todos", "Stock bajo", "Sin stock", "Con stock", "En uso", "Con fuera de servicio"])
        self.combo_filtro_stock.setFixedHeight(26)
        self.combo_filtro_stock.setStyleSheet(estilo_combo)
        self.combo_filtro_stock.currentTextChanged.connect(self.aplicar_filtros)
        filtros_layout.addWidget(self.combo_filtro_stock)

        filtros_layout.addStretch()
        layout.addLayout(filtros_layout)

        self.crear_tabla()
        layout.addWidget(self.tabla, 1)

        self.frame_resumen = QFrame()
        self.frame_resumen.setStyleSheet("""
            QFrame { background-color: #fafafa; border: 2px solid #e0e0e0;
                     border-radius: 8px; padding: 8px; }
        """)
        resumen_layout = QVBoxLayout()
        resumen_layout.setContentsMargins(10, 5, 10, 5)
        resumen_layout.setSpacing(2)
        self.lbl_resumen = QLabel("")
        self.lbl_resumen.setFont(QFont("Arial", 9, QFont.Weight.Bold))
        self.lbl_resumen.setStyleSheet("color: #37474f;")
        self.lbl_resumen.setWordWrap(True)
        resumen_layout.addWidget(self.lbl_resumen)
        self.frame_resumen.setLayout(resumen_layout)
        layout.addWidget(self.frame_resumen)

        col_frame.setLayout(layout)
        return col_frame

    def crear_tabla(self):
        self.tabla = QTableWidget()
        self.columnas = [
            "N°", "ID", "N° de parte", "Nombre", "Compatible con",
            "🟢 Aerop.", "🔴 Aerop.", "🟢 Ezeiza", "🔴 Ezeiza",
            "🔵 En uso", "Σ Total", "Último ingreso",
        ]
        self.tabla.setColumnCount(len(self.columnas))
        self.tabla.setHorizontalHeaderLabels(self.columnas)
        self.tabla.hideColumn(1)
        self.tabla.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.tabla.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.tabla.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.tabla.setAlternatingRowColors(True)
        self.tabla.setStyleSheet("""
            QTableWidget { border: 2px solid #cfd8dc; border-radius: 8px;
                           background-color: white; font-size: 9pt; color: black; }
            QTableWidget::item { padding: 4px; color: black; }
            QTableWidget::item:selected { background-color: #bbdefb; color: #0d47a1; }
            QTableWidget::item:alternate { background-color: #f5f5f5; }
            QHeaderView::section { background-color: #78909c; color: white; padding: 6px;
                                   font-weight: bold; font-size: 9pt; border: none;
                                   border-right: 1px solid #607d8b; }
            QHeaderView::section:last { border-right: none; }
        """)
        # Columnas: se auto-ajustan al contenido la primera vez, pero quedan
        # en modo Interactive para que el usuario las pueda redimensionar a mano
        # (o doble clic en el borde del encabezado para volver a auto-ajustar).
        header = self.tabla.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        header.setStretchLastSection(False)
        self._columnas_ajustadas = False
        self.tabla.verticalHeader().setDefaultSectionSize(32)
        self.tabla.setHorizontalScrollMode(QAbstractItemView.ScrollMode.ScrollPerPixel)
        self.tabla.itemSelectionChanged.connect(self.on_seleccion_cambiada)
        self.tabla.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.tabla.customContextMenuRequested.connect(
            lambda pos: self.mostrar_menu_contextual(self.tabla, pos))

    # ─────────────────────────────────────────────────────────
    #  COMBOS / LISTAS
    # ─────────────────────────────────────────────────────────
    def llenar_combo_modelos(self):
        self.combo_filtro_modelo.blockSignals(True)
        self.combo_filtro_modelo.clear()
        self.combo_filtro_modelo.addItem("Todos")
        for _id, nombre in self.modelos:
            self.combo_filtro_modelo.addItem(nombre, _id)
        self.combo_filtro_modelo.blockSignals(False)

    def llenar_lista_modelos(self):
        self.lista_modelos.clear()
        for _id, nombre in self.modelos:
            item = QListWidgetItem(nombre)
            item.setFlags(item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
            item.setCheckState(Qt.CheckState.Unchecked)
            item.setData(Qt.ItemDataRole.UserRole, _id)
            self.lista_modelos.addItem(item)

    def _modelos_marcados(self):
        ids = []
        for i in range(self.lista_modelos.count()):
            item = self.lista_modelos.item(i)
            if item.checkState() == Qt.CheckState.Checked:
                ids.append(item.data(Qt.ItemDataRole.UserRole))
        return ids

    def _marcar_modelos(self, ids):
        ids = set(ids or [])
        for i in range(self.lista_modelos.count()):
            item = self.lista_modelos.item(i)
            _id = item.data(Qt.ItemDataRole.UserRole)
            item.setCheckState(
                Qt.CheckState.Checked if _id in ids else Qt.CheckState.Unchecked)

    # ─────────────────────────────────────────────────────────
    #  BORRADOS PROVISORIOS (para la carga inicial)
    # ─────────────────────────────────────────────────────────
    def borrar_modelo_lista(self):
        """Borra de la lista los modelos resaltados. Provisorio.
        Se pueden elegir varios con Ctrl/Shift + clic."""
        items = self.lista_modelos.selectedItems()
        if not items:
            QMessageBox.warning(
                self, "⚠️ Sin selección",
                "Resaltá uno o varios modelos de la lista (Ctrl/Shift + clic para varios) "
                "y después borralos. No hace falta tildar la casilla, solo resaltar la fila.")
            return
        ids = [it.data(Qt.ItemDataRole.UserRole) for it in items]
        nombres = [it.text() for it in items]
        idset = set(ids)
        usados = sum(1 for r in self.datos_completos
                     if any(m in idset for m in r.get("modelos", [])))
        muestra = ", ".join(nombres[:6]) + (f"  …(+{len(nombres) - 6})" if len(nombres) > 6 else "")
        resp = QMessageBox.question(
            self, "🗑️ Borrar modelos de la lista",
            f"¿Borrar {len(ids)} modelo(s) de la lista?\n\n{muestra}\n\n"
            + (f"Están vinculados a {usados} repuesto(s); se desvincularán.\n\n" if usados else "")
            + "Es solo para la carga inicial provisoria (no toca tu base de datos).",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if resp != QMessageBox.StandardButton.Yes:
            return
        # quitar de la lista de modelos
        self.modelos = [(mid, n) for mid, n in self.modelos if mid not in idset]
        # desvincular de todos los repuestos
        for r in self.datos_completos:
            r["modelos"] = [m for m in r.get("modelos", []) if m not in idset]
        # refrescar combos y lista, manteniendo el repuesto seleccionado
        self.llenar_combo_modelos()
        self.llenar_lista_modelos()
        rep = self._repuesto_actual()
        if rep is not None:
            self._marcar_modelos(rep.get("modelos", []))
        self.aplicar_filtros()

    def actualizar_modelos(self):
        """Re-lee el listado de modelos vinculables.
        • Con API conectada: los trae de la base (aparecen los agregados después).
        • En modo provisorio (standalone): recarga la lista base (restaura los borrados)."""
        nuevos = None
        if self.api is not None:
            try:
                # Con backend real. Se espera [{id_modelo, marca, modelo_equipo}, ...].
                data = self.api.get("modelos.php")
                nuevos = []
                for m in data:
                    nombre = f"{m.get('marca', '')} {m.get('modelo_equipo', m.get('modelo', ''))}".strip()
                    nuevos.append((m.get("id_modelo"), nombre))
            except Exception as e:
                QMessageBox.warning(self, "Error",
                                    f"No se pudo actualizar desde la base:\n{e}")
                return
        if nuevos is None:
            nuevos = list(MODELOS_EJEMPLO)   # provisorio: fuente embebida

        # conservar el orden alfabético por nombre
        self.modelos = sorted(nuevos, key=lambda x: (x[1] or "").upper())
        self.llenar_combo_modelos()
        self.llenar_lista_modelos()
        rep = self._repuesto_actual()
        if rep is not None:
            self._marcar_modelos(rep.get("modelos", []))
        QMessageBox.information(self, "✅ Actualizado",
                               f"Lista de modelos actualizada ({len(self.modelos)} modelos).")

    def borrar_todos_repuestos(self):
        """Vacía la tabla de repuestos para empezar de cero. Provisorio."""
        if not self.datos_completos:
            QMessageBox.information(self, "Info", "No hay repuestos para borrar.")
            return
        resp = QMessageBox.question(
            self, "🧨 Borrar TODOS los repuestos",
            f"¿Borrar los {len(self.datos_completos)} repuestos registrados y empezar de cero?\n\n"
            "Esto NO toca tu base de datos: solo limpia esta tab provisoria.\n"
            "Los modelos de la lista se conservan.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if resp != QMessageBox.StandardButton.Yes:
            return
        self.datos_completos = []
        self.datos_filtrados = []
        self.borrar_campos()
        self.aplicar_filtros()
    # ─────────────────────────────────────────────────────────
    #  TABLA
    # ─────────────────────────────────────────────────────────
    def cargar_tabla(self):
        self.tabla.setRowCount(len(self.datos_filtrados))
        for fila, rep in enumerate(self.datos_filtrados):
            total_stock = self._total_stock(rep)
            en_uso = self._en_uso(rep)
            total_general = self._total_general(rep)
            
            item_orden = QTableWidgetItem(str(fila + 1))
            item_orden.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            item_orden.setFont(QFont("Arial", 9, QFont.Weight.Bold))
            if total_stock == 0:
                color = QColor("#b71c1c")
            elif total_stock <= UMBRAL_BAJO:
                color = QColor("#f57c00")
            else:
                color = QColor("#2e7d32")
            item_orden.setBackground(QBrush(color))
            item_orden.setForeground(QBrush(QColor("white")))
            self.tabla.setItem(fila, 0, item_orden)

            ae = self._st(rep, NOMBRES_TALLER_REAL["Aeroparque"])
            ez = self._st(rep, NOMBRES_TALLER_REAL["Ezeiza"])
            valores = [
                str(rep.get("id_repuesto", "")),
                rep.get("numero_parte", "") or "-",
                rep.get("nombre", "") or "-",
                self._compat_text(rep.get("modelos", [])) or "-",
                str(int(ae["stock_actual"] or 0)),
                str(int(ae["fuera_servicio"] or 0)),
                str(int(ez["stock_actual"] or 0)),
                str(int(ez["fuera_servicio"] or 0)),
                str(en_uso),
                str(total_general),
                self._formatear_fecha(self._ultima_fecha(rep)),
            ]
            for col, valor in enumerate(valores, 1):
                item = QTableWidgetItem(str(valor))
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                item.setFont(QFont("Arial", 9))
                if col in (6, 8) and valor not in ("0", "-"):   # F/S por taller
                    item.setForeground(QBrush(QColor("#c62828")))
                    item.setFont(QFont("Arial", 9, QFont.Weight.Bold))
                if col == 9:   # en uso
                    item.setForeground(QBrush(QColor("#0d47a1")))
                    item.setFont(QFont("Arial", 9, QFont.Weight.Bold))
                if col == 10:  # total
                    item.setFont(QFont("Arial", 9, QFont.Weight.Bold))
                self.tabla.setItem(fila, col, item)

        # Auto-ajuste de ancho SOLO la primera carga; después respeta lo que
        # el usuario haya redimensionado a mano.
        if not getattr(self, "_columnas_ajustadas", False):
            self.tabla.resizeColumnsToContents()
            self._columnas_ajustadas = True

        self.actualizar_resumen()

    def _formatear_fecha(self, fecha):
        if not fecha:
            return "-"
        try:
            dt = datetime.strptime(str(fecha)[:19], "%Y-%m-%d %H:%M:%S")
            return dt.strftime("%d/%m/%Y")   # solo fecha, sin hora
        except (ValueError, TypeError):
            return str(fecha)

    def actualizar_resumen(self):
        total = len(self.datos_completos)
        en_stock = sum(self._total_stock(r) for r in self.datos_completos)
        en_uso = sum(self._en_uso(r) for r in self.datos_completos)
        fs = sum(self._total_fs(r) for r in self.datos_completos)
        bajos = sum(1 for r in self.datos_completos if 0 < self._total_stock(r) <= UMBRAL_BAJO)
        sin = sum(1 for r in self.datos_completos if self._total_stock(r) == 0)

        por_taller = []
        #talleres = rep.get("talleres", {})
        for t in NOMBRES_TALLER_REAL:
            n = sum(int(self._st(r, t)["stock_actual"] or 0) for r in self.datos_completos)
            f = sum(int(self._st(r, t)["fuera_servicio"] or 0) for r in self.datos_completos)
            por_taller.append(f"{t}: {n} 🟢 / {f} 🔴")

        self.lbl_resumen.setText(
            f"📦 {total} repuestos  •  🟢 {en_stock} en stock  •  🔵 {en_uso} en uso  •  "
            f"🔴 {fs} fuera de servicio  •  Σ {en_stock + en_uso + fs} en total   "
            f"(mostrando {len(self.datos_filtrados)})\n"
            f"⚠️ {bajos} con stock bajo  •  ❌ {sin} sin stock   —   "
            f"Por taller →  " + "     ".join(por_taller))

    # ─────────────────────────────────────────────────────────
    #  FILTROS
    # ─────────────────────────────────────────────────────────
    def _stock_segun_filtro(self, rep):
        t = self.combo_filtro_taller.currentText()
        if t in NOMBRES_TALLER_REAL:
            return int(self._st(rep, t)["stock_actual"] or 0)
        return self._total_stock(rep)

    def _fs_segun_filtro(self, rep):
        t = self.combo_filtro_taller.currentText()
        if t in NOMBRES_TALLER_REAL:
            return int(self._st(rep, t)["fuera_servicio"] or 0)
        return self._total_fs(rep)

    def aplicar_filtros(self):
        datos = list(self.datos_completos)
        texto = self.input_buscar.text().strip().upper()
        if texto:
            datos = [r for r in datos if
                     texto in str(r.get("numero_parte", "")).upper()
                     or texto in str(r.get("nombre", "")).upper()
                     or texto in self._compat_text(r.get("modelos", [])).upper()]
        if self.combo_filtro_modelo.currentIndex() > 0:
            id_modelo = self.combo_filtro_modelo.currentData()
            datos = [r for r in datos if id_modelo in r.get("modelos", [])]
        estado = self.combo_filtro_stock.currentText()
        if estado == "Stock bajo":
            datos = [r for r in datos if 0 < self._stock_segun_filtro(r) <= UMBRAL_BAJO]
        elif estado == "Sin stock":
            datos = [r for r in datos if self._stock_segun_filtro(r) == 0]
        elif estado == "Con stock":
            datos = [r for r in datos if self._stock_segun_filtro(r) > 0]
        elif estado == "En uso":
            datos = [r for r in datos if self._en_uso(r) > 0]
        elif estado == "Con fuera de servicio":
            datos = [r for r in datos if self._fs_segun_filtro(r) > 0]
        self.datos_filtrados = datos
        self.cargar_tabla()

    def limpiar_filtros(self):
        self.input_buscar.clear()
        self.combo_filtro_taller.setCurrentIndex(0)
        self.combo_filtro_modelo.setCurrentIndex(0)
        self.combo_filtro_stock.setCurrentIndex(0)
        self.datos_filtrados = list(self.datos_completos)
        self.cargar_tabla()

    # ─────────────────────────────────────────────────────────
    #  SELECCIÓN
    # ─────────────────────────────────────────────────────────
    def on_seleccion_cambiada(self):
        fila = self.tabla.currentRow()
        if 0 <= fila < len(self.datos_filtrados):
            rep = self.datos_filtrados[fila]
            self.repuesto_en_edicion = rep.get("id_repuesto")
            self.input_numero_parte.setText(rep.get("numero_parte", "") or "")
            self.input_nombre.setText(rep.get("nombre", "") or "")
            self._actualizar_compat_form()
            self.spin_stock_aep.setValue(int(self._st(rep, NOMBRES_TALLER_REAL["Aeroparque"])["stock_actual"] or 0))
            self.spin_stock_eze.setValue(int(self._st(rep, NOMBRES_TALLER_REAL["Ezeiza"])["stock_actual"] or 0))
            self._marcar_modelos(rep.get("modelos", []))
            self._refrescar_estado(rep)
        else:
            self.repuesto_en_edicion = None
            self._refrescar_estado(None)

    def _repuesto_actual(self):
        """Devuelve el repuesto de la fila seleccionada en la tabla, o None."""
        fila = self.tabla.currentRow()
        if 0 <= fila < len(self.datos_filtrados):
            return self.datos_filtrados[fila]
        return None

    def _refrescar_estado(self, rep):
        for taller, (lbl_s, lbl_fs, lbl_f) in self.lbls_taller.items():
            if rep is None:
                lbl_s.setText("-"); lbl_fs.setText("-"); lbl_f.setText("-")
                continue

            st = self._st(rep, self._nombre_real_taller(taller))
            lbl_s.setText(str(int(st["stock_actual"] or 0)))
            lbl_fs.setText(str(int(st["fuera_servicio"] or 0)))
            lbl_f.setText(self._formatear_fecha(st["fecha_ingreso"]))
        if rep is None:
            self.lbl_totales.setText("🔵 En uso: -    •    Σ Total: -")
        else:
            self.lbl_totales.setText(
                f"🔵 En uso: {self._en_uso(rep)}    •    Σ Total: {self._total_general(rep)}")

    # ─────────────────────────────────────────────────────────
    #  CATÁLOGO
    # ─────────────────────────────────────────────────────────
    def _leer_formulario(self):
        return {
            "numero_parte": self.input_numero_parte.text().strip(),
            "nombre": self.input_nombre.text().strip(),
            "stock_aep": self.spin_stock_aep.value(),
            "stock_eze": self.spin_stock_eze.value(),
            "modelos": self._modelos_marcados(),
        }

    def _validar(self, datos):
        if not datos["numero_parte"]:
            QMessageBox.warning(self, "⚠️ Atención", "Ingresá el número de parte.")
            return False
        if not datos["nombre"]:
            QMessageBox.warning(self, "⚠️ Atención", "Ingresá el nombre del repuesto.")
            return False
        if not datos["modelos"]:
            QMessageBox.warning(self, "⚠️ Atención",
                                "Vinculá al menos un modelo de equipo al repuesto.")
            return False
        return True

    def guardar_repuesto(self):
        if self.repuesto_en_edicion:
            self.borrar_campos()
            return
        repuestos = self._leer_formulario()
        if not self._validar(repuestos):
            return
        ahora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        repuestos["en_uso"] = 0
        repuestos["stock_actual"] = repuestos["stock_aep"] + repuestos["stock_eze"]  # referencia
        repuestos["talleres"] = {
            "Aeroparque": _taller(repuestos["stock_aep"], 0, ahora),
            "Ezeiza": _taller(repuestos["stock_eze"], 0, ahora),
        }

        try:
            self.api.post("guardar_repuesto.php", repuestos)
            self.aplicar_filtros()
            self.borrar_campos()
            QMessageBox.information(
                self, "✅ Guardado",
                f"Repuesto '{repuestos['nombre']}' agregado.\n"
                f"Stock inicial → Aeroparque: {repuestos['stock_aep']}  •  Ezeiza: {repuestos['stock_eze']}.")
            return True
        except SesionExpirada:
            QMessageBox.warning(self, "Sesión expirada",
                                "Tu sesión venció. Cerrá y volvé a iniciar sesión.")
            return False
        except ApiError as e:
            QMessageBox.critical(self, "❌ Error al Guardar",
                                 f"No se pudo guardar el repuesto:\n{e}")
            return False
        
    def modificar_repuesto(self):
        if self.repuesto_en_edicion is None:
            QMessageBox.warning(self, "⚠️ Sin selección",
                                "Seleccioná un repuesto de la tabla para modificar.")
            return
        datos = self._leer_formulario()
        if not self._validar(datos):
            return

        datos.update({"id_repuesto": self.repuesto_en_edicion})
        try:
            self.api.post("modificar_repuesto.php", datos)
            self.aplicar_filtros()
            QMessageBox.information(self, "✅ Modificado", "Repuesto modificado correctamente.")
        except SesionExpirada:
            QMessageBox.warning(self, "Sesión expirada",
                "Tu sesión venció. Cerrá y volvé a iniciar sesión.")
        except ApiError as e:
            QMessageBox.critical(self, "Error", f"No se pudo modificar el repuesto:\n{e}")


    def baja_repuesto(self):
        if self.repuesto_en_edicion is None:
            QMessageBox.warning(self, "⚠️ Sin selección",
                                "Seleccioná un repuesto de la tabla para dar de baja.")
            return
        rep = self._repuesto_actual()
        if rep is None:
            return
        resp = QMessageBox.question(
            self, "❌ Dar de baja",
            f"¿Dar de baja el repuesto '{rep['nombre']}' (N° parte {rep['numero_parte']})?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if resp == QMessageBox.StandardButton.Yes:
            try:
                self.api.post("baja_repuesto.php", {"id_repuesto": self.repuesto_en_edicion})
                self.borrar_campos()
                self.aplicar_filtros()
                QMessageBox.information(self, "✅ Baja", "Repuesto dado de baja correctamente.")
            except SesionExpirada:
                QMessageBox.warning(self, "Sesión expirada",
                "Tu sesión venció. Cerrá y volvé a iniciar sesión.")
            except ApiError as e:
                QMessageBox.critical(self, "Error", f"No se pudo borrar el repuesto:\n{e}")

    def borrar_campos(self):
        self.repuesto_en_edicion = None
        self.input_numero_parte.clear()
        self.input_nombre.clear()
        self.lbl_compat.setText("🔗 Compatible con: —")
        self.spin_stock_aep.setValue(0)
        self.spin_stock_eze.setValue(0)
        self._marcar_modelos([])
        self._refrescar_estado(None)
        self.tabla.clearSelection()
        self.tabla.setCurrentCell(-1, -1)

    # ─────────────────────────────────────────────────────────
    #  MOVIMIENTOS DE ESTADO
    # ─────────────────────────────────────────────────────────
    def _repuesto_actual(self):
        return next((r for r in self.datos_completos
                     if r["id_repuesto"] == self.repuesto_en_edicion), None)

    def _requiere_seleccion(self):
        if self.repuesto_en_edicion is None:
            QMessageBox.warning(self, "⚠️ Sin selección",
                                "Seleccioná un repuesto de la tabla.")
            return None, None
        return self._repuesto_actual(), self.combo_taller_oper.currentText()

    def ajustar_stock(self):
        """Forzar a mano stock/fuera de servicio de cada taller + en uso."""
        if self.repuesto_en_edicion is None:
            QMessageBox.warning(self, "⚠️ Sin selección",
                                "Seleccioná un repuesto de la tabla para ajustar su stock.")
            return
        rep = self._repuesto_actual()
        dlg = DialogoAjusteStock(rep, parent=self)
        if dlg.exec() != QDialog.DialogCode.Accepted:
            return
        valores, en_uso = dlg.valores()
        ahora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        for taller, v in valores.items():
            st = rep["talleres"].setdefault(
                taller, {"stock": 0, "fuera_servicio": 0, "fecha_ingreso": None})
            if v["stock"] != int(st.get("stock", 0) or 0):
                st["fecha_ingreso"] = ahora   # actualiza fecha si cambió el stock
            st["stock"] = v["stock"]
            st["fuera_servicio"] = v["fuera_servicio"]
        rep["en_uso"] = en_uso

        payload = {
            "id_repuesto": rep["id_repuesto"],
            "en_uso": rep["en_uso"],
            "talleres": rep["talleres"],
        }
        try:
            self.api.post("ajustar_stock.php", payload)
            self._post_movimiento(rep)
            QMessageBox.information(self, "✅ Ajuste guardado",
                            f"Stock de '{rep['nombre']}' actualizado (forzado).")
        except SesionExpirada:
            QMessageBox.warning(self, "Sesión expirada",
                "Tu sesión venció. Cerrá y volvé a iniciar sesión.")
        except ApiError as e:
            QMessageBox.critical(self, "Error", f"No se pudo ajustar el stock:\n{e}")

    def registrar_ingreso(self):
        """+ stock en el taller elegido."""
        rep, taller = self._requiere_seleccion()
        if rep is None:
            return
        dlg = DialogoCantidad("📥 Registrar ingreso",
                              f"Unidades que ingresan a stock en {taller}:",
                              color="#f57c00", parent=self)
        if dlg.exec() != QDialog.DialogCode.Accepted:
            return
        cant = dlg.valor()
        st = rep["talleres"][taller]
        st["stock_actual"] = int(st["stock_actual"] or 0) + cant
        st["fecha_ingreso"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"Registrar ingreso: {cant} de '{rep['nombre']}' a {taller}. Nuevo stock: {st['stock_actual']}")
        payload = {
            "id_repuesto": rep["id_repuesto"],
            "taller": taller,
            "cantidad": cant,
        }
        try:
            self.api.post("ingreso_repuesto.php", payload)
            self._post_movimiento(rep)
            QMessageBox.information(self, "✅ Ingreso registrado",
                               f"Ingresaron {cant} de '{rep['nombre']}' a {taller}.\n"
                               f"Stock en {taller}: {st['stock_actual']}.")
        except SesionExpirada:
            QMessageBox.warning(self, "Sesión expirada",
                "Tu sesión venció. Cerrá y volvé a iniciar sesión.")
        except ApiError as e:
            QMessageBox.critical(self, "Error", f"No se pudo registrar el ingreso:\n{e}")

    def usar_en_equipo(self):
        """stock (taller) → en uso (general). Es lo que dispara el ingreso/
        modificación de equipo al marcar repuestos usados."""
        rep, taller = self._requiere_seleccion()
        if rep is None:
            return
        st = self._st(rep, self._nombre_real_taller(taller))
        disp = int(st["stock_actual"] or 0)
        if disp <= 0:
            QMessageBox.warning(self, "⚠️ Sin stock",
                                f"No hay stock de '{rep['nombre']}' en {taller}.")
            return
        dlg = DialogoCantidad("🔧 Usar en equipo",
                              f"Unidades de '{rep['nombre']}' que pasan a EN USO "
                              f"(salen del stock de {taller}):",
                              maximo=disp, color="#1976d2", parent=self)
        if dlg.exec() != QDialog.DialogCode.Accepted:
            return
        cant = dlg.valor()
        st["stock_actual"] = disp - cant
        rep["en_uso"] = self._en_uso(rep) + cant
        payload = {
            "id_repuesto": rep["id_repuesto"],
            "taller": taller,
            "cantidad": cant,
        }
        try:
            self.api.post("usar_repuesto.php", payload)
            self._post_movimiento(rep)
            QMessageBox.information(self, "🔧 En uso",
                f"{cant} de '{rep['nombre']}' pasaron a EN USO.\n"
                f"En uso (total): {rep['en_uso']}  •  Stock {taller}: {st['stock_actual']}.")
        except SesionExpirada:
            QMessageBox.warning(self, "Sesión expirada",
                "Tu sesión venció. Cerrá y volvé a iniciar sesión.")
        except ApiError as e:
            QMessageBox.critical(self, "Error", f"No se pudo registrar el uso:\n{e}")

    def marcar_fuera_servicio(self):
        """en uso (general) → fuera de servicio (taller). Solo cuenta; el
        rótulo (origen/falla) es una etiqueta física del usuario."""
        rep, taller = self._requiere_seleccion()
        if rep is None:
            return
        en_uso = self._en_uso(rep)
        if en_uso <= 0:
            QMessageBox.warning(self, "⚠️ Sin unidades en uso",
                                f"No hay unidades de '{rep['nombre']}' en uso para dar de baja.")
            return
        dlg = DialogoCantidad("🔴 Fuera de servicio",
                              f"Unidades de '{rep['nombre']}' que salen de servicio "
                              f"(quedan a reparar en {taller}):",
                              maximo=en_uso, color="#8e24aa", parent=self)
        if dlg.exec() != QDialog.DialogCode.Accepted:
            return
        cant = dlg.valor()
        rep["en_uso"] = en_uso - cant
        st = rep["talleres"][taller]
        st["fuera_servicio"] = int(st["fuera_servicio"] or 0) + cant
        payload = {
            "id_repuesto": rep["id_repuesto"],
            "taller": taller,
            "cantidad": cant,
        }
        try:
            self.api.post("fuera_servicio.php", payload)
            self._post_movimiento(rep)
            QMessageBox.information(self, "🔴 Fuera de servicio",
                               f"{cant} de '{rep['nombre']}' quedaron FUERA DE SERVICIO en {taller}.\n"
                               f"Recordá ponerles la etiqueta física (origen / falla).\n"
                               f"En uso: {rep['en_uso']}  •  Fuera de servicio en {taller}: {st['fuera_servicio']}.")
        except SesionExpirada:
            QMessageBox.warning(self, "Sesión expirada",
                "Tu sesión venció. Cerrá y volvé a iniciar sesión.")
        except ApiError as e:
            QMessageBox.critical(self, "Error", f"No se pudo marcar fuera de servicio:\n{e}")

    def reparar_repuesto(self):
        """fuera de servicio (taller) → stock (taller)."""
        rep, taller = self._requiere_seleccion()
        if rep is None:
            return
        st = self._st(rep, self._nombre_real_taller(taller))
        fs = int(st["fuera_servicio"] or 0)
        if fs <= 0:
            QMessageBox.warning(self, "⚠️ Sin fuera de servicio",
                                f"No hay unidades fuera de servicio de '{rep['nombre']}' en {taller}.")
            return
        dlg = DialogoCantidad("♻️ Reparar",
                              f"Unidades reparadas que vuelven al stock en {taller}:",
                              maximo=fs, color="#00897b", parent=self)
        if dlg.exec() != QDialog.DialogCode.Accepted:
            return
        cant = dlg.valor()
        st["fuera_servicio"] = fs - cant
        st["stock_actual"] = int(st["stock_actual"] or 0) + cant
        st["fecha_ingreso"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        payload = {
            "id_repuesto": rep["id_repuesto"],
            "taller": taller,
            "cantidad": cant,
        }
        try:
            self.api.post("reparar_repuesto.php", payload)
            self._post_movimiento(rep)
            QMessageBox.information(self, "♻️ Reparación registrada",
                f"{cant} de '{rep['nombre']}' volvieron al stock en {taller}.\n"
                f"Stock {taller}: {st['stock_actual']}  •  Fuera de servicio: {st['fuera_servicio']}.")
        except SesionExpirada:
                QMessageBox.warning(self, "Sesión expirada",
                    "Tu sesión venció. Cerrá y volvé a iniciar sesión.")
        except ApiError as e:
                QMessageBox.critical(self, "Error", f"No se pudo reparar repuesto:\n{e}")

    def descartar_fuera_servicio(self):
        """- fuera de servicio (taller): baja definitiva (irreparable)."""
        rep, taller = self._requiere_seleccion()
        if rep is None:
            return
        st = self._st(rep, self._nombre_real_taller(taller))
        fs = int(st["fuera_servicio"] or 0)
        if fs <= 0:
            QMessageBox.warning(self, "⚠️ Sin fuera de servicio",
                                f"No hay unidades fuera de servicio de '{rep['nombre']}' en {taller}.")
            return
        dlg = DialogoCantidad("🗑️ Descartar",
                              f"Unidades irreparables a descartar en {taller}:",
                              maximo=fs, color="#546e7a", parent=self)
        if dlg.exec() != QDialog.DialogCode.Accepted:
            return
        cant = dlg.valor()
        resp = QMessageBox.question(
            self, "🗑️ Confirmar descarte",
            f"¿Descartar {cant} unidad(es) de '{rep['nombre']}' en {taller}?\n"
            f"Esta acción no se puede deshacer.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if resp != QMessageBox.StandardButton.Yes:
            return
        st["fuera_servicio"] = fs - cant
        payload = {
            "id_repuesto": rep["id_repuesto"],
            "taller": taller,
            "cantidad": cant,
        }
        try:
            self.api.post("descartar_repuesto.php", payload)
            self._post_movimiento(rep)
            QMessageBox.information(self, "🗑️ Descartado",
                f"Se descartaron {cant} de '{rep['nombre']}' en {taller}.")
        except SesionExpirada:
                QMessageBox.warning(self, "Sesión expirada",
                    "Tu sesión venció. Cerrá y volvé a iniciar sesión.")
        except ApiError as e:
                QMessageBox.critical(self, "Error", f"No se pudo descartar el repuesto:\n{e}")


    # ─────────────────────────────────────────────────────────
    #  INTEGRACIÓN: ingreso / modificación de equipo
    # ─────────────────────────────────────────────────────────
    def aplicar_uso_por_equipo(self, usos, taller=None):
        """Punto de integración para el ingreso/modificación de equipo.

        usos: lista de (id_repuesto, cantidad) de los repuestos utilizados.
        taller: de dónde sale el stock (por defecto, el elegido en la tab).

        Descuenta del stock del taller y suma al conteo GENERAL "en uso".
        Si no hay stock suficiente en ese taller, igual suma a "en uso"
        (el faltante queda como stock negativo evitado -> se limita a 0) y
        se informa. Devuelve la lista de repuestos que no tenían stock.
        """
        if taller is None:
            taller = self.combo_taller_oper.currentText()
        sin_stock = []
        for id_repuesto, cantidad in usos:
            rep = next((r for r in self.datos_completos
                        if r["id_repuesto"] == id_repuesto), None)
            if rep is None:
                continue
            st = rep["talleres"].get(taller)
            if st is None:
                continue
            disponible = int(st["stock"] or 0)
            usa_de_stock = min(disponible, cantidad)
            st["stock"] = disponible - usa_de_stock
            rep["en_uso"] = self._en_uso(rep) + cantidad
            if usa_de_stock < cantidad:
                sin_stock.append((rep["nombre"], cantidad - usa_de_stock))
        # Con backend: un solo POST con la lista -> usar_repuesto.php
        self.aplicar_filtros()
        return sin_stock

    # ─────────────────────────────────────────────────────────
    def _post_movimiento(self, rep):
        self.aplicar_filtros()
        self._reseleccionar(rep["id_repuesto"])
        self._refrescar_estado(self._repuesto_actual())

    def _reseleccionar(self, id_repuesto):
        for fila, rep in enumerate(self.datos_filtrados):
            if rep["id_repuesto"] == id_repuesto:
                self.tabla.blockSignals(True)
                self.tabla.selectRow(fila)
                self.tabla.blockSignals(False)
                self.repuesto_en_edicion = id_repuesto
                return

    # ─────────────────────────────────────────────────────────
    #  MENÚ CONTEXTUAL (copiar)
    # ─────────────────────────────────────────────────────────
    # ─────────────────────────────────────────────────────────
    #  EXPORTAR A SQL (migración provisoria)
    # ─────────────────────────────────────────────────────────
    def _sql_str(self, s):
        """Escapa un texto para SQL (comillas simples). Preserva el texto EXACTO."""
        if s is None:
            return "NULL"
        return "'" + str(s).replace("\\", "\\\\").replace("'", "\\'") + "'"

    def exportar_sql(self):
        """Genera un .sql con TODO lo cargado en la tab, para migrar a la base final.
        Usa identificadores en minúscula (compatibles con Linux) y los id_taller reales."""
        ruta, _ = QFileDialog.getSaveFileName(
            self, "Exportar migración de repuestos",
            "migracion_repuestos.sql", "Archivos SQL (*.sql)")
        if not ruta:
            return

        L = []
        L.append("-- Migración de Stock de Repuestos (generada por la tab provisoria)")
        L.append("-- Identificadores en minúscula (compatibles con MySQL/Linux case-sensitive).")
        L.append("-- Talleres: 1 = Taller de radio AEP (Aeroparque), 2 = Taller de radio EZE (Ezeiza).")
        L.append("SET NAMES utf8mb4;")
        L.append("START TRANSACTION;")
        L.append("")
        L.append("-- 1) Columnas nuevas en `repuestos` (ejecutar UNA sola vez; si ya existen, comentá estas líneas).")
        L.append("ALTER TABLE `repuestos`")
        L.append("    ADD COLUMN `numero_parte` VARCHAR(60) NULL AFTER `id_repuesto`,")
        L.append("    ADD COLUMN `en_uso` INT(11) NOT NULL DEFAULT 0;")
        L.append("")
        L.append("-- 2) Tabla de stock por taller (ejecutar UNA sola vez).")
        L.append("CREATE TABLE IF NOT EXISTS `repuesto_stock` (")
        L.append("    `id_repuesto` INT(11) NOT NULL,")
        L.append("    `id_taller` INT(11) NOT NULL,")
        L.append("    `stock_actual` INT(11) NOT NULL DEFAULT 0,")
        L.append("    `fuera_servicio` INT(11) NOT NULL DEFAULT 0,")
        L.append("    `fecha_ingreso` DATETIME NULL,")
        L.append("    PRIMARY KEY (`id_repuesto`,`id_taller`)")
        L.append(") ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;")
        L.append("")
        L.append("-- 2b) La descripción se reemplaza por la compatibilidad (tabla modelo_repuesto).")
        L.append("--     Si querés eliminar la columna que ya no se usa, descomentá:")
        L.append("-- ALTER TABLE `repuestos` DROP COLUMN `descripcion`;")
        L.append("")

        # 3) Catálogo de repuestos (existentes -> UPDATE; nuevos -> INSERT). Sin descripción.
        L.append("-- 3) Catálogo de repuestos (sin descripción).")
        for rep in self.datos_completos:
            rid = rep["id_repuesto"]
            total = self._total_stock(rep)
            nombre = self._sql_str(rep.get("nombre", ""))
            np = self._sql_str(rep.get("numero_parte", "") or None)
            en_uso = self._en_uso(rep)
            if rid in IDS_ORIGINALES_BD:
                L.append(f"UPDATE `repuestos` SET `nombre`={nombre}, "
                         f"`numero_parte`={np}, `stock_actual`={total}, `en_uso`={en_uso} "
                         f"WHERE `id_repuesto`={rid};")
            else:
                # `descripcion` es NOT NULL en la base actual: si todavía existe, se manda ''.
                L.append(f"INSERT INTO `repuestos` (`id_repuesto`,`nombre`,`numero_parte`,"
                         f"`descripcion`,`stock_actual`,`en_uso`) "
                         f"VALUES ({rid},{nombre},{np},'',{total},{en_uso});")
        L.append("")

        # 4) Vínculos modelo_repuesto (INSERT IGNORE para no duplicar los existentes)
        L.append("-- 4) Vínculos repuesto ↔ modelo.")
        pares = []
        for rep in self.datos_completos:
            for id_mod in rep.get("modelos", []):
                pares.append((id_mod, rep["id_repuesto"]))
        if pares:
            valores = ",\n".join(f"({m},{r})" for m, r in pares)
            L.append("INSERT IGNORE INTO `modelo_repuesto` (`id_modelo`,`id_repuesto`) VALUES")
            L.append(valores + ";")
        L.append("")

        # 5) Stock por taller
        L.append("-- 5) Stock por taller (en stock + fuera de servicio).")
        filas = []
        for rep in self.datos_completos:
            for taller in TALLERES:
                st = self._st(rep, taller)
                idt = TALLER_ID[taller]
                fecha = self._sql_str(st.get("fecha_ingreso"))
                filas.append(f"({rep['id_repuesto']},{idt},{int(st['stock'] or 0)},"
                             f"{int(st['fuera_servicio'] or 0)},{fecha})")
        if filas:
            L.append("INSERT INTO `repuesto_stock` "
                     "(`id_repuesto`,`id_taller`,`stock_actual`,`fuera_servicio`,`fecha_ingreso`) VALUES")
            L.append(",\n".join(filas) + "")
            L.append("ON DUPLICATE KEY UPDATE `stock_actual`=VALUES(`stock_actual`), "
                     "`fuera_servicio`=VALUES(`fuera_servicio`), `fecha_ingreso`=VALUES(`fecha_ingreso`);")
        L.append("")
        L.append("COMMIT;")

        try:
            with open(ruta, "w", encoding="utf-8") as f:
                f.write("\n".join(L))
            QMessageBox.information(
                self, "✅ Exportado",
                f"Migración exportada a:\n{ruta}\n\n"
                f"{len(self.datos_completos)} repuestos, {len(pares)} vínculos, "
                f"{len(filas)} filas de stock.\n\n"
                "Revisá el archivo antes de correrlo en la base. Las columnas nuevas y la tabla "
                "`repuesto_stock` se crean una sola vez (comentá esas líneas si ya existen).")
        except OSError as e:
            QMessageBox.critical(self, "Error", f"No se pudo guardar el archivo:\n{e}")

    def mostrar_menu_contextual(self, tabla, pos):
        menu = QMenu(self)
        menu.setStyleSheet("""
            QMenu { background-color: white; border: 1px solid #cfd8dc;
                    border-radius: 4px; padding: 5px; }
            QMenu::item { padding: 8px 25px; border-radius: 3px; color: black; }
            QMenu::item:selected { background-color: #e3f2fd; color: #1976d2; }
        """)
        item = tabla.itemAt(pos)
        if item:
            accion_celda = QAction("📋 Copiar celda", self)
            accion_celda.triggered.connect(lambda: self.copiar_celda(tabla))
            menu.addAction(accion_celda)
            accion_fila = QAction("📄 Copiar fila completa", self)
            accion_fila.triggered.connect(lambda: self.copiar_fila(tabla))
            menu.addAction(accion_fila)
            menu.addSeparator()
        menu.exec(tabla.mapToGlobal(pos))

    def copiar_celda(self, tabla):
        item = tabla.currentItem()
        if item:
            QApplication.clipboard().setText(item.text())
            QMessageBox.information(self, "✅ Copiado", f"Texto copiado: {item.text()}")

    def copiar_fila(self, tabla):
        fila = tabla.currentRow()
        if fila >= 0:
            textos = []
            for col in range(tabla.columnCount()):
                if tabla.isColumnHidden(col):
                    continue
                item = tabla.item(fila, col)
                textos.append(item.text() if item else "")
            QApplication.clipboard().setText("\t".join(textos))
            QMessageBox.information(self, "✅ Copiado", "Fila copiada al portapapeles")
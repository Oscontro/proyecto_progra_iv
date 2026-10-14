"""
Pestaña:  Estadísticas
Versión:  4.0 - AISLADA (PRUEBA Y DISEÑO)
Fecha:  2026-08-10
Autor:  Lucas E Goitea Juarez
Descripción:
    Dashboard de estadísticas rediseñado para manejar ALTA CARDINALIDAD
    (40 escalas, muchos modelos, cientos de repuestos).

    Cambios respecto de la v3:
      • Tarjetas superiores compactas (tira horizontal, ~mitad de alto).
      • Distribución: barras (no torta). "Por modelo" con scroll. "Por escala"
        con selector + tabla de equipos asociados. Es estado ACTUAL (sin año).
      • Incidencias: filtro Año (total/año) + filtro Escala (total/una escala).
        Gráficos: incidencias por TIPO de equipo, y repuestos utilizados por un
        MODELO elegido. (Reemplaza "incidencias por escala" ilegible con 40.)
      • Dados de baja: filtro Año. Barras horizontales con scroll por modelo y
        por escala (soporta 40+).
      • Gráficos con muchas categorías = barras horizontales ordenadas + scroll.

    MODO STANDALONE / PRUEBA   ->   python tab_estadisticas.py
    (datos de ejemplo en memoria; con backend se reemplazan por self.api.get(...))

    Integración en main.py:
        from tabs.tab_estadisticas import EstadisticasTab
        self.tabs.addTab(EstadisticasTab(self.api), "📊 Estadísticas")
"""

import sys
import random
from datetime import datetime
from base_tab import ApiTab
from api_client import ApiError, SesionExpirada
from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame,
    QTabWidget, QComboBox, QPushButton, QScrollArea, QTableWidget,
    QTableWidgetItem, QHeaderView, QAbstractItemView, QSizePolicy,
    QLineEdit, QTextEdit, QDialog, QMessageBox
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont

import matplotlib
matplotlib.use('QtAgg')
from matplotlib.figure import Figure
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas


# ═══════════════════════════════════════════════════════════
#  DATOS DE EJEMPLO
# ═══════════════════════════════════════════════════════════
TIPOS = ["PORTATIL", "MOVIL", "BASE", "REPETIDORA", "ESCANER", "FUENTE", "ANTENA"]

MODELOS = [
    "DEP450", "EP450", "R2", "GM300", "PRO5100", "PRO3100", "DGM6100", "EM200",
    "IC-A200", "IC-A210", "IC-A110", "IC-V80", "TK-90", "BC355N", "BC365CRS",
    "UBC860XLT", "MB-53", "EP-815", "PRO2150", "GM339", "DEM300", "MIP5000",
]

# 40 escalas (códigos de aeropuertos AR)
ESCALAS = [
    "PAE", "EZE", "COR", "MDZ", "BRC", "FTE", "IGR", "SLA", "TUC", "NQN",
    "BHI", "RES", "PSS", "CNQ", "RGL", "USH", "REL", "CRD", "VDM", "RGA",
    "JUJ", "SDE", "CTC", "LGS", "IRJ", "SFN", "PRA", "ROS", "MDQ", "RCU",
    "VLG", "EQS", "ESQ", "RSA", "OYA", "CPC", "RZA", "PMY", "EHL", "AFA",
]


TALLERES = ["Aeroparque", "Ezeiza"]


def _generar_datos_ejemplo():
    """Genera un set de datos coherente para la demo (determinístico)."""
    rnd = random.Random(42)
    equipos = []
    eid = 100
    # 1) Equipos asignados a una escala
    for esc in ESCALAS:
        # cada escala tiene entre 2 y 14 equipos
        for _ in range(rnd.randint(2, 14)):
            eid += 1
            modelo = rnd.choice(MODELOS)
            tipo = rnd.choice(TIPOS)
            equipos.append({
                "id_equipo": eid,
                "numero_serie": f"SN-{modelo}-{eid}",
                "tipo": tipo,
                "modelo": modelo,
                "escala": esc,
                "en_stock": None,          # asignado -> no está en stock
                "anio_baja": rnd.choice([None, None, None, None, 2023, 2024, 2025]), # ->fecha envio a papelera.
                "incidencias": {a: rnd.randint(0, 4) for a in (2023, 2024, 2025)}, # -> fecha ingreso
            })
    # 2) Equipos EN STOCK en un taller, a la espera de asignación (sin escala)
    for taller in TALLERES:
        for _ in range(rnd.randint(8, 16)):
            eid += 1
            modelo = rnd.choice(MODELOS)
            tipo = rnd.choice(TIPOS)
            equipos.append({
                "id_equipo": eid,
                "numero_serie": f"SN-{modelo}-{eid}",
                "tipo": tipo,
                "modelo": modelo,
                "escala": None,
                "en_stock": taller,        # esperando asignación en este taller
                "anio_baja": None,
                "incidencias": {a: 0 for a in (2023, 2024, 2025)},
            })
    return equipos


EQUIPOS = _generar_datos_ejemplo()

# Repuestos vinculados a cada modelo, con uso por (año, escala) simulado.
REPUESTOS_POR_MODELO = {
    "DEP450": ["POTENCIOMETRO", "ANTENA", "CARCAZA", "BATERIA", "SWITCH PTT",
               "MICROFONO", "DISPLAY", "PARLANTE"],
    "EP450": ["POTENCIOMETRO", "ANTENA", "CARCAZA", "BATERIA", "SWITCH PTT",
              "GOMA PTT", "CLIP DE CINTURA"],
    "GM300": ["MICROFONO", "FUENTE 13,8V", "PERILLA", "FUSIBLE", "CONECTOR RF"],
    "IC-A200": ["DISPLAY", "PERILLA", "FUSIBLE", "MICROFONO", "CONECTOR RF"],
    "PRO5100": ["MICROFONO", "FUENTE 13,8V", "PERILLA", "DISPLAY"],
}


def _uso_repuestos(modelo, anio, escala):
    """Uso simulado de repuestos para un modelo, filtrando año/escala."""
    reps = REPUESTOS_POR_MODELO.get(modelo, ["REPUESTO A", "REPUESTO B", "REPUESTO C"])
    rnd = random.Random(hash((modelo, anio or 0, escala or "T")) & 0xFFFF)
    return {r: rnd.randint(1, 30) for r in reps}


# ═══════════════════════════════════════════════════════════
#  CANVAS
# ═══════════════════════════════════════════════════════════
class GraficoCanvas(FigureCanvas):
    def __init__(self, parent=None, width=6, height=5, dpi=100):
        self.fig = Figure(figsize=(width, height), dpi=dpi)
        self.axes = self.fig.add_subplot(111)
        super().__init__(self.fig)
        self.setParent(parent)
        self.fig.patch.set_facecolor('#ffffff')
        self.axes.set_facecolor('#ffffff')


AZUL = "#1976d2"
NARANJA = "#f57c00"
ROJO = "#c62828"
VIOLETA = "#7b1fa2"

# Paleta categórica validada (guía dataviz, modo claro). Un color por barra,
# en orden fijo y cíclico. La identidad la da la etiqueta del eje + el número;
# el color es una ayuda visual para separar barras contiguas.
PALETA_CAT = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100",
              "#e87ba4", "#008300", "#4a3aa7", "#e34948"]


def _vacio(canvas, mensaje="Sin datos"):
    canvas.axes.clear()
    canvas.axes.text(0.5, 0.5, mensaje, ha='center', va='center',
                     transform=canvas.axes.transAxes, fontsize=13,
                     color='#90a4ae', weight='bold')
    canvas.axes.set_xticks([]); canvas.axes.set_yticks([])
    canvas.draw()


def barras_horizontales(canvas, datos, color=None, unidad="", titulo=""):
    """Barras horizontales ordenadas de mayor a menor (más grande arriba).
    Cada barra toma un color distinto de la paleta categórica (cíclico)."""
    if not datos:
        _vacio(canvas)
        return
    items = sorted(datos.items(), key=lambda kv: kv[1])   # asc -> mayor arriba en barh
    labels = [k for k, _ in items]
    valores = [v for _, v in items]
    colores = [PALETA_CAT[i % len(PALETA_CAT)] for i in range(len(labels))]

    canvas.axes.clear()
    y = range(len(labels))
    barras = canvas.axes.barh(list(y), valores, color=colores, alpha=0.95,
                              edgecolor='white', linewidth=1.2)
    canvas.axes.set_yticks(list(y))
    canvas.axes.set_yticklabels(labels, fontsize=9)
    for b, v in zip(barras, valores):
        canvas.axes.text(b.get_width(), b.get_y() + b.get_height()/2,
                         f' {int(v)}', va='center', ha='left',
                         fontsize=8, weight='bold', color='#37474f')
    total = sum(valores)
    canvas.axes.set_title(f"{titulo}   (Total: {total} {unidad})".strip(),
                          fontsize=11, weight='bold', color='#37474f')
    canvas.axes.grid(axis='x', alpha=0.3, linestyle='--')
    canvas.axes.margins(x=0.12)
    canvas.fig.tight_layout()
    canvas.draw()


# ═══════════════════════════════════════════════════════════
#  UTILIDADES DE UI
# ═══════════════════════════════════════════════════════════
def _frame_grafico(titulo):
    frame = QFrame()
    frame.setStyleSheet("""
        QFrame { background-color: white; border-radius: 10px; border: 2px solid #cfd8dc; }
    """)
    lay = QVBoxLayout(frame)
    lay.setContentsMargins(8, 6, 8, 8)
    lay.setSpacing(4)
    lbl = QLabel(titulo)
    lbl.setFont(QFont("Arial", 10, QFont.Weight.Bold))
    lbl.setStyleSheet("color: #37474f;")
    lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
    lay.addWidget(lbl)
    return frame


def _grafico_con_scroll(canvas):
    """Envuelve un canvas en un scroll vertical (para muchas categorías)."""
    scroll = QScrollArea()
    scroll.setWidgetResizable(True)
    scroll.setFrameShape(QFrame.Shape.NoFrame)
    scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
    scroll.setStyleSheet("""
        QScrollArea { background: white; border: none; }
        QScrollBar:vertical { border: none; background: #eceff1; width: 12px;
                              margin: 0; border-radius: 6px; }
        QScrollBar::handle:vertical { background: #78909c; min-height: 30px; border-radius: 6px; }
        QScrollBar::handle:vertical:hover { background: #1976d2; }
        QScrollBar::sub-line:vertical, QScrollBar::add-line:vertical { height: 0; }
    """)
    scroll.setWidget(canvas)
    return scroll


def ajustar_alto_scroll(canvas, n):
    """Alto del canvas proporcional a la cantidad de barras (para el scroll)."""
    canvas.setMinimumHeight(max(280, 26 * n + 90))
    canvas.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)


def _combo(items, color="#1976d2"):
    c = QComboBox()
    c.addItems(items)
    c.setFixedHeight(28)
    c.setStyleSheet(f"""
        QComboBox {{ border: 2px solid #cfd8dc; border-radius: 6px; padding: 2px 6px;
                     min-width: 100px; background: white; color: black; font-size: 9pt; }}
        QComboBox:hover {{ border: 2px solid {color}; }}
        QComboBox QAbstractItemView {{ background: white; color: black;
                     selection-background-color: {color}; selection-color: white; }}
    """)
    return c


def _boton(texto, color, hover):
    b = QPushButton(texto)
    b.setFixedHeight(28)
    b.setCursor(Qt.CursorShape.PointingHandCursor)
    b.setStyleSheet(f"""
        QPushButton {{ background-color: {color}; color: white; border-radius: 6px;
                       padding: 0 16px; font-weight: bold; font-size: 10pt; }}
        QPushButton:hover {{ background-color: {hover}; }}
    """)
    return b


# ═══════════════════════════════════════════════════════════
#  SUB-PESTAÑA 1: DISTRIBUCIÓN (estado actual)
# ═══════════════════════════════════════════════════════════
class DistribucionTab(ApiTab):
    def __init__(self, api=None, equipos=None):
        super().__init__(api)
        self.api = api
        self.equipos = equipos if equipos is not None else []
        self.crear_interfaz()
        self.llenar_desplegables()
        self.actualizar()
        
        

    def crear_interfaz(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(8)

        fila = QHBoxLayout()
        fila.setSpacing(8)

        # Por tipo
        f_tipo = _frame_grafico("Por Tipo de Equipo")
        self.canvas_tipo = GraficoCanvas(width=5, height=4)
        f_tipo.layout().addWidget(self.canvas_tipo)
        fila.addWidget(f_tipo, 1)

        # Por modelo (con scroll)
        f_mod = _frame_grafico("Por Modelo")
        self.canvas_modelo = GraficoCanvas(width=5, height=4)
        f_mod.layout().addWidget(_grafico_con_scroll(self.canvas_modelo))
        fila.addWidget(f_mod, 1)

        layout.addLayout(fila, 3)

        # Fila inferior: por escala (izq) + tipo/modelo/cantidad (der)
        fila_inf = QHBoxLayout()
        fila_inf.setSpacing(8)

        # Por escala: selector + tabla
        f_esc = QFrame()
        f_esc.setStyleSheet("QFrame { background: white; border-radius: 10px;"
                            " border: 2px solid #cfd8dc; }")
        esc_lay = QVBoxLayout(f_esc)
        esc_lay.setContentsMargins(8, 8, 8, 8)

        sel_lay = QHBoxLayout()
        t = QLabel("Por Escala:")
        t.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        t.setStyleSheet("color: #37474f;")
        sel_lay.addWidget(t)

        estilo_combo = """
    QComboBox {
        border: 2px solid #cfd8dc; 
        border-radius: 6px; 
        padding: 2px 6px;
        min-width: 100px; 
        background-color: white; 
        color: black; 
        font-size: 9pt;
    }
    QComboBox:hover { 
        border: 2px solid #1976d2; 
        color: black;
    }
    QComboBox QAbstractItemView {
        background-color: white; 
        color: black;
        selection-background-color: #1976d2; 
        selection-color: white;
    }
    QComboBox QAbstractItemView::item {
        color: black;
        background-color: white;
    }
    """
        self.combo_escala = QComboBox()
        self.combo_escala.setFixedHeight(28)
        self.combo_escala.setStyleSheet(estilo_combo)
        self.combo_escala.currentTextChanged.connect(self.actualizar_escala)
        sel_lay.addWidget(self.combo_escala)
        self.lbl_escala_info = QLabel("")
        self.lbl_escala_info.setStyleSheet("color: #1565c0; font-weight: bold;")
        sel_lay.addWidget(self.lbl_escala_info)
        sel_lay.addStretch()
        esc_lay.addLayout(sel_lay)

        self.tabla_escala = QTableWidget()
        self.tabla_escala.setColumnCount(2)
        self.tabla_escala.setHorizontalHeaderLabels(["Modelo", "Cantidad"])
        self.tabla_escala.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.tabla_escala.setAlternatingRowColors(True)
        self.tabla_escala.setStyleSheet("""
            QTableWidget { border: 2px solid #cfd8dc; border-radius: 8px; background: white;
                           font-size: 10pt; color: black; }
            QTableWidget::item { padding: 5px; }
            QTableWidget::item:alternate { background: #f5f5f5; }
            QHeaderView::section { background: #78909c; color: white; padding: 6px;
                                   font-weight: bold; border: none; }
        """)
        self.tabla_escala.horizontalHeader().setSectionResizeMode(
            0, QHeaderView.ResizeMode.Stretch)
        self.tabla_escala.horizontalHeader().setSectionResizeMode(
            1, QHeaderView.ResizeMode.ResizeToContents)
        esc_lay.addWidget(self.tabla_escala)
        fila_inf.addWidget(f_esc, 1)

        # Tipo / Modelo / Cantidad
        f_tm = QFrame()
        f_tm.setStyleSheet("QFrame { background: white; border-radius: 10px;"
                           " border: 2px solid #cfd8dc; }")
        tm_lay = QVBoxLayout(f_tm)
        tm_lay.setContentsMargins(8, 8, 8, 8)
        t2 = QLabel("Tipo · Modelo · Cantidad")
        t2.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        t2.setStyleSheet("color: #37474f;")
        tm_lay.addWidget(t2)

        self.tabla_tm = QTableWidget()
        self.tabla_tm.setColumnCount(3)
        self.tabla_tm.setHorizontalHeaderLabels(["Tipo", "Modelo", "Cantidad"])
        self.tabla_tm.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.tabla_tm.setAlternatingRowColors(True)
        self.tabla_tm.setStyleSheet("""
            QTableWidget { border: 2px solid #cfd8dc; border-radius: 8px; background: white;
                           font-size: 10pt; color: black; }
            QTableWidget::item { padding: 5px; }
            QTableWidget::item:alternate { background: #f5f5f5; }
            QHeaderView::section { background: #78909c; color: white; padding: 6px;
                                   font-weight: bold; border: none; }
        """)
        self.tabla_tm.horizontalHeader().setSectionResizeMode(
            0, QHeaderView.ResizeMode.ResizeToContents)
        self.tabla_tm.horizontalHeader().setSectionResizeMode(
            1, QHeaderView.ResizeMode.Stretch)
        self.tabla_tm.horizontalHeader().setSectionResizeMode(
            2, QHeaderView.ResizeMode.ResizeToContents)
        tm_lay.addWidget(self.tabla_tm)
        fila_inf.addWidget(f_tm, 1)

        layout.addLayout(fila_inf, 2)

    def actualizar(self):
        # Por tipo
        por_tipo = {}
        for e in self.equipos:
            if e["anio_baja"] is None:  # solo activos
                por_tipo[e["tipo"]] = por_tipo.get(e["tipo"], 0) + 1
        barras_horizontales(self.canvas_tipo, por_tipo, color=AZUL, unidad="equipos")

        # Por modelo (scroll)
        por_modelo = {}
        for e in self.equipos:
            if e["anio_baja"] is None:
                por_modelo[e["modelo"]] = por_modelo.get(e["modelo"], 0) + 1
        ajustar_alto_scroll(self.canvas_modelo, len(por_modelo))
        barras_horizontales(self.canvas_modelo, por_modelo, unidad="equipos")

        # Tabla Tipo / Modelo / Cantidad (equipos activos)
        combos = {}
        for e in self.equipos:
            if e["anio_baja"] is None:
                k = (e["tipo"], e["modelo"])
                combos[k] = combos.get(k, 0) + 1
        items = sorted(combos.items(), key=lambda kv: (kv[0][0], -kv[1]))
        self.tabla_tm.setRowCount(len(items))
        for i, ((tipo, modelo), cant) in enumerate(items):
            it_t = QTableWidgetItem(tipo)
            it_m = QTableWidgetItem(modelo)
            it_c = QTableWidgetItem(str(cant))
            for it in (it_t, it_m, it_c):
                it.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            it_c.setFont(QFont("Arial", 10, QFont.Weight.Bold))
            self.tabla_tm.setItem(i, 0, it_t)
            self.tabla_tm.setItem(i, 1, it_m)
            self.tabla_tm.setItem(i, 2, it_c)

        self.actualizar_escala()

    def actualizar_escala(self):
        esc = self.combo_escala.currentText()
        equipos = [e for e in self.equipos if e["escala"] == esc and e["anio_baja"] is None]
        # Agregado por modelo (cantidad), no lista de series.
        por_modelo = {}
        for e in equipos:
            por_modelo[e["modelo"]] = por_modelo.get(e["modelo"], 0) + 1
        items = sorted(por_modelo.items(), key=lambda kv: kv[1], reverse=True)

        self.lbl_escala_info.setText(
            f"Total en {esc}: {len(equipos)} equipos  ·  {len(items)} modelos")
        self.tabla_escala.setRowCount(len(items))
        for i, (modelo, cant) in enumerate(items):
            it_m = QTableWidgetItem(modelo)
            it_m.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            it_c = QTableWidgetItem(str(cant))
            it_c.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            it_c.setFont(QFont("Arial", 10, QFont.Weight.Bold))
            self.tabla_escala.setItem(i, 0, it_m)
            self.tabla_escala.setItem(i, 1, it_c)
     
    def llenar_desplegables(self):
        """Llena todos los combos de la pestaña"""
        self.llenar_combo("escalas.php", self.combo_escala, "escala", incluir_todos=False)


# ═══════════════════════════════════════════════════════════
#  DIÁLOGO: N° de serie (ver y copiar)
# ═══════════════════════════════════════════════════════════
class DialogoSeries(QDialog):
    """Lista los N° de serie de un tipo+modelo y permite copiarlos."""

    def __init__(self, titulo, series, parent=None):
        super().__init__(parent)
        self.series = series
        self.setWindowTitle("N° de serie")
        self.setModal(True)
        self.setMinimumSize(420, 460)
        self.setStyleSheet("QDialog { background: #eceff1; }")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 18, 18, 18)
        layout.setSpacing(8)

        cab = QLabel(f"🔢 {titulo}")
        cab.setFont(QFont("Arial", 13, QFont.Weight.Bold))
        cab.setWordWrap(True)
        cab.setStyleSheet("color: white; background: #1976d2; border-radius: 8px; padding: 10px;")
        cab.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(cab)

        info = QLabel(f"{len(series)} unidad(es)")
        info.setStyleSheet("color: #546e7a; font-weight: bold;")
        layout.addWidget(info)

        self.texto = QTextEdit()
        self.texto.setReadOnly(True)
        self.texto.setPlainText("\n".join(series))
        self.texto.setStyleSheet("""
            QTextEdit { border: 2px solid #cfd8dc; border-radius: 8px; padding: 8px;
                        background: white; color: #263238; font-size: 11pt; }
        """)
        layout.addWidget(self.texto, 1)

        fila = QHBoxLayout()
        fila.setSpacing(8)
        btn_copiar = QPushButton("📋 Copiar todo")
        btn_copiar.setFixedHeight(42)
        btn_copiar.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_copiar.setStyleSheet("""
            QPushButton { background: #27ae60; color: white; border: none; border-radius: 8px;
                          padding: 0 22px; font-weight: bold; font-size: 11pt; }
            QPushButton:hover { background: #1e8449; }
        """)
        btn_copiar.clicked.connect(self.copiar)
        fila.addWidget(btn_copiar)

        btn_cerrar = QPushButton("Cerrar")
        btn_cerrar.setFixedHeight(42)
        btn_cerrar.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_cerrar.setStyleSheet("""
            QPushButton { background: #757575; color: white; border: none; border-radius: 8px;
                          padding: 0 22px; font-weight: bold; font-size: 11pt; }
            QPushButton:hover { background: #616161; }
        """)
        btn_cerrar.clicked.connect(self.accept)
        fila.addWidget(btn_cerrar)
        layout.addLayout(fila)

    def copiar(self):
        QApplication.clipboard().setText("\n".join(self.series))
        QMessageBox.information(self, "✅ Copiado",
                               f"{len(self.series)} N° de serie copiados al portapapeles.")


# ═══════════════════════════════════════════════════════════
#  SUB-PESTAÑA: EN STOCK (equipos en taller, sin asignar)
# ═══════════════════════════════════════════════════════════
class EnStockTab(QWidget):
    """Equipos en taller (Aeroparque/Ezeiza) esperando asignación.
    Se ven por Tipo/Modelo/Cantidad; un botón lista y copia los N° de serie."""

    def __init__(self, api=None, stock_equipos=None):
        super().__init__()
        self.api = api
        self.stock_equipos = stock_equipos
        self.tablas = {}
        self.labels = {}
        self.mapa_filas = {}   # taller -> [(tipo, modelo, [series...]), ...]
        self.crear_interfaz()
        self.actualizar()

    def crear_interfaz(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(10)

        intro = QLabel("Equipos disponibles en taller, a la espera de ser asignados a una escala.")
        intro.setFont(QFont("Arial", 10))
        intro.setStyleSheet("color: #607d8b; font-style: italic;")
        layout.addWidget(intro)

        busq = QHBoxLayout()
        b = QLabel("🔍 Buscar:")
        b.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        b.setStyleSheet("color: #37474f;")
        busq.addWidget(b)
        self.input_buscar = QLineEdit()
        self.input_buscar.setPlaceholderText("Tipo o modelo...")
        self.input_buscar.setFixedHeight(32)
        self.input_buscar.setStyleSheet("""
            QLineEdit { border: 2px solid #cfd8dc; border-radius: 6px; padding: 5px;
                        background: white; color: black; }
            QLineEdit:focus { border: 2px solid #1976d2; }
        """)
        self.input_buscar.textChanged.connect(self.actualizar)
        busq.addWidget(self.input_buscar)
        layout.addLayout(busq)

        fila = QHBoxLayout()
        fila.setSpacing(8)
        colores = {"Aeroparque": "#1976d2", "Ezeiza": "#00897b"}
        talleres_presentes = sorted(set(e.get('en_stock') for e in self.stock_equipos if e.get('en_stock')))
        for taller in talleres_presentes:
            frame = QFrame()
            frame.setStyleSheet("QFrame { background: white; border-radius: 10px;"
                                " border: 2px solid #cfd8dc; }")
            flay = QVBoxLayout(frame)
            flay.setContentsMargins(8, 8, 8, 8)

            lbl = QLabel(f"🏢 {taller}")
            lbl.setFont(QFont("Arial", 13, QFont.Weight.Bold))
            lbl.setStyleSheet(f"color: {colores[taller]};")
            lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            flay.addWidget(lbl)
            self.labels[taller] = lbl

            tabla = QTableWidget()
            tabla.setColumnCount(3)
            tabla.setHorizontalHeaderLabels(["Tipo", "Modelo", "Cantidad"])
            tabla.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
            tabla.setAlternatingRowColors(True)
            tabla.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
            tabla.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
            tabla.setStyleSheet("""
                QTableWidget { border: 2px solid #cfd8dc; border-radius: 8px; background: white;
                               font-size: 10pt; color: black; }
                QTableWidget::item { padding: 5px; }
                QTableWidget::item:selected { background: #bbdefb; color: #0d47a1; }
                QTableWidget::item:alternate { background: #f5f5f5; }
                QHeaderView::section { background: #78909c; color: white; padding: 6px;
                                       font-weight: bold; border: none; }
            """)
            tabla.horizontalHeader().setSectionResizeMode(
                0, QHeaderView.ResizeMode.ResizeToContents)
            tabla.horizontalHeader().setSectionResizeMode(
                1, QHeaderView.ResizeMode.Stretch)
            tabla.horizontalHeader().setSectionResizeMode(
                2, QHeaderView.ResizeMode.ResizeToContents)
            tabla.doubleClicked.connect(lambda _i, t=taller: self.ver_series(t))
            flay.addWidget(tabla)
            self.tablas[taller] = tabla

            btn = QPushButton("🔢 Ver N° de serie y copiar")
            btn.setFixedHeight(34)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setStyleSheet(f"""
                QPushButton {{ background: {colores[taller]}; color: white; border-radius: 6px;
                               padding: 0 14px; font-weight: bold; font-size: 10pt; }}
                QPushButton:hover {{ background: #0d47a1; }}
            """)
            btn.clicked.connect(lambda _c, t=taller: self.ver_series(t))
            flay.addWidget(btn)

            fila.addWidget(frame, 1)
        layout.addLayout(fila, 1)

    def _agrupar(self, taller, texto):
        """Devuelve [(tipo, modelo, [series...]), ...] agrupado, filtrado."""
        grupos = {}
        for e in self.stock_equipos:
            if e.get("en_stock") != taller:
                continue
            if texto and not (texto in e["tipo"].upper() or texto in e["modelo"].upper()):
                continue
            grupos.setdefault((e["tipo"], e["modelo"]), []).append(e["numero_serie"])
        # ordenar por tipo, luego cantidad desc
        return sorted(([t, m, s] for (t, m), s in grupos.items()),
                      key=lambda r: (r[0], -len(r[2])))

    def actualizar(self, *_):
        texto = self.input_buscar.text().strip().upper()
        talleres_presentes = sorted(set(e.get('en_stock') for e in self.stock_equipos if e.get('en_stock')))
        for taller in talleres_presentes:
            filas = self._agrupar(taller, texto)
            self.mapa_filas[taller] = filas
            total = sum(len(f[2]) for f in filas)
            self.labels[taller].setText(
                f"🏢 {taller}  —  {total} equipos sin asignar  ·  {len(filas)} tipo/modelo")
            tabla = self.tablas[taller]
            tabla.setRowCount(len(filas))
            for i, (tipo, modelo, series) in enumerate(filas):
                it_t = QTableWidgetItem(tipo)
                it_m = QTableWidgetItem(modelo)
                it_c = QTableWidgetItem(str(len(series)))
                for it in (it_t, it_m, it_c):
                    it.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                it_c.setFont(QFont("Arial", 10, QFont.Weight.Bold))
                tabla.setItem(i, 0, it_t)
                tabla.setItem(i, 1, it_m)
                tabla.setItem(i, 2, it_c)

    def ver_series(self, taller):
        tabla = self.tablas[taller]
        fila = tabla.currentRow()
        filas = self.mapa_filas.get(taller, [])
        if fila < 0 or fila >= len(filas):
            QMessageBox.warning(self, "⚠️ Sin selección",
                                f"Seleccioná un tipo/modelo de la tabla de {taller}.")
            return
        tipo, modelo, series = filas[fila]
        DialogoSeries(f"{tipo} · {modelo}  ({taller})", series, parent=self).exec()


# ═══════════════════════════════════════════════════════════
#  SUB-PESTAÑA 2: INCIDENCIAS
# ═══════════════════════════════════════════════════════════
class IncidenciasTab(ApiTab):
    def __init__(self, api=None, equipos=None):
        super().__init__(api)
        self.api = api
        self.datos_incidencias = equipos
        self.datos_anios = []
        self.crear_interfaz()
        self.llenar_desplegables()
        self.actualizar()
        

    def crear_interfaz(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(8)

        # Filtros
        filtros = QHBoxLayout()
        filtros.setSpacing(10)

        estilo_combo = """
            QComboBox {
                border: 2px solid #cfd8dc; 
                border-radius: 6px; 
                padding: 2px 6px;
                min-width: 100px; 
                background-color: white; 
                color: black; 
                font-size: 9pt;
            }
            QComboBox:hover { 
                border: 2px solid #1976d2; 
                color: black;
            }
            QComboBox QAbstractItemView {
                background-color: white; 
                color: black;
                selection-background-color: #1976d2; 
                selection-color: white;
            }
            QComboBox QAbstractItemView::item {
                color: black;
                background-color: white;
            }
            """

        filtros.addWidget(self._lbl("Año:"))
        self.combo_anio = QComboBox()
        self.combo_anio.setFixedHeight(28)
        self.combo_anio.setStyleSheet(estilo_combo)
        self.combo_anio.currentTextChanged.connect(self.actualizar)
        filtros.addWidget(self.combo_anio)

        filtros.addWidget(self._lbl("Escala:"))
        self.combo_escala = _combo(["Total"] + sorted(ESCALAS), NARANJA)
        self.combo_escala.currentTextChanged.connect(self.actualizar)
        filtros.addWidget(self.combo_escala)

        filtros.addWidget(self._lbl("Modelo (repuestos):"))
        self.combo_modelo = _combo(sorted(REPUESTOS_POR_MODELO.keys()), NARANJA)
        self.combo_modelo.currentTextChanged.connect(self.actualizar)
        filtros.addWidget(self.combo_modelo)

        filtros.addStretch()
        layout.addLayout(filtros)

        # Gráficos
        fila = QHBoxLayout()
        fila.setSpacing(8)

        f_tipo = _frame_grafico("Incidencias por Tipo de Equipo")
        self.canvas_tipo = GraficoCanvas(width=5, height=4)
        f_tipo.layout().addWidget(self.canvas_tipo)
        fila.addWidget(f_tipo, 1)

        f_rep = _frame_grafico("Repuestos utilizados (por modelo)")
        self.canvas_rep = GraficoCanvas(width=5, height=4)
        f_rep.layout().addWidget(self.canvas_rep)
        fila.addWidget(f_rep, 1)

        layout.addLayout(fila, 1)

    def _lbl(self, txt):
        l = QLabel(txt)
        l.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        l.setStyleSheet("color: #37474f;")
        return l

    def actualizar(self):
        anio = self.combo_anio.currentText()
        escala = self.combo_escala.currentText()
        modelo = self.combo_modelo.currentText()
        if anio == "Total" or not anio:
            anios = [int(d["anio"]) for d in self.datos_anios] if self.datos_anios else []
        else:
            anios = [int(anio)]

        # Incidencias por tipo (filtra escala + año)
        por_tipo = {}
        for inc in self.datos_incidencias:
            if escala != "Todos" and inc["escala"] != escala:
                continue
            if anio != "Total" and inc["anio"] != int(anio):
                continue
            por_tipo[inc["tipo"]] = por_tipo.get(inc["tipo"], 0) + 1
        barras_horizontales(self.canvas_tipo, por_tipo, color=NARANJA, unidad="incid.")

        # Repuestos por modelo elegido (filtra escala + año)
        acum = {}
        for a in anios:
            for r, c in _uso_repuestos(modelo, a, None if escala == "Todos" else escala).items():
                acum[r] = acum.get(r, 0) + c
        barras_horizontales(self.canvas_rep, acum, color="#fb8c00",
                            unidad="usos", titulo=modelo)
        
    def llenar_desplegables(self):
        """Llena todos los combos de la pestaña"""
        self.combo_escala.blockSignals(True)
        self.combo_anio.blockSignals(True)

        self.llenar_combo("escalas.php", self.combo_escala, "escala", incluir_todos=True)
        self.datos_anios = self.llenar_combo(
        "anios.php", self.combo_anio, "anio", incluir_total=True
        )

        self.combo_escala.blockSignals(False)
        self.combo_anio.blockSignals(False)


# ═══════════════════════════════════════════════════════════
#  SUB-PESTAÑA 3: DADOS DE BAJA
# ═══════════════════════════════════════════════════════════
class DadosDeBajaTab(ApiTab):
    def __init__(self, api=None, equipos=None):
        super().__init__(api)
        self.api = api
        self.equipos_bajas = equipos
        self.crear_interfaz()
        self.llenar_desplegables()
        self.actualizar()

    def crear_interfaz(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(8)

        filtros = QHBoxLayout()
        l = QLabel("Filtrar por año:")
        l.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        l.setStyleSheet("color: #37474f;")
        filtros.addWidget(l)
        estilo_combo = """
                    QComboBox {
                        border: 2px solid #cfd8dc; 
                        border-radius: 6px; 
                        padding: 2px 6px;
                        min-width: 100px; 
                        background-color: white; 
                        color: black; 
                        font-size: 9pt;
                    }
                    QComboBox:hover { 
                        border: 2px solid #1976d2; 
                        color: black;
                    }
                    QComboBox QAbstractItemView {
                        background-color: white; 
                        color: black;
                        selection-background-color: #1976d2; 
                        selection-color: white;
                    }
                    QComboBox QAbstractItemView::item {
                        color: black;
                        background-color: white;
                    }
                    """
        
        self.combo_anio = QComboBox()
        self.combo_anio.setFixedHeight(28)
        self.combo_anio.setStyleSheet(estilo_combo)
        self.combo_anio.currentTextChanged.connect(self.actualizar)
        filtros.addWidget(self.combo_anio)
        filtros.addStretch()
        layout.addLayout(filtros)

        fila = QHBoxLayout()
        fila.setSpacing(8)

        f_mod = _frame_grafico("Dados de Baja por Modelo")
        self.canvas_modelo = GraficoCanvas(width=5, height=4)
        f_mod.layout().addWidget(_grafico_con_scroll(self.canvas_modelo))
        fila.addWidget(f_mod, 1)

        f_esc = _frame_grafico("Dados de Baja por Escala")
        self.canvas_escala = GraficoCanvas(width=5, height=4)
        f_esc.layout().addWidget(_grafico_con_scroll(self.canvas_escala))
        fila.addWidget(f_esc, 1)

        layout.addLayout(fila, 1)

    def actualizar(self):
        anio = self.combo_anio.currentText()
        bajas = [e for e in self.equipos_bajas if e["anio_baja"] is not None
                 and (anio == "Total" or e["anio_baja"] == int(anio))]

        por_modelo = {}
        por_escala = {}
        for e in bajas:
            por_modelo[e["modelo"]] = por_modelo.get(e["modelo"], 0) + 1
            por_escala[e["escala"]] = por_escala.get(e["escala"], 0) + 1

        ajustar_alto_scroll(self.canvas_modelo, len(por_modelo))
        barras_horizontales(self.canvas_modelo, por_modelo, color=ROJO, unidad="bajas")
        ajustar_alto_scroll(self.canvas_escala, len(por_escala))
        barras_horizontales(self.canvas_escala, por_escala, color="#e53935", unidad="bajas")

    def llenar_desplegables(self):
            """Llena todos los combos de la pestaña"""
            self.combo_anio.blockSignals(True)

            self.llenar_combo(
            "anios.php", self.combo_anio, "anio", incluir_total=True
            )

            self.combo_anio.blockSignals(False)


# ═══════════════════════════════════════════════════════════
#  PESTAÑA PRINCIPAL
# ═══════════════════════════════════════════════════════════
class EstadisticasTab(ApiTab):
    def __init__(self, api=None):
        super().__init__(api)
        self.api = api
        self.equipos_data = self.obtener_equipos() 
        self.equipos_stock = self.obtener_stock()
        self.equipos_incidencias = self.obtener_incidencias()
        self.equipos_bajas = self.obtener_bajas()
        self.crear_interfaz()
        self.cargar_resumen()

    def crear_interfaz(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(6)

        header = QLabel("📊 ESTADÍSTICAS")
        header.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        header.setAlignment(Qt.AlignmentFlag.AlignCenter)
        header.setFixedHeight(36)
        header.setStyleSheet("""
            QLabel { background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                        stop:0 #1565c0, stop:1 #1976d2);
                     color: white; padding: 4px; border-radius: 8px;
                     border: 2px solid #0d47a1; }
        """)
        layout.addWidget(header)

        # Tira compacta de tarjetas
        layout.addWidget(self.crear_tira_resumen())

        # Sub-pestañas
        self.tabs = QTabWidget()
        self.tabs.setStyleSheet("""
            QTabWidget::pane { border: 2px solid #cfd8dc; border-radius: 8px; background: white; }
            QTabBar::tab { background: #eceff1; color: #37474f; padding: 6px 14px;
                           margin-right: 2px; border-top-left-radius: 8px;
                           border-top-right-radius: 8px; font-weight: bold; font-size: 9pt; }
            QTabBar::tab:selected { background: #1976d2; color: white; }
            QTabBar::tab:hover { background: #90caf9; }
        """)
        self.tabs.addTab(DistribucionTab(self.api, self.equipos_data), "📊 Distribución")
        self.tabs.addTab(EnStockTab(self.api, self.equipos_stock), "📦 En Stock")
        self.tabs.addTab(IncidenciasTab(self.api, self.equipos_incidencias), "⚠️ Incidencias")
        self.tabs.addTab(DadosDeBajaTab(self.api, self.equipos_bajas), "🗑️ Dados de Baja")
        layout.addWidget(self.tabs, 1)

    def crear_tira_resumen(self):
        """Tira horizontal compacta (número al lado del texto)."""
        cont = QFrame()
        cont.setFixedHeight(46)
        cont.setStyleSheet("QFrame { background: transparent; }")
        fila = QHBoxLayout(cont)
        fila.setContentsMargins(0, 0, 0, 0)
        fila.setSpacing(8)

        anio_concurrente = datetime.now().year

        # Desempaquetamos (frame, label) en dos variables cada vez.
        chip_total, self.lbl_total = self._chip("📦 Total de equipos", "—", "#1976d2")
        chip_mov, self.lbl_mov = self._chip(f"🔄 Movimientos {anio_concurrente}", "—", "#f57c00")
        chip_taller, self.lbl_taller = self._chip("🔧 En taller", "—", "#7b1fa2")
        chip_baja, self.lbl_baja = self._chip("🗑️ Dados de baja", "—", "#c62828")

        for chip in (chip_total, chip_mov, chip_taller, chip_baja):
            fila.addWidget(chip)
        return cont

    def _chip(self, titulo, valor, color):
        frame = QFrame()
        frame.setStyleSheet(f"""
            QFrame {{ background: white; border-left: 5px solid {color};
                      border-radius: 8px; }}
        """)
        lay = QHBoxLayout(frame)
        lay.setContentsMargins(10, 3, 10, 3)
        lay.setSpacing(8)
        lbl_t = QLabel(titulo)
        lbl_t.setFont(QFont("Arial", 9, QFont.Weight.Bold))
        lbl_t.setStyleSheet(f"color: {color};")
        lay.addWidget(lbl_t)
        lay.addStretch()
        lbl_v = QLabel(valor)
        lbl_v.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        lbl_v.setStyleSheet("color: #37474f;")
        lay.addWidget(lbl_v)
        return frame, lbl_v

    def cargar_resumen(self):

        try:
            datos = self.api.get("estadisticas_resumen.php")

            self.lbl_total.setText(str(datos.get("total_equipos", 0)))
            self.lbl_mov.setText(str(datos.get("movimientos", 0)))
            self.lbl_taller.setText(str(datos.get("en_taller", 0)))
            self.lbl_baja.setText(str(datos.get("dados_baja", 0)))

        except SesionExpirada:
                    QMessageBox.warning(self, "Sesión expirada",
                        "Tu sesión venció. Cerrá y volvé a iniciar sesión.")
        except ApiError as e:
                    QMessageBox.critical(self, "Error",
                        f"No se pudieron cargar las estadísticas:\n{e}")

    def obtener_equipos(self):
        try:
            return self.api.get("estadistica_equipos.php")
        except SesionExpirada:
            QMessageBox.warning(self, "Sesión expirada",
                "Tu sesión venció. Cerrá y volvé a iniciar sesión.")
            return []
        except ApiError as e:
            QMessageBox.critical(self, "Error",
                f"Error al obtener equipos:\n{e}")
            return[]

    def obtener_stock(self):
        try:
            return self.api.get("estadistica_stock.php")
        except SesionExpirada:
            QMessageBox.warning(self, "Sesión expirada",
                "Tu sesión venció. Cerrá y volvé a iniciar sesión.")
            return []
        except ApiError as e:
            QMessageBox.critical(self, "Error",
                f"Error al obtener equipos:\n{e}")
            return[]

    def obtener_incidencias(self):
        try:
            return self.api.get("estadistica_incidencias.php")
        except SesionExpirada:
            QMessageBox.warning(self, "Sesión expirada",
                "Tu sesión venció. Cerrá y volvé a iniciar sesión.")
            return []
        except ApiError as e:
            QMessageBox.critical(self, "Error",
                f"Error al obtener equipos:\n{e}")
            return[]

    def obtener_bajas(self):
        try:
            return self.api.get("estadistica_bajas.php")
        except SesionExpirada:
            QMessageBox.warning(self, "Sesión expirada",
                "Tu sesión venció. Cerrá y volvé a iniciar sesión.")
            return []
        except ApiError as e:
            QMessageBox.critical(self, "Error",
                f"Error al obtener equipos:\n{e}")
            return[]


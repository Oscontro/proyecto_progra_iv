"""
Sistema de Inventario de Equipos de Radio - Solo Interfaz Gráfica
Versión: 3.1 - GUI ONLY
Fecha: 2025-12-13
Usuario: lucasarsa2015-cpu
Tecnología: Python 3.11+ / PyQt6
Descripción: Interfaz gráfica limpia sin lógica de negocio.
"""

import sys
import requests
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QComboBox, QPushButton, QTextEdit,
    QDialog, QTableWidget, QTableWidgetItem, QSpinBox, QCheckBox,
    QHeaderView, QFrame, QGridLayout, QTabWidget, QScrollArea, QSizePolicy
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont

# --- CLASES DE DIÁLOGO Y VENTANAS SECUNDARIAS ---


class ProgramacionDialog(QDialog):
    """Ventana Modal para Programación de Frecuencias y Canales (Solo GUI)"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Programación de Frecuencias y Canales")
        self.setModal(True)
        self.showMaximized()
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()

        # --- Sección: Cantidad de Canales ---
        top_widget = QWidget()
        top_widget.setStyleSheet("background-color: #d5dce0; padding: 15px;")
        top_layout = QHBoxLayout()

        label_cant = QLabel("Cantidad de Canales:")
        label_cant.setFont(QFont("Arial", 13, QFont.Weight.Bold))
        label_cant.setStyleSheet("color: #1a1a1a;")
        top_layout.addWidget(label_cant)

        self.spin_canales = QSpinBox()
        self.spin_canales.setMinimum(1)
        self.spin_canales.setMaximum(999)
        self.spin_canales.setValue(16)  # Valor por defecto visual
        self.spin_canales.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        self.spin_canales.setFixedSize(100, 40)
        self.spin_canales.setStyleSheet("""
            QSpinBox {
                border: 2px solid #7f8c8d;
                border-radius: 5px;
                padding: 5px;
                background-color: #ecf0f1;
            }
            QSpinBox:focus {
                border: 2px solid #0074c9;
                background-color: white;
            }
        """)
        top_layout.addWidget(self.spin_canales)

        btn_generar = QPushButton("Generar Tabla")
        # Sin lógica conectada
        btn_generar.setFont(QFont("Arial", 13, QFont.Weight.Bold))
        btn_generar.setFixedSize(150, 40)
        btn_generar.setStyleSheet("""
            QPushButton {
                background-color: #005a9c;
                color: white;
                border-radius: 5px;
                border: none;
            }
            QPushButton:hover {
                background-color: #003d6b;
            }
        """)
        top_layout.addWidget(btn_generar)

        top_layout.addStretch()
        top_widget.setLayout(top_layout)
        layout.addWidget(top_widget)

        # --- Tabla de Canales ---
        self.tabla_canales = QTableWidget()
        self.tabla_canales.setColumnCount(5)
        self.tabla_canales.setHorizontalHeaderLabels([
            "Canal #", "TX (MHz)", "RX (MHz)", "Codificación (SQL/DPL/TPL)", "Código"
        ])

        # Estilo de la tabla
        self.tabla_canales.setStyleSheet("""
            QTableWidget {
                border: 1px solid #7f8c8d;
                gridline-color: #95a5a6;
                font-family: Arial;
                font-size: 13pt;
                font-weight: bold;
                background-color: #ecf0f1;
            }
            QTableWidget::item {
                padding: 8px;
            }
            QTableWidget::item:alternate {
                background-color: #dfe6e9;
            }
            QHeaderView::section {
                background-color: #2c3e50;
                color: white;
                font-family: Arial;
                font-size: 13pt;
                font-weight: bold;
                padding: 10px;
                border: none;
            }
        """)

        # Ajustes visuales de columnas
        header = self.tabla_canales.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.Stretch)
        self.tabla_canales.verticalHeader().setDefaultSectionSize(50)
        self.tabla_canales.setAlternatingRowColors(True)

        # Ejemplo visual de una fila (sin lógica de generación dinámica real)
        self.tabla_canales.setRowCount(1)
        item_canal = QTableWidgetItem("1")
        item_canal.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        self.tabla_canales.setItem(0, 0, item_canal)

        layout.addWidget(self.tabla_canales)

        # --- Botones de Plantillas ---
        plantillas_layout = QHBoxLayout()
        plantillas_layout.addStretch()

        btn_cargar_plantilla = QPushButton("📂 Cargar Programación Existente")
        btn_cargar_plantilla.setFont(QFont("Arial", 13, QFont.Weight.Bold))
        btn_cargar_plantilla.setFixedSize(280, 45)
        btn_cargar_plantilla.setStyleSheet("""
            QPushButton {
                background-color: #7f8c8d;
                color: white;
                border-radius: 5px;
                border: none;
            }
            QPushButton:hover {
                background-color: #5d6d7e;
            }
        """)
        plantillas_layout.addWidget(btn_cargar_plantilla)

        btn_guardar_plantilla = QPushButton("💾 Guardar como Plantilla")
        btn_guardar_plantilla.setFont(QFont("Arial", 13, QFont.Weight.Bold))
        btn_guardar_plantilla.setFixedSize(250, 45)
        btn_guardar_plantilla.setStyleSheet("""
            QPushButton {
                background-color: #d68910;
                color: white;
                border-radius: 5px;
                border: none;
            }
            QPushButton:hover {
                background-color: #b36b0e;
            }
        """)
        plantillas_layout.addWidget(btn_guardar_plantilla)

        plantillas_layout.addStretch()
        layout.addLayout(plantillas_layout)

        # --- Botones Aceptar/Cancelar ---
        botones_layout = QHBoxLayout()
        botones_layout.addStretch()

        btn_cancelar = QPushButton("Cancelar")
        btn_cancelar.clicked.connect(self.reject)  # Cierra la ventana
        btn_cancelar.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        btn_cancelar.setFixedSize(130, 45)
        btn_cancelar.setStyleSheet("""
            QPushButton {
                background-color: #c0392b;
                color: white;
                border-radius: 5px;
                border: none;
            }
            QPushButton:hover {
                background-color: #922b21;
            }
        """)
        botones_layout.addWidget(btn_cancelar)

        btn_aceptar = QPushButton("Aceptar")
        btn_aceptar.clicked.connect(self.accept)  # Cierra la ventana
        btn_aceptar.setDefault(True)
        btn_aceptar.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        btn_aceptar.setFixedSize(130, 45)
        btn_aceptar.setStyleSheet("""
            QPushButton {
                background-color: #1e8449;
                color: white;
                border-radius: 5px;
                border: none;
            }
            QPushButton:hover {
                background-color: #186a3b;
            }
        """)
        botones_layout.addWidget(btn_aceptar)

        layout.addLayout(botones_layout)
        self.setLayout(layout)


# --- PESTAÑA PRINCIPAL: INGRESO DE EQUIPOS ---

class IngresoEquiposTab(QWidget):
    """Pestaña: Ingreso de Equipos (Diseño Visual)"""

    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        # Layout principal con scroll
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(20)

        # --- Header con título y logo (Placeholder) ---
        header_widget = QWidget()
        header_widget.setFixedHeight(80)
        header_layout = QHBoxLayout()
        header_layout.setContentsMargins(0, 0, 0, 0)

        titulo = QLabel("📥 INGRESO DE EQUIPOS")
        titulo.setFont(QFont("Arial", 20, QFont.Weight.Bold))
        titulo.setAlignment(Qt.AlignmentFlag.AlignLeft |
                            Qt.AlignmentFlag.AlignVCenter)
        titulo.setStyleSheet("""
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                stop:0 #005a9c, stop:1 #003d6b);
            color: white;
            padding: 15px;
            border-radius: 8px;
        """)
        titulo.setSizePolicy(QSizePolicy.Policy.Expanding,
                             QSizePolicy.Policy.Fixed)
        header_layout.addWidget(titulo, 1)

        # Logo Placeholder
        self.logo_label = QLabel("LOGO")
        self.logo_label.setFixedSize(220, 70)
        self.logo_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.logo_label.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        self.logo_label.setStyleSheet("""
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                stop:0 #005a9c, stop:1 #003d6b);
            border-radius: 8px;
            padding: 5px;
            color: white;
        """)
        header_layout.addWidget(self.logo_label)
        header_widget.setLayout(header_layout)
        main_layout.addWidget(header_widget)

        # --- Scroll Area ---
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)

        # Contenedor principal
        form_widget = QWidget()
        form_widget_layout = QHBoxLayout()
        form_widget_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # --- Frame principal en 2 COLUMNAS ---
        form_frame = QFrame()
        form_frame.setMinimumWidth(1100)
        form_frame.setMaximumWidth(1400)
        form_frame.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
        form_frame.setStyleSheet("""
            QFrame {
                background-color: #dfe6e9;
                border-radius: 10px;
                border: 2px solid #34495e;
            }
        """)

        # Layout principal: 2 columnas
        main_form_layout = QHBoxLayout()
        main_form_layout.setContentsMargins(30, 25, 30, 25)
        main_form_layout.setSpacing(30)

        # === COLUMNA IZQUIERDA: FORMULARIO ===
        left_column = QWidget()
        left_column.setMinimumWidth(500)
        left_column.setMaximumWidth(650)
        form_layout = QGridLayout()
        form_layout.setSpacing(15)
        form_layout.setContentsMargins(0, 0, 0, 0)
        form_layout.setColumnMinimumWidth(0, 140)
        form_layout.setColumnStretch(1, 1)

        label_font = QFont("Arial", 13, QFont.Weight.Bold)
        input_font = QFont("Arial", 14, QFont.Weight.Bold)

        input_style = """
            QComboBox, QLineEdit {
                border: 2px solid #7f8c8d;
                border-radius: 5px;
                padding: 8px;
                background-color: #ecf0f1;
            }
            QComboBox:focus, QLineEdit:focus {
                border: 2px solid #0074c9;
                background-color: white;
            }
        """

        row = 0

        # Tipo de equipo
        lbl = QLabel("Tipo de equipo:")
        lbl.setFont(label_font)
        lbl.setStyleSheet("color: #1a1a1a;")
        lbl.setAlignment(Qt.AlignmentFlag.AlignRight |
                         Qt.AlignmentFlag.AlignVCenter)
        form_layout.addWidget(lbl, row, 0)

        self.combo_tipo = QComboBox()
        self.combo_tipo.setEditable(True)
        self.combo_tipo.addItems(
            ["Handheld", "Móvil", "Base", "Repetidor", "Gateway"])
        self.combo_tipo.setFont(input_font)
        self.combo_tipo.setFixedHeight(45)
        self.combo_tipo.setStyleSheet(input_style)
        form_layout.addWidget(self.combo_tipo, row, 1)
        row += 1

        # Modelo
        lbl = QLabel("Modelo:")
        lbl.setFont(label_font)
        lbl.setStyleSheet("color: #1a1a1a;")
        lbl.setAlignment(Qt.AlignmentFlag.AlignRight |
                         Qt.AlignmentFlag.AlignVCenter)
        form_layout.addWidget(lbl, row, 0)

        self.combo_modelo = QComboBox()
        self.combo_modelo.setEditable(True)
        self.combo_modelo.addItems(
            ["IC-A120", "EP450", "DGP8550", "XTS2500", "TK-3207", "IC-F3161"])
        self.combo_modelo.setFont(input_font)
        self.combo_modelo.setFixedHeight(45)
        self.combo_modelo.setStyleSheet(input_style)
        form_layout.addWidget(self.combo_modelo, row, 1)
        row += 1

        # N° de Serie
        lbl = QLabel("N° de Serie:")
        lbl.setFont(label_font)
        lbl.setStyleSheet("color: #c0392b;")
        lbl.setAlignment(Qt.AlignmentFlag.AlignRight |
                         Qt.AlignmentFlag.AlignVCenter)
        form_layout.addWidget(lbl, row, 0)

        self.input_serie = QLineEdit()
        self.input_serie.setPlaceholderText("ABC123XYZ")
        self.input_serie.setFont(input_font)
        self.input_serie.setFixedHeight(45)
        self.input_serie.setStyleSheet("""
            QLineEdit {
                border: 2px solid #c0392b;
                border-radius: 5px;
                padding: 8px;
                background-color: #fadbd8;
            }
            QLineEdit:focus {
                border: 2px solid #922b21;
                background-color: white;
            }
        """)
        form_layout.addWidget(self.input_serie, row, 1)
        row += 1

        # Escala
        lbl = QLabel("Escala:")
        lbl.setFont(label_font)
        lbl.setStyleSheet("color: #1a1a1a;")
        lbl.setAlignment(Qt.AlignmentFlag.AlignRight |
                         Qt.AlignmentFlag.AlignVCenter)
        form_layout.addWidget(lbl, row, 0)

        self.combo_escala = QComboBox()
        self.combo_escala.setEditable(True)
        self.combo_escala.addItems(["COM", "SEG", "LOG", "OPE", "ADM"])
        self.combo_escala.setFont(input_font)
        self.combo_escala.setFixedHeight(45)
        self.combo_escala.setStyleSheet(input_style)
        form_layout.addWidget(self.combo_escala, row, 1)
        row += 1

        # Sector
        lbl = QLabel("Sector:")
        lbl.setFont(label_font)
        lbl.setStyleSheet("color: #1a1a1a;")
        lbl.setAlignment(Qt.AlignmentFlag.AlignRight |
                         Qt.AlignmentFlag.AlignVCenter)
        form_layout.addWidget(lbl, row, 0)

        self.combo_sector = QComboBox()
        self.combo_sector.setEditable(True)
        self.combo_sector.addItems(
            ["Logística", "Seguridad", "Operaciones", "Mantenimiento"])
        self.combo_sector.setFont(input_font)
        self.combo_sector.setFixedHeight(45)
        self.combo_sector.setStyleSheet(input_style)
        form_layout.addWidget(self.combo_sector, row, 1)
        row += 1

        # Estado
        lbl = QLabel("Estado:")
        lbl.setFont(label_font)
        lbl.setStyleSheet("color: #1a1a1a;")
        lbl.setAlignment(Qt.AlignmentFlag.AlignRight |
                         Qt.AlignmentFlag.AlignVCenter)
        form_layout.addWidget(lbl, row, 0)

        self.combo_estado = QComboBox()
        self.combo_estado.setEditable(True)
        self.combo_estado.addItems(
            ["Operativo", "En Stock", "En Reparación", "De Baja"])
        self.combo_estado.setFont(input_font)
        self.combo_estado.setFixedHeight(45)
        self.combo_estado.setStyleSheet(input_style)
        form_layout.addWidget(self.combo_estado, row, 1)
        row += 1

        # Programación
        lbl = QLabel("Programación:")
        lbl.setFont(label_font)
        lbl.setStyleSheet("color: #1a1a1a;")
        lbl.setAlignment(Qt.AlignmentFlag.AlignRight |
                         Qt.AlignmentFlag.AlignVCenter)
        form_layout.addWidget(lbl, row, 0)

        prog_container = QWidget()
        prog_layout = QVBoxLayout()
        prog_layout.setContentsMargins(0, 0, 0, 0)
        prog_layout.setSpacing(5)

        self.btn_programacion = QPushButton("⚙ Configurar Canales")
        self.btn_programacion.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        self.btn_programacion.setFixedHeight(45)
        self.btn_programacion.setStyleSheet("""
            QPushButton {
                background-color: #7d3c98;
                color: white;
                border-radius: 5px;
                border: none;
            }
            QPushButton:hover {
                background-color: #5b2c6f;
            }
        """)
        # Abre el diálogo solo para ver la interfaz
        self.btn_programacion.clicked.connect(
            lambda: ProgramacionDialog(self).exec())
        prog_layout.addWidget(self.btn_programacion)

        self.label_prog_info = QLabel("(No configurado)")
        self.label_prog_info.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        self.label_prog_info.setStyleSheet(
            "color: #c0392b; font-style: italic;")
        prog_layout.addWidget(self.label_prog_info)

        prog_container.setLayout(prog_layout)
        form_layout.addWidget(prog_container, row, 1)
        row += 1

        # Potencia
        lbl = QLabel("Potencia:")
        lbl.setFont(label_font)
        lbl.setStyleSheet("color: #1a1a1a;")
        lbl.setAlignment(Qt.AlignmentFlag.AlignRight |
                         Qt.AlignmentFlag.AlignVCenter)
        form_layout.addWidget(lbl, row, 0)

        self.combo_potencia = QComboBox()
        self.combo_potencia.setEditable(True)
        self.combo_potencia.addItems(["1W", "2W", "5W", "25W", "50W", "100W"])
        self.combo_potencia.setFont(input_font)
        self.combo_potencia.setFixedHeight(45)
        self.combo_potencia.setStyleSheet(input_style)
        form_layout.addWidget(self.combo_potencia, row, 1)
        row += 1

        # Observaciones
        lbl = QLabel("Observaciones:")
        lbl.setFont(label_font)
        lbl.setStyleSheet("color: #1a1a1a;")
        lbl.setAlignment(Qt.AlignmentFlag.AlignRight |
                         Qt.AlignmentFlag.AlignTop)
        form_layout.addWidget(lbl, row, 0)

        self.text_observaciones = QTextEdit()
        self.text_observaciones.setPlaceholderText(
            "Observaciones iniciales...")
        self.text_observaciones.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        self.text_observaciones.setMinimumHeight(100)
        self.text_observaciones.setMaximumHeight(120)
        self.text_observaciones.setStyleSheet("""
            QTextEdit {
                border: 2px solid #7f8c8d;
                border-radius: 5px;
                padding: 10px;
                background-color: #ecf0f1;
            }
            QTextEdit:focus {
                border: 2px solid #0074c9;
                background-color: white;
            }
        """)
        form_layout.addWidget(self.text_observaciones, row, 1)

        left_column.setLayout(form_layout)
        main_form_layout.addWidget(left_column)

        # === COLUMNA DERECHA: IMAGEN GRANDE ===
        right_column = QWidget()
        right_column.setMinimumWidth(380)
        right_column.setMaximumWidth(450)
        imagen_layout = QVBoxLayout()
        imagen_layout.setContentsMargins(0, 0, 0, 0)
        imagen_layout.setSpacing(10)

        # Título de la imagen
        titulo_img = QLabel("Vista del Equipo")
        titulo_img.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        titulo_img.setStyleSheet("color: #34495e;")
        titulo_img.setAlignment(Qt.AlignmentFlag.AlignCenter)
        imagen_layout.addWidget(titulo_img)

        # Imagen GRANDE (Placeholder visual)
        self.label_imagen = QLabel("📷\n\nSin imagen\ndisponible")
        self.label_imagen.setFixedSize(450, 450)
        self.label_imagen.setStyleSheet("""
            QLabel {
                border: 4px solid #34495e;
                border-radius: 10px;
                background-color: white;
                padding: 10px;
                color: #7f8c8d;
                font-size: 11pt;
                font-weight: bold;
            }
        """)
        self.label_imagen.setAlignment(Qt.AlignmentFlag.AlignCenter)
        imagen_layout.addWidget(self.label_imagen)

        imagen_layout.addStretch()

        right_column.setLayout(imagen_layout)
        main_form_layout.addWidget(right_column)

        form_frame.setLayout(main_form_layout)
        form_widget_layout.addWidget(form_frame)
        form_widget.setLayout(form_widget_layout)

        scroll.setWidget(form_widget)
        main_layout.addWidget(scroll, 1)

        # --- Botones fijos inferiores ---
        botones_widget = QWidget()
        botones_widget.setFixedHeight(80)
        botones_widget.setStyleSheet(
            "background-color: #d5dce0; border-radius: 8px;")
        botones_layout = QHBoxLayout()
        botones_layout.setContentsMargins(20, 15, 20, 15)

        self.btn_importar = QPushButton("📊 Importar Excel")
        self.btn_importar.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        self.btn_importar.setFixedSize(200, 50)
        self.btn_importar.setStyleSheet("""
            QPushButton {
                background-color: #005a9c;
                color: white;
                border-radius: 8px;
                border: none;
            }
            QPushButton:hover {
                background-color: #003d6b;
            }
        """)
        botones_layout.addWidget(self.btn_importar)

        botones_layout.addStretch()

        self.btn_guardar = QPushButton("✅ Guardar Equipo")
        self.btn_guardar.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        self.btn_guardar.setFixedSize(220, 50)
        self.btn_guardar.setStyleSheet("""
            QPushButton {
                background-color: #1e8449;
                color: white;
                border-radius: 8px;
                border: none;
            }
            QPushButton:hover {
                background-color: #186a3b;
            }
        """)
        botones_layout.addWidget(self.btn_guardar)

        botones_widget.setLayout(botones_layout)
        main_layout.addWidget(botones_widget)

        self.setLayout(main_layout)

# --- OTRAS PESTAÑAS (VISUALES) ---


class BaseTab(QWidget):
    """Clase base para pestañas genéricas"""

    def __init__(self, titulo_texto, icono_texto=""):
        super().__init__()
        layout = QVBoxLayout()
        titulo = QLabel(f"{icono_texto} {titulo_texto}")
        titulo.setFont(QFont("Arial", 20, QFont.Weight.Bold))
        titulo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        titulo.setStyleSheet("""
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #005a9c, stop:1 #003d6b);
            color: white; padding: 15px; border-radius: 8px;
        """)
        layout.addWidget(titulo)
        layout.addStretch()
        self.setLayout(layout)

# Clases derivadas simples para mantener estructura


class InventarioTab(BaseTab):
    def __init__(self): super().__init__("INVENTARIO", "📦")


class TallerTab(BaseTab):
    def __init__(self): super().__init__("TALLER", "🔧")


class VehiculosTab(BaseTab):
    def __init__(self): super().__init__("VEHÍCULOS", "🚗")


class EtiquetasTab(BaseTab):
    def __init__(self): super().__init__("ETIQUETAS", "🏷️")


class PapeleraTab(BaseTab):
    def __init__(self): super().__init__("PAPELERA", "🗑️")


class EstadisticasTab(BaseTab):
    def __init__(self): super().__init__("ESTADÍSTICAS", "📊")


class UltimosMovimientosTab(BaseTab):
    def __init__(self): super().__init__("ÚLTIMOS MOVIMIENTOS", "📋")


class ConfiguracionTab(BaseTab):
    def __init__(self): super().__init__("CONFIGURACIÓN", "⚙️")


class AdministracionTab(BaseTab):
    def __init__(self): super().__init__("ADMINISTRACIÓN", "👤")


# --- VENTANA PRINCIPAL ---

class MainWindow(QMainWindow):
    """Ventana Principal Contenedora"""

    def __init__(self):
        super().__init__()
        self.setWindowTitle(
            "Sistema de Inventario de Equipos de Radio - Interfaz")
        self.setGeometry(100, 50, 1400, 900)
        self.setMinimumSize(1000, 700)

        self.setStyleSheet("""
            QMainWindow {
                background-color: #bdc3c7;
            }
        """)

        # TabWidget principal
        self.tabs = QTabWidget()
        self.tabs.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        self.tabs.setStyleSheet("""
            QTabWidget::pane {
                border: 2px solid #34495e;
                border-radius: 5px;
                background-color: #bdc3c7;
            }
            QTabBar::tab {
                background-color: #7f8c8d;
                color: white;
                padding: 12px 20px;
                margin-right: 2px;
                border-top-left-radius: 5px;
                border-top-right-radius: 5px;
                font-family: Arial;
                font-size: 13pt;
                font-weight: bold;
            }
            QTabBar::tab:selected {
                background-color: #005a9c;
                color: white;
            }
            QTabBar::tab:hover {
                background-color: #34495e;
                color: white;
            }
        """)

        # Agregar pestañas
        self.tabs.addTab(IngresoEquiposTab(), "📥 Ingreso de Equipos")
        self.tabs.addTab(InventarioTab(), "📦 Inventario")
        self.tabs.addTab(TallerTab(), "🔧 Taller")
        self.tabs.addTab(VehiculosTab(), "🚗 Vehículos")
        self.tabs.addTab(EtiquetasTab(), "🏷️ Etiquetas")
        self.tabs.addTab(PapeleraTab(), "🗑️ Papelera")
        self.tabs.addTab(EstadisticasTab(), "📊 Estadísticas")
        self.tabs.addTab(UltimosMovimientosTab(), "📋 Últimos Movimientos")
        self.tabs.addTab(ConfiguracionTab(), "⚙️ Configuración")
        self.tabs.addTab(AdministracionTab(), "👤 Administración")

        self.setCentralWidget(self.tabs)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setFont(QFont("Arial", 12, QFont.Weight.Bold))

    ventana = MainWindow()
    ventana.show()

    sys.exit(app.exec())

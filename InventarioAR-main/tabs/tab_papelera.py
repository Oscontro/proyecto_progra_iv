"""
Pestaña:   Papelera
Versión: 1.0 - COMPLETA
Fecha: 2025-12-15
Autor: lucasarsa2015-cpu
Descripción: Gestión de equipos eliminados (papelera de reciclaje)
"""
import requests
import pandas as pd
import direcciones # type: ignore
from base_tab import ApiTab
from api_client import ApiError, SesionExpirada
from openpyxl import load_workbook
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QFrame, QComboBox, QTableWidget, QTableWidgetItem,
    QHeaderView, QMessageBox, QAbstractItemView, QDialog,
    QTextEdit, QScrollArea, QMenu, QApplication
)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QAction, QFont, QColor, QBrush
from datetime import datetime


# ═══════════════════════════════════════════════════════════
# DIÁLOGO:   VER HISTORIAL
# ═══════════════════════════════════════════════════════════

class DialogoHistorial(QDialog):
    def __init__(self, datos_historial=None, dato_equipo=None, dato_vehiculo=None, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Registros de historial")
        self.resize(1280, 768)
        self.setModal(True)
        
        self.dato_equipo = dato_equipo
        self.dato_vehiculo = dato_vehiculo
        
        if dato_equipo and dato_vehiculo is None:
            self.marca = dato_equipo.get("marca", "")
            self.modelo = dato_equipo.get("modelo_equipo", "")
            self.serie = dato_equipo.get("numero_serie", "")
        else:
            if dato_vehiculo and dato_equipo is None:
                self.tipo = dato_vehiculo.get("tipo", "")
                self.identificacion = dato_vehiculo.get("identificacion", "")
        
        self.API_BASE_URL = direcciones.URL.API_BASE_URL  # URL base de la API
        
        self.crear_interfaz(datos_historial)
        
        
    def crear_interfaz(self, datos_historial):
        # 1. Layout principal donde irá el QScrollArea
        layout_principal = QVBoxLayout(self)
        layout_principal.setContentsMargins(0, 0, 0, 0)
                
        # 2. Contenedor interno y su layout
        contenedor = QWidget()
        layout = QVBoxLayout(contenedor)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        if self.dato_equipo and self.dato_vehiculo is None:
            header = QLabel(f"📜 Historial de {self.marca} {self.modelo} {self.serie}")
        else:
            header = QLabel(f"📜 Historial de {self.tipo} {self.identificacion}")
        header.setFont(QFont("Arial", 18, QFont.Weight.Bold))
        header.setAlignment(Qt.AlignmentFlag.AlignCenter)
        header.setFixedHeight(60)
        header.setStyleSheet("""
            QLabel {
                background-color: #7b1fa2;
                color: white;
                border-radius: 8px;
                padding: 10px;
            }
        """)
        layout.addWidget(header)
        
        # Crear la tabla
        self.tabla = QTableWidget()
        self.tabla.setRowCount(len(datos_historial))
        self.tabla.setColumnCount(len(datos_historial.columns))
        self.tabla.setHorizontalHeaderLabels(datos_historial.columns)
        self.tabla.setHorizontalHeaderLabels([
            "Fecha Evento",
            "Usuario Evento",
            "Tipo Evento",
            "Campo Modificado",
            "Valor Anterior",
            "Valor Nuevo",
            "Observaciones",
            "IP Usuario",            
        ])
        # Alternar colores
        self.tabla.setAlternatingRowColors(True)

        # Estilo
        self.tabla.setStyleSheet("""
            QTableWidget {
                border: 2px solid #cfd8dc;
                border-radius: 8px;
                gridline-color: #eceff1;
                background-color:  white;
                font-size: 11pt;
                color: grey;
            }
            QTableWidget::item {
                padding: 8px;
            }
            QTableWidget::item:selected {
                background-color: #bbdefb;
                color: #0d47a1;
            }
            QTableWidget::item:alternate {
                background-color: #f5f5f5;
            }
            QHeaderView::section {
                background-color: #78909c;
                color: white;
                font-size: 11pt;
                font-weight: bold;
                padding: 10px;
                border: none;
                border-right: 1px solid #607d8b;
            }
            QHeaderView::section:last {
                border-right: none;
            }
            QHeaderView::section: hover {
                background-color: #607d8b;
            }
        """)

        # Configuración de columnas
        header = self.tabla.horizontalHeader()
        header.setSectionResizeMode(
            0, QHeaderView.ResizeMode.ResizeToContents)  # fecha evento
        header.setSectionResizeMode(
            1, QHeaderView.ResizeMode.ResizeToContents)  # usuario evento
        header.setSectionResizeMode(
            2, QHeaderView.ResizeMode.ResizeToContents)  # tipo evento
        header.setSectionResizeMode(
            3, QHeaderView.ResizeMode.ResizeToContents)  # campo modificado
        header.setSectionResizeMode(
            4, QHeaderView.ResizeMode.ResizeToContents)  # valor anterior
        header.setSectionResizeMode(
            5, QHeaderView.ResizeMode.ResizeToContents)  # valor nuevo
        header.setSectionResizeMode(
            6, QHeaderView.ResizeMode.ResizeToContents)  # observaciones
        header.setSectionResizeMode(
            7, QHeaderView.ResizeMode.Stretch)  # ip usuario

        # Altura de filas
        self.tabla.verticalHeader().setDefaultSectionSize(30)

        # Llenar datos
        for i in range(len(datos_historial)):
            for j in range(len(datos_historial.columns)):
                valor = str(datos_historial.iat[i, j]) if pd.notna(datos_historial.iat[i, j]) else ""
                self.tabla.setItem(i, j, QTableWidgetItem(valor))
                
        self.tabla.setHorizontalScrollMode(QAbstractItemView.ScrollMode.ScrollPerPixel)
        self.tabla.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        
        layout.addWidget(self.tabla)
        # 3. Configurar el QScrollArea
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)  # Mantiene el contenido adaptado al ancho
        scroll.setWidget(contenedor)     # Asigna el widget con todo el contenido
        scroll.setStyleSheet("""
        /* Estilo de la barra vertical */
        QScrollBar:vertical {
            border: none;
            background-color: #eceff1;  /* Gris claro de fondo para distinguirla */
            width: 14px;                 /* Ancho para que sea fácil de ver y dar clic */
            margin: 0px;
            border-radius: 7px;
        }

        /* El indicador deslizante de la barra */
        QScrollBar::handle:vertical {
            background-color: #78909c;  /* Mismo tono azulado/grisáceo de las cabeceras */
            min-height: 30px;
            border-radius: 7px;
        }

        /* Color cuando pasas el puntero sobre la barra */
        QScrollBar::handle:vertical:hover {
            background-color: #7b1fa2;  /* Morado, combinado con el encabezado */
        }

        /* Ocultar botones superiores/inferiores si no los usas */
        QScrollBar::sub-line:vertical, QScrollBar::add-line:vertical {
            height: 0px;
        }

        /* Estilo de la barra horizontal (si llegara a aparecer) */
        QScrollBar:horizontal {
            border: none;
            background-color: #eceff1;
            height: 14px;
            margin: 0px;
            border-radius: 7px;
        }
        QScrollBar::handle:horizontal {
            background-color: #78909c;
            min-width: 30px;
            border-radius: 7px;
        }
        QScrollBar::handle:horizontal:hover {
            background-color: #7b1fa2;
        }
        QScrollBar::sub-line:horizontal, QScrollBar::add-line:horizontal {
            width: 0px;
        }
        """)
        # 4. Añadir el scroll al layout principal de la ventana
        layout_principal.addWidget(scroll)
        
        botones_layout = QHBoxLayout()
        botones_layout.setSpacing(15)
        
        btn_cancelar = QPushButton("❌ Cancelar")
        btn_cancelar.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        btn_cancelar.setFixedHeight(45)
        btn_cancelar.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_cancelar.setStyleSheet("""
            QPushButton {
                background-color: #757575;
                color: white;
                border: none;
                border-radius: 8px;
                padding: 0 30px;
            }
            QPushButton:hover {
                background-color: #616161;
            }
        """)
        btn_cancelar.clicked.connect(self.reject) # Cierra el diálogo
        botones_layout.addWidget(btn_cancelar)
        
        btn_aceptar = QPushButton("Aceptar")
        btn_aceptar.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        btn_aceptar.setFixedHeight(45)
        btn_aceptar.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_aceptar.setStyleSheet("""
            QPushButton {
                background:  qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #1e8449, stop:1 #27ae60);
                color: white;
                border: none;
                border-radius: 8px;
                padding: 0 30px;
            }
            QPushButton:hover {
                background:  qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #186a3b, stop:1 #1e8449);
            }
        """)
        btn_aceptar.clicked.connect(self.accept)
        botones_layout.addWidget(btn_aceptar)

        layout.addLayout(botones_layout)



# ═══════════════════════════════════════════════════════════
# PESTAÑA PRINCIPAL:  PAPELERA
# ═══════════════════════════════════════════════════════════

class PapeleraTab(ApiTab):
    """Pestaña de papelera de equipos eliminados"""

    def __init__(self, api, es_administrador=False):
        super().__init__(api)
        self.api = api                                  # ← nuevo, primero
        self.es_administrador = es_administrador  # True si es admin

        self.datos_completos = []  # SIN datos precargados
        self.datos_filtrados = []
        self._actualizando = False
        # (borré self.API_BASE_URL: ya no se usa con self.api)

        self.crear_interfaz()
        self.llenar_desplegables()
        self.obtener_datos_iniciales()  # Cargar datos al iniciar
        
        

    def crear_interfaz(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(15)

        # Header
        header = QLabel("🗑️ PAPELERA")
        header.setFont(QFont("Arial", 20, QFont.Weight.Bold))
        header.setAlignment(Qt.AlignmentFlag.AlignCenter)
        header.setFixedHeight(60)
        header.setStyleSheet("""
            QLabel {
                background:  qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #c62828, stop:1 #e53935);
                color: white;
                padding: 15px;
                border-radius:  10px;
                border: 3px solid #b71c1c;
            }
        """)
        layout.addWidget(header)

        # Búsqueda y filtros
        busqueda_filtros = self.crear_busqueda_filtros()
        layout.addLayout(busqueda_filtros)

        # Tabla
        self.crear_tabla()
        layout.addWidget(self.tabla, 1)

        # Botones inferiores
        botones_layout = self.crear_botones()
        layout.addLayout(botones_layout)

        self.setLayout(layout)
        self.renderizar_tabla()

    def crear_busqueda_filtros(self):
        """Búsqueda y filtros"""
        container_layout = QVBoxLayout()
        container_layout.setSpacing(10)

        # Título
        titulo = QLabel("📋 Equipos Eliminados")
        titulo.setFont(QFont("Arial", 13, QFont.Weight.Bold))
        titulo.setStyleSheet("color: #c62828;")
        container_layout.addWidget(titulo)

        # Búsqueda
        busqueda_layout = QHBoxLayout()
        lbl_buscar = QLabel("🔍 Buscar:")
        lbl_buscar.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        lbl_buscar.setStyleSheet("color: black;")
        busqueda_layout.addWidget(lbl_buscar)

        self.input_buscar = QLineEdit()
        self.input_buscar.setPlaceholderText("N° de Serie...")
        self.input_buscar.setFixedHeight(35)
        self.input_buscar.setStyleSheet("""
            QLineEdit {
                border: 2px solid #cfd8dc;
                border-radius: 6px;
                padding: 6px;
                background-color: white;
                color: black;
            }
            QLineEdit:focus { border: 2px solid #c62828; }
        """)
        self.input_buscar.textChanged.connect(self.aplicar_filtros)
        busqueda_layout.addWidget(self.input_buscar)

        btn_limpiar = QPushButton("🗑️ Limpiar Filtros")
        btn_limpiar.setFixedHeight(35)
        btn_limpiar.setStyleSheet("""
            QPushButton {
                background-color: #757575;
                color: white;
                border-radius: 6px;
                padding: 0 15px;
                font-weight: bold;
            }
            QPushButton:hover { background-color: #616161; }
        """)
        btn_limpiar.clicked.connect(self.limpiar_filtros)
        busqueda_layout.addWidget(btn_limpiar)

        container_layout.addLayout(busqueda_layout)
        
        btn_actualizar = QPushButton("🔁 Actualizar Tabla")
        btn_actualizar.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        btn_actualizar.setFixedHeight(38)
        btn_actualizar.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_actualizar.setStyleSheet("""
            QPushButton {
                background-color: #757575;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 0 20px;
            }
            QPushButton:hover {
                background-color: #616161;
            }
        """)
        btn_actualizar.clicked.connect(self.obtener_datos_iniciales)
        busqueda_layout.addWidget(btn_actualizar)

        # Filtros
        filtros_layout = QHBoxLayout()
        lbl_filtros = QLabel("Filtros:")
        lbl_filtros.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        lbl_filtros.setStyleSheet("color: #37474f;")
        filtros_layout.addWidget(lbl_filtros)

        estilo_combo = """
        QComboBox {
            border: 2px solid #cfd8dc;
            border-radius: 6px;
            padding: 5px;
            min-width: 110px;
            background-color: white;
            color: black;
        }
        QComboBox:hover {
            border: 2px solid #c62828;
        }
        QComboBox QAbstractItemView {
            background-color: white;
            color: black;
            outline: none;
        }
        QComboBox QAbstractItemView::item {
            color: black;
            padding: 5px;
        }
        QComboBox QAbstractItemView::item:selected {
            background-color: #1976d2;
            color: white;
        }
        """
        
        
        #Tipo
        label_tipo = QLabel("Tipo:")
        label_tipo.setStyleSheet("color: black;")
        filtros_layout.addWidget(label_tipo)
        self.combo_filtro_tipo = QComboBox()
        self.combo_filtro_tipo.addItem("Todos")
        self.combo_filtro_tipo.setFixedHeight(32)
        self.combo_filtro_tipo.setStyleSheet(estilo_combo)
        self.combo_filtro_tipo.currentTextChanged.connect(
            lambda: self.aplicar_filtros())
        filtros_layout.addWidget(self.combo_filtro_tipo)
        
        
        #Marca
        label_marca = QLabel("Marca:")
        label_marca.setStyleSheet("color: black;")
        filtros_layout.addWidget(label_marca)
        self.combo_filtro_marca = QComboBox()
        self.combo_filtro_marca.addItem("Todos")
        self.combo_filtro_marca.setFixedHeight(32)
        self.combo_filtro_marca.setStyleSheet(estilo_combo)
        self.combo_filtro_marca.currentTextChanged.connect(
            lambda: self.aplicar_filtros())
        filtros_layout.addWidget(self.combo_filtro_marca)
        
        
        # Escala
        label_escala = QLabel("Escala:")
        label_escala.setStyleSheet("color: black;")
        filtros_layout.addWidget(label_escala)
        self.combo_filtro_escala = QComboBox()
        self.combo_filtro_escala.addItem("Todos")
        self.combo_filtro_escala.setFixedHeight(32)
        self.combo_filtro_escala.setStyleSheet(estilo_combo)
        self.combo_filtro_escala.currentTextChanged.connect(
            lambda: self.aplicar_filtros())
        filtros_layout.addWidget(self.combo_filtro_escala)

        filtros_layout.addStretch()
        container_layout.addLayout(filtros_layout)

        return container_layout

    def crear_tabla(self):
        """Crea la tabla de equipos eliminados"""
        self.tabla = QTableWidget()
        self.tabla.setColumnCount(9)
        self.tabla.hideColumn(0)  # Ocultar columna origen
        self.tabla.hideColumn(1)  # Ocultar columna ID
        self.tabla.setHorizontalHeaderLabels([
            "origen",
            "id_referencia",
            "Tipo",
            "Marca",
            "Modelo",
            "N° Serie",
            "Escala",
            "Sector",
            "Fecha Eliminación"
        ])
        self.tabla.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.tabla.customContextMenuRequested.connect(
            lambda pos: self.mostrar_menu_contextual(self.tabla, pos))

        self.tabla.setEditTriggers(
            QAbstractItemView.EditTrigger.NoEditTriggers)
        self.tabla.setSelectionBehavior(
            QAbstractItemView.SelectionBehavior.SelectRows)
        self.tabla.setSelectionMode(
            QAbstractItemView.SelectionMode.SingleSelection)
        self.tabla.setAlternatingRowColors(True)

        self.tabla.setStyleSheet("""
            QTableWidget {
                border: 2px solid #cfd8dc;
                border-radius: 8px;
                background-color:  white;
                font-size: 10pt;
            }
            QTableWidget::item {
                padding: 8px;
            }
            QTableWidget::item:selected {
                background-color: #ffcdd2;
                color: #b71c1c;
            }
            QTableWidget::item:alternate {
                background-color: #f5f5f5;
            }
            QHeaderView::section {
                background-color: #c62828;
                color: white;
                padding: 10px;
                font-weight: bold;
                border: none;
                border-right: 1px solid #b71c1c;
            }
            QHeaderView::section: last {
                border-right: none;
            }
        """)

        header = self.tabla.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents) # origen oculto
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents) # ID oculto pero importante para operaciones internas
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents) # Tipo
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents) # Marca
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents) # Modelo
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.Stretch) # N° Serie
        header.setSectionResizeMode(6, QHeaderView.ResizeMode.ResizeToContents) # Escala
        header.setSectionResizeMode(7, QHeaderView.ResizeMode.ResizeToContents) # Sector
        header.setSectionResizeMode(8, QHeaderView.ResizeMode.ResizeToContents) # Fecha Eliminación

        self.tabla.verticalHeader().setDefaultSectionSize(45)
        self.tabla.itemSelectionChanged.connect(self.on_seleccion_cambiada)

    def crear_botones(self):
        """Crea los botones inferiores"""
        botones_layout = QHBoxLayout()
        botones_layout.setSpacing(15)

        # BOTONES IZQUIERDA (Técnico y Admin)
        self.btn_historial = QPushButton("📜 Ver Historial")
        self.btn_historial.setEnabled(False)
        self.btn_historial.setFont(QFont("Arial", 11, QFont.Weight.Bold))
        self.btn_historial.setFixedHeight(45)
        self.btn_historial.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_historial.setStyleSheet("""
            QPushButton {
                background-color: #7b1fa2;
                color:  white;
                border-radius:  6px;
                padding:  0 25px;
            }
            QPushButton:hover {
                background-color: #6a1b9a;
            }
            QPushButton:disabled {
                background-color: #cfd8dc;
                color: #90a4ae;
            }
        """)
        self.btn_historial.clicked.connect(self.ver_historial)
        botones_layout.addWidget(self. btn_historial)

        self.btn_restaurar = QPushButton("♻️ Restaurar Item")
        self.btn_restaurar.setEnabled(False)
        self.btn_restaurar. setFont(QFont("Arial", 11, QFont.Weight. Bold))
        self.btn_restaurar.setFixedHeight(45)
        self.btn_restaurar.setCursor(Qt. CursorShape.PointingHandCursor)
        self.btn_restaurar.setStyleSheet("""
            QPushButton {
                background-color: #388e3c;
                color:  white;
                border-radius:  6px;
                padding:  0 25px;
            }
            QPushButton:hover {
                background-color: #2e7d32;
            }
            QPushButton:disabled {
                background-color: #cfd8dc;
                color: #90a4ae;
            }
        """)
        self.btn_restaurar.clicked.connect(self.restaurar_item)
        botones_layout.addWidget(self.btn_restaurar)

        botones_layout.addStretch()

        # BOTÓN DERECHA (Solo Admin)
        if self.es_administrador:
            self.btn_eliminar = QPushButton("🔥 Eliminar de la Base de Datos")
            self.btn_eliminar.setEnabled(False)
            self.btn_eliminar.setFont(QFont("Arial", 11, QFont. Weight.Bold))
            self.btn_eliminar.setFixedHeight(45)
            self.btn_eliminar.setCursor(Qt.CursorShape. PointingHandCursor)
            self.btn_eliminar.setStyleSheet("""
                QPushButton {
                    background-color: #d32f2f;
                    color: white;
                    border-radius: 6px;
                    padding: 0 25px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background-color:  #c62828;
                }
                QPushButton:disabled {
                    background-color: #cfd8dc;
                    color: #90a4ae;
                }
            """)
            self.btn_eliminar. clicked.connect(self.eliminar_definitivo)
            botones_layout. addWidget(self.btn_eliminar)

        return botones_layout

    def renderizar_tabla(self):
        """Carga datos en la tabla"""
        try:
            self.tabla.setRowCount(0)  # Limpiar tabla antes de cargar nuevos datos
            self.tabla.setRowCount(len(self.datos_filtrados))

            for fila, equipo in enumerate(self.datos_filtrados):
                for col, campo in enumerate(['origen','tipo', 'marca', 'modelo_equipo', 'numero_serie', 'escala', 'sector', 'fecha_eliminacion'], 1):
                    valor = equipo.get(campo, '') or '-'
                    item = QTableWidgetItem(str(valor))
                    item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                    item.setFont(QFont("Arial", 10))
                    item.setForeground(QBrush(QColor("black")))
                    self.tabla.setItem(fila, col, item)
                    
        except Exception as e:
            QMessageBox.warning(self, "Error", f"No se pudieron cargar los datos en la tabla:\n{e}")
    
    def obtener_datos_iniciales(self):
        """Obtiene TODOS los datos de la API una sola vez al inicio."""
        self._actualizando = True  # ← Bloquear
        try:
            self.datos_completos = self.api.get("inventario_historial.php")
            self.datos_filtrados = self.datos_completos.copy()
        
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
                f"No se pudieron cargar los datos del inventario:\n{e}")
            self.datos_completos = []
            self.datos_filtrados = []
        finally:
            # En un finally: si algo inesperado falla, el flag no queda
            # trabado en True y la pestaña sigue usable.
            self.renderizar_tabla()
            self._actualizando = False  # ← Desbloquear
            QTimer.singleShot(50, self.renderizar_tabla)

    def aplicar_filtros(self):
        
        if self._actualizando:
            return  # Evitar aplicar filtros mientras se actualizan los datos
        """Aplica filtros a la tabla"""
        self.datos_filtrados = self.datos_completos. copy()

        # Filtro por búsqueda
        texto = self.input_buscar.text().strip().upper()
        if texto:
            self.datos_filtrados = [
                e for e in self.datos_filtrados
                if texto in e.get('numero_serie', '').upper()
            ]

        # Filtro por tipo
        tipo = self.combo_filtro_tipo.currentText()
        if tipo != "Todos":
            self.datos_filtrados = [
                e for e in self.datos_filtrados
                if e.get('tipo', '') == tipo
            ]

        # Filtro por marca
        marca = self.combo_filtro_marca.currentText()
        if marca != "Todos":
            self.datos_filtrados = [
                e for e in self.datos_filtrados
                if e.get('marca', '') == marca
            ]

        # Filtro por escala
        escala = self. combo_filtro_escala. currentText()
        if escala != "Todos":
            self.datos_filtrados = [
                e for e in self.datos_filtrados
                if e.get('escala', '') == escala
            ]

        self.renderizar_tabla()

    def limpiar_filtros(self):
        """Limpia todos los filtros"""
        self.input_buscar.clear()
        self.combo_filtro_tipo.setCurrentIndex(0)
        self.combo_filtro_marca.setCurrentIndex(0)
        self.combo_filtro_escala.setCurrentIndex(0)
        self.datos_filtrados = self.datos_completos.copy()
        #self.cargar_tabla()

    def on_seleccion_cambiada(self):
        """Maneja cambio de selección en tabla"""
        hay_seleccion = len(self.tabla.selectedItems()) > 0
        self.btn_historial.setEnabled(hay_seleccion)
        self.btn_restaurar.setEnabled(hay_seleccion)

        if self.es_administrador:
            self. btn_eliminar.setEnabled(hay_seleccion)

    def get_equipo_seleccionado(self):
        """Retorna el equipo seleccionado"""
        fila = self.tabla.currentRow()
        if fila >= 0 and fila < len(self. datos_filtrados):
            return self.datos_filtrados[fila]
        return None

    def ver_historial(self):
        """Ver historial del equipo"""
        item_seleccionado = self.get_equipo_seleccionado()
        if not item_seleccionado:
            QMessageBox.warning(self, "Aviso", "Debe seleccionar un item de la tabla.")
            return
        origen = item_seleccionado.get("origen", "")

        if origen == "equipo":
            id_equipo = item_seleccionado.get("id_referencia", "")
            try:
                respuesta = self.api.get("historialEquipo.php", {"id_equipo": id_equipo})
                equipo = {
                    "marca" : item_seleccionado.get("marca", ""),
                    "modelo_equipo" : item_seleccionado.get("modelo_equipo", ""),
                    "numero_serie" : item_seleccionado.get("numero_serie", "")
                }
                
                if respuesta:
                    # Convertir la lista de datos a DataFrame
                    #datos = respuesta.get("data", [])
                    datos = respuesta
                    if datos:
                        df_historial = pd.DataFrame(datos)
                        vehiculo = None
                        dialogo = DialogoHistorial(df_historial, equipo, vehiculo, self)
                        dialogo.showMaximized()
                        dialogo.exec()
                    else:
                        QMessageBox.information(self, "Info", "No hay historial para este equipo.")
                else:
                    QMessageBox.warning(self, "Error", respuesta.get("message", "Error desconocido"))
            
            except SesionExpirada:
                QMessageBox.warning(self, "Sesión expirada",
                    "Tu sesión venció. Cerrá y volvé a iniciar sesión.")
            except ApiError as e:
                QMessageBox.critical(self, "Error", f"No se pudo cargar el historial:\n{e}")
        else:
            identificacion = item_seleccionado.get("numero_serie", "")
            try:
                respuesta = self.api.get("historialVehiculos.php", {"identificacion": identificacion})
                vehiculo = {
                    "tipo" : item_seleccionado.get("tipo", ""),
                    "identificacion" : item_seleccionado.get("numero_serie", "")
                }
                
                if respuesta:
                    # Convertir la lista de datos a DataFrame
                    #datos = respuesta.get("data", [])
                    datos = respuesta
                    if datos:
                        df_historial = pd.DataFrame(datos)
                        equipo = None
                        dialogo = DialogoHistorial(df_historial, equipo, vehiculo, self)
                        dialogo.showMaximized()
                        dialogo.exec()
                    else:
                        QMessageBox.information(self, "Info", "No hay historial para este vehiculo.")
                else:
                    QMessageBox.warning(self, "Error", respuesta.get("message", "Error desconocido"))
            
            except SesionExpirada:
                QMessageBox.warning(self, "Sesión expirada",
                    "Tu sesión venció. Cerrá y volvé a iniciar sesión.")
            except ApiError as e:
                QMessageBox.critical(self, "Error", f"No se pudo cargar el historial:\n{e}")
        
            

    def restaurar_item(self):
        """Restaura el equipo al inventario"""
        item_seleccionado = self.get_equipo_seleccionado()
        if not item_seleccionado:
            return
        
        origen =  item_seleccionado.get("origen", "")
        
        if origen == "equipo":
            id_equipo = item_seleccionado.get("id_referencia", "")
            numero_serie = item_seleccionado.get("numero_serie", "")
            modelo = item_seleccionado.get("modelo_equipo", "")

            respuesta = QMessageBox.question(
                self,
                "♻️ Confirmar Restauración",
                f"¿Está seguro que desea restaurar este equipo al inventario?\n\n"
                f"N° Serie: {numero_serie}\n"
                f"Modelo: {modelo}\n\n"
                f"El equipo volverá a estar disponible en el inventario.",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )

            if respuesta == QMessageBox.StandardButton.Yes:
                try:
                    self.api.post("restaurar_equipo.php", datos={
                        "id_equipo": id_equipo
                    })

                        # Eliminar de la tabla
                    self.datos_completos.remove(item_seleccionado)
                    self.datos_filtrados.remove(item_seleccionado)
                    self.renderizar_tabla()
                    QMessageBox.information(
                            self,
                            "✅ Equipo Restaurado",
                            f"El equipo {numero_serie} ha sido restaurado correctamente al inventario."
                    )
                except SesionExpirada:
                    QMessageBox.warning(self, "Sesión expirada",
                        "Tu sesión venció. Cerrá y volvé a iniciar sesión.")
                    return
                except ApiError as e:
                    QMessageBox.critical(self, "Error", f"Restaurar equipo:\n{e}")
                    return
        else:
            id_vehiculo = item_seleccionado.get("id_referencia", "")
            identificacion = item_seleccionado.get("numero_serie", "")
            escala = item_seleccionado.get("escala", "")

            respuesta = QMessageBox.question(
                self,
                "♻️ Confirmar Restauración",
                f"¿Está seguro que desea restaurar este vehiculo?\n\n"
                f"Identificacion: {identificacion}\n"
                f"Escala: {escala}\n\n"
                f"El vehiculo volverá a estar disponbible.",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )

            if respuesta == QMessageBox.StandardButton.Yes:
                try:
                    self.api.post("restaurar_vehiculo.php", datos={
                        "id_vehiculo": id_vehiculo
                    })
                    # Eliminar de la tabla
                    self.datos_completos.remove(item_seleccionado)
                    self.datos_filtrados.remove(item_seleccionado)
                    self.renderizar_tabla()
                    QMessageBox.information(
                            self,
                            "✅ Equipo Restaurado",
                            f"El vehiculo {identificacion} ha sido restaurado correctamente."
                        )
                except SesionExpirada:
                    QMessageBox.warning(self, "Sesión expirada",
                        "Tu sesión venció. Cerrá y volvé a iniciar sesión.")
                    return
                except ApiError as e:
                    QMessageBox.critical(self, "Error", f"Restaurar vehiculo:\n{e}")
                    return



    def eliminar_definitivo(self):
        """Elimina el equipo definitivamente de la base de datos (solo admin)"""
        item_seleccionado = self.get_equipo_seleccionado()
        if not item_seleccionado:
                    return
                
        origen =  item_seleccionado.get("origen", "")
        if origen == "equipo":
            equipo = item_seleccionado
            # Diálogo de confirmación con advertencia grave
            # Agregar input de confirmación
            from PyQt6.QtWidgets import QInputDialog
            texto, ok = QInputDialog.getText(
                self,
                "⚠️ Confirmación Requerida",
                f"🔥 ELIMINAR DEFINITIVAMENTE:\n\n"
                f"N° Serie: {equipo.get('numero_serie', 'N/A')}\n"
                f"Modelo: {equipo.get('modelo_equipo', 'N/A')}\n\n"
                f"⚠️ Esta acción es IRREVERSIBLE.\n"
                f"Todos los datos se perderán permanentemente.\n\n"
                f"Escriba 'ELIMINAR' para confirmar:"
            )

            if ok and texto == "ELIMINAR":
                datos= {"origen": origen, "id_referencia": equipo.get("id_referencia", ""),
                        "numero_serie": equipo.get("numero_serie", "")}
                self.api.post("eliminar_definitivo.php", datos)
                QMessageBox.warning(
                    self,
                    "Equipo Eliminado Definitivamente",
                    f"El equipo {equipo.get('numero_serie', 'N/A')} ha sido eliminado PERMANENTEMENTE de la base de datos.\n\n"
                    f"Esta acción no se puede deshacer."
                )

                # Eliminar de la tabla
                self.datos_completos.remove(equipo)
                self.datos_filtrados.remove(equipo)
                self.renderizar_tabla()
                #self.cargar_tabla()
            elif ok:
                QMessageBox.information(
                    self,
                    "❌ Cancelado",
                    "El texto de confirmación no coincide.\nOperación cancelada."
                )
        else:
            vehiculo = item_seleccionado
            # Diálogo de confirmación con advertencia grave
            from PyQt6.QtWidgets import QInputDialog
            texto, ok = QInputDialog.getText(
                self,
                "⚠️ Confirmación Requerida",
                f"🔥 ELIMINAR DEFINITIVAMENTE:\n\n"
                f"Identificacion: {vehiculo.get('numero_serie', 'N/A')}\n"
                f"Escala: {vehiculo.get('escala', 'N/A')}\n\n"
                f"⚠️ Esta acción es IRREVERSIBLE.\n"
                f"Todos los datos se perderán permanentemente.\n\n"
                f"Escriba 'ELIMINAR' para confirmar:"
            )

            if ok and texto == "ELIMINAR":
                datos= {"origen": origen, "id_referencia": vehiculo.get("id_referencia", ""),
                        "numero_serie": vehiculo.get("numero_serie", "")}
                self.api.post("eliminar_definitivo.php", datos)
                QMessageBox.warning(
                    self,
                    "Vehiculo Eliminado Definitivamente",
                    f"El vehiculo {vehiculo.get('numero_serie', 'N/A')} ha sido eliminado PERMANENTEMENTE de la base de datos.\n\n"
                    f"Esta acción no se puede deshacer."
                )

                # Eliminar de la tabla
                self.datos_completos.remove(vehiculo)
                self.datos_filtrados.remove(vehiculo)
                self.renderizar_tabla()
            elif ok:
                QMessageBox.information(
                    self,
                    "❌ Cancelado",
                    "El texto de confirmación no coincide.\nOperación cancelada."
                )
            
    def llenar_combo(self, endpoint, combo, campo_json, incluir_todos=False, incluir_escriba=False):
            """
            endpoint: Archivo PHP (ej. marcas.php)
            combo: El objeto QComboBox
            campo_json: El nombre de la clave en el JSON (ej. 'marca')
            incluir_todos: Si agrega el item "Todos"
            """
            data = []
    
            try:
                data = self.api.get(endpoint)
    
                # Extraemos la lista de valores
                items = [str(obj[campo_json]) for obj in data]
    
                combo.clear()
                if incluir_todos:
                    combo.addItem("Todos")
                elif incluir_escriba:
                    combo.addItem("Escriba o seleccione")
    
                combo.addItems(items)
    
            except SesionExpirada:
                raise                      # la maneja llenar_desplegables, un solo aviso
            except ApiError as e:
                print(f"Error al cargar {endpoint}: {e}")
            except KeyError as e:
                print(f"Campo '{campo_json}' no encontrado en el JSON: {e}")
            except Exception as e:
                print(f"Error inesperado en {endpoint}: {e}")
    
            return data
    
    def llenar_desplegables(self):
        """Llena todos los combos de la pestaña"""
        self.llenar_combo("tipos.php", self.combo_filtro_tipo, "tipo", incluir_todos=True)
        self.llenar_combo("marcas.php", self.combo_filtro_marca, "marca", incluir_todos=True)
        self.llenar_combo("escalas.php", self.combo_filtro_escala, "escala", incluir_todos=True)
        #self.llenar_combo("tipo_vehiculo.php", self.combo_filtro_tipo, "tipo_vehiculo", incluir_todos=False)
        
    def mostrar_menu_contextual(self, tabla, pos):
        """Muestra menú contextual con opciones de copiar"""
        menu = QMenu(self)
        menu.setStyleSheet("""
            QMenu {
                background-color: white;
                border: 1px solid #cfd8dc;
                border-radius: 4px;
                padding: 5px;
            }
            QMenu::item {
                padding: 8px 25px;
                border-radius: 3px;
                color: black;
            }
            QMenu::item:selected {
                background-color: #e3f2fd;
                color: #1976d2;
            }
        """)

        # Obtener item seleccionado
        item = tabla.itemAt(pos)

        if item:
            # Copiar celda
            accion_copiar_celda = QAction("📋 Copiar celda", self)
            accion_copiar_celda.triggered.connect(
                lambda: self.copiar_celda(tabla))
            menu.addAction(accion_copiar_celda)

            # Copiar fila completa
            accion_copiar_fila = QAction("📄 Copiar fila completa", self)
            accion_copiar_fila.triggered.connect(
                lambda: self.copiar_fila(tabla))
            menu.addAction(accion_copiar_fila)

            menu.addSeparator()

        menu.exec(tabla.mapToGlobal(pos))
    
    def copiar_celda(self, tabla):
        """Copia el contenido de la celda seleccionada"""
        item = tabla.currentItem()
        if item:
            from PyQt6.QtWidgets import QApplication
            QApplication.clipboard().setText(item.text())
            QMessageBox.information(
                self, "✅ Copiado", f"Texto copiado: {item.text()}")

    def copiar_fila(self, tabla):
        """Copia el contenido de la fila seleccionada"""
        fila = tabla.currentRow()
        if fila >= 0:
            textos = []
            for col in range(tabla.columnCount()):
                item = tabla.item(fila, col)
                if item:
                    textos.append(item.text())
            texto_fila = "\t".join(textos)
            from PyQt6.QtWidgets import QApplication
            QApplication.clipboard().setText(texto_fila)
            QMessageBox.information(
                self, "✅ Copiado", "Fila copiada al portapapeles")

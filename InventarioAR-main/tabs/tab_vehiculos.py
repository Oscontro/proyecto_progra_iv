"""
Pestaña:   Vehículos
Versión: 8.7 - OPTIMIZADO PARA 1366x768
Fecha:  2026-02-15
Autor: lucasarsa2015-cpu
Descripción: Gestión de vehículos - Interfaz optimizada con más espacio para radios
"""
import os
import requests
import pandas as pd
import direcciones # type: ignore
from base_tab import ApiTab
from api_client import ApiError, SesionExpirada
from PyQt6.QtWidgets import (
    QScrollArea, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QFrame, QComboBox, QTableWidget, QTableWidgetItem,
    QHeaderView, QMessageBox, QAbstractItemView, QDialog,
    QTextEdit, QGridLayout, QMenu
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QColor, QBrush, QAction, QCursor, QPixmap

class DialogoMotivoPapelera(QDialog):
    def __init__(self, identificacion=None, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Enviar a papelera")
        self.setMinimumWidth(400)
        
        layout = QVBoxLayout(self)
        
        layout.addWidget(QLabel(f"¿Enviar equipo {identificacion} a la papelera?"))
        layout.addWidget(QLabel("Motivo:"))
        
        self.txt_motivo = QTextEdit()
        self.txt_motivo.setMaximumHeight(100)
        layout.addWidget(self.txt_motivo)
        
        # Botones
        btn_layout = QHBoxLayout()
        btn_cancelar = QPushButton("Cancelar")
        btn_confirmar = QPushButton("Confirmar")
        
        btn_cancelar.clicked.connect(self.reject)
        btn_confirmar.clicked.connect(self.accept)
        
        btn_layout.addWidget(btn_cancelar)
        btn_layout.addWidget(btn_confirmar)
        layout.addLayout(btn_layout)
    
    def get_motivo(self):
        print(f"Motivo ingresado: {self.txt_motivo.toPlainText()}")
        return self.txt_motivo.toPlainText().strip()

class DialogoHistorial(QDialog):
    def __init__(self, datos_historial=None, dato_equipo=None, dato_vehiculo=None, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Registros de historial")
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
            6, QHeaderView.ResizeMode.Stretch)  # observaciones

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

        self.setLayout(layout)


class DialogoHistorialVehiculo(QDialog):
    """Ventana modal para ver historial del vehículo"""

    def __init__(self, vehiculo_data, parent=None):
        super().__init__(parent)
        self.vehiculo_data = vehiculo_data
        self.setWindowTitle("📜 Historial del Vehículo")
        self.setModal(True)
        self.setFixedSize(700, 500)
        self.crear_interfaz()
        
    def crear_interfaz(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(25, 25, 25, 25)
        layout.setSpacing(20)

        datos_frame = QFrame()
        datos_frame.setStyleSheet("""
            QFrame {
                background-color: #e8f5e9;
                border: 2px solid #4caf50;
                border-radius: 8px;
                padding: 15px;
            }
        """)

        datos_layout = QVBoxLayout()
        titulo_datos = QLabel("Datos del vehículo")
        titulo_datos.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        titulo_datos.setStyleSheet("color: #2e7d32;")
        datos_layout.addWidget(titulo_datos)

        info_html = f"""
        <p style='margin: 5px 0; color: #2e7d32;'><b>Tipo:</b> {self.vehiculo_data.get('tipo', 'N/A')}</p>
        <p style='margin: 5px 0; color: #2e7d32;'><b>N° Interno:</b> {self.vehiculo_data.get('identificacion', 'N/A')}</p>
        <p style='margin: 5px 0; color: #2e7d32;'><b>Escala:</b> {self.vehiculo_data.get('escala', 'N/A')}</p>
        <p style='margin: 5px 0; color: #2e7d32;'><b>Radio Asociado:</b> {self.vehiculo_data.get('radio_asignado', 'Sin radio')}</p>
        """

        lbl_info = QLabel(info_html)
        lbl_info.setFont(QFont("Arial", 11))
        datos_layout.addWidget(lbl_info)
        datos_frame.setLayout(datos_layout)
        layout.addWidget(datos_frame)

        lbl_historial = QLabel("📋 Historial de eventos:")
        lbl_historial.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        layout.addWidget(lbl_historial)

        historial_text = QTextEdit()
        historial_text.setReadOnly(True)
        historial_text.setPlaceholderText(
            "No hay eventos registrados para este vehículo.")
        historial_text.setStyleSheet("""
            QTextEdit {
                border: 2px solid #cfd8dc;
                border-radius: 8px;
                padding: 10px;
                background-color: white;
            }
        """)
        layout.addWidget(historial_text)

        botones_layout = QHBoxLayout()
        botones_layout.addStretch()

        btn_cerrar = QPushButton("Cerrar")
        btn_cerrar.setFixedHeight(45)
        btn_cerrar.setStyleSheet("""
            QPushButton {
                background-color: #1976d2;
                color: white;
                border-radius: 6px;
                padding: 0 30px;
            }
            QPushButton:hover { background-color: #1565c0; }
        """)
        btn_cerrar.clicked.connect(self.accept)
        botones_layout.addWidget(btn_cerrar)

        layout.addLayout(botones_layout)
        self.setLayout(layout)


class VehiculosTab(ApiTab):
    """Pestaña de vehículos - OPTIMIZADA 1366x768 CON MENÚ CONTEXTUAL COPIAR"""

    def __init__(self, api):
        super().__init__(api)
        self.api = api
        self.datos_completos = []
        self.datos_filtrados = []
        self.datos_radios_disponibles = []
        self.API_BASE_URL = direcciones.URL.API_BASE_URL #URL base de de la API
        self.crear_interfaz()
        self.llenar_desplegables()
        self.get_internos()

    def crear_interfaz(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(15)

        header = QLabel("🚌 VEHÍCULOS")
        header.setFont(QFont("Arial", 20, QFont.Weight.Bold))
        header.setAlignment(Qt.AlignmentFlag.AlignCenter)
        header.setFixedHeight(60)
        header.setStyleSheet("""
            QLabel {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #1565c0, stop:1 #1976d2);
                color: white;
                padding: 15px;
                border-radius: 10px;
                border: 3px solid #0d47a1;
            }
        """)
        layout.addWidget(header)

        contenido_principal = QHBoxLayout()
        contenido_principal.setSpacing(15)

        columna_izquierda = self.crear_columna_izquierda()
        contenido_principal.addWidget(columna_izquierda, 40)

        columna_derecha = self.crear_columna_derecha()
        contenido_principal.addWidget(columna_derecha, 60)

        layout.addLayout(contenido_principal, 1)

        self.setLayout(layout)
        self.cargar_tabla()

    def crear_columna_izquierda(self):
        """Columna izquierda: Datos Vehículo (COMPACTO) + Radios Disponibles (MÁS ESPACIO)"""
        col_frame = QFrame()
        col_frame.setStyleSheet("""
            QFrame {
                background-color: white;
                border-radius: 10px;
                border: 2px solid #cfd8dc;
                color: black;
            }
        """)

        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(10, 10, 10, 10)  # Reducido de 15 a 10
        main_layout.setSpacing(6)  # Reducido de 10 a 6

        # SECCIÓN: DATOS DEL VEHÍCULO (MÁS COMPACTO)
        titulo_vehiculo = QLabel("🚌 Datos del Vehículo")
        titulo_vehiculo.setFont(QFont("Arial", 10, QFont.Weight.Bold))  # Reducido de 12 a 10
        titulo_vehiculo.setStyleSheet("color: #1976d2;")
        main_layout.addWidget(titulo_vehiculo)

        campos_frame = QFrame()
        campos_frame.setStyleSheet("""
            QFrame {
                background-color: #fafafa;
                border: 2px solid #e0e0e0;
                border-radius: 8px;
                padding: 5px;
            }
        """)

        grid = QGridLayout()
        grid.setSpacing(4)  # Reducido de 6 a 4
        grid.setColumnStretch(1, 1)

        estilo_input = """
            QLineEdit, QComboBox {
                border: 2px solid #cfd8dc;
                border-radius: 5px;
                padding: 3px;
                min-height: 22px;
                max-width: 220px;
                font-size: 9pt;
                background-color: white;
                color: black;
            }
            QLineEdit:focus, QComboBox:focus {
                border: 2px solid #1976d2;
            }
                        QComboBox:: drop-down {
                border: none;
                width: 30px;
                color: black;
            }
            QComboBox::down-arrow {
                image: none;
                border-left: 5px solid transparent;
                border-right: 5px solid transparent;
                border-top: 7px solid #37474f;
                margin-right: 8px;
                color: black;
            }
        """

        estilo_label = "color: #37474f; font-weight: bold; font-size: 9pt;"

        lbl_tipo = QLabel("🚌 Tipo:")
        lbl_tipo.setStyleSheet(estilo_label)
        grid.addWidget(lbl_tipo, 0, 0)

        self.combo_tipo = QComboBox()
        self.combo_tipo.setEditable(True)
        self.combo_tipo.setPlaceholderText("Seleccione o escriba...")
        self.combo_tipo.lineEdit().setPlaceholderText("Seleccione o escriba...")
        self.combo_tipo.setStyleSheet(estilo_input)
        grid.addWidget(self.combo_tipo, 0, 1)

        lbl_interno = QLabel("🆔 N° Interno:")
        lbl_interno.setStyleSheet(estilo_label)
        grid.addWidget(lbl_interno, 1, 0)

        self.input_interno = QLineEdit()
        self.input_interno.setPlaceholderText("Ej: VEH001")
        self.input_interno.setStyleSheet(estilo_input)
        grid.addWidget(self.input_interno, 1, 1)

        lbl_escala = QLabel("📍 Escala:")
        lbl_escala.setStyleSheet(estilo_label)
        grid.addWidget(lbl_escala, 2, 0)

        self.combo_escala = QComboBox()
        self.combo_escala.setEditable(True)
        self.combo_escala.setPlaceholderText("Seleccione o escriba...")
        self.combo_escala.lineEdit().setPlaceholderText("Seleccione o escriba...")
        self.combo_escala.setStyleSheet(estilo_input)
        grid.addWidget(self.combo_escala, 2, 1)

        campos_frame.setLayout(grid)
        main_layout.addWidget(campos_frame)

        # Botones Guardar y Modificar (MÁS PEQUEÑOS)
        botones_layout = QHBoxLayout()
        botones_layout.setSpacing(6)

        btn_guardar = QPushButton("💾 Guardar")
        btn_guardar.setFixedHeight(26)  # Reducido de 32 a 26
        btn_guardar.setStyleSheet("""
            QPushButton {
                background-color: #27ae60;
                color: white;
                border-radius: 5px;
                padding: 0 8px;
                font-weight: bold;
                font-size: 8pt;
            }
            QPushButton:hover { background-color: #1e8449; }
        """)
        btn_guardar.clicked.connect(self.guardar_vehiculo)
        botones_layout.addWidget(btn_guardar)

        btn_modificar = QPushButton("📝 Modificar Vehiculo")
        btn_modificar.setFixedHeight(26)  # Reducido de 32 a 26
        btn_modificar.setStyleSheet("""
            QPushButton {
                background:  #1976d2;
                color: white;
                border-radius: 5px;
                padding: 0 8px;
                font-weight: bold;
                font-size: 8pt;
            }
            QPushButton:hover {
                background-color: #1565c0;
            }
            QPushButton:disabled {
                background-color: #cfd8dc;
                color: #90a4ae;
            }
        """)
        btn_modificar.clicked.connect(self.modificar_vehiculo)
        botones_layout.addWidget(btn_modificar)
        
        btn_borrar = QPushButton("🧹 Borrar campos")
        btn_borrar.setFixedHeight(26)  # Reducido de 32 a 26
        btn_borrar.setStyleSheet("""
            QPushButton {
                background-color: #AB2B2B;
                color: white;
                border-radius: 5px;
                padding: 0 8px;
                font-weight: bold;
                font-size: 8pt;
            }
            QPushButton:hover { background-color: #A83939; }
        """)
        btn_borrar.clicked.connect(self.borrar_campos)
        botones_layout.addWidget(btn_borrar)
        
        btn_baja = QPushButton("✏️ Baja de vehiculo")
        btn_baja.setFixedHeight(26)  # Reducido de 32 a 26
        btn_baja.setStyleSheet("""
            QPushButton {
                background-color: #c62828;
                color: white;
                border-radius: 5px;
                padding: 0 8px;
                font-weight: bold;
                font-size: 8pt;
            }
            QPushButton:hover { background-color: #b71c1c; }
        """)
        btn_baja.clicked.connect(self.baja_vehiculo)
        botones_layout.addWidget(btn_baja)
        
        btn_historial = QPushButton("📜 Historial del vehiculo")
        btn_historial.setFixedHeight(26)  # Reducido de 32 a 26
        btn_historial.setStyleSheet("""
            QPushButton {
                background-color: #7b1fa2;
                color: white;
                border-radius: 5px;
                padding: 0 8px;
                font-weight: bold;
                font-size: 8pt;
            }
            QPushButton:hover { background-color: #6a1b9a; }
            QPushButton:disabled { background-color: #cfd8dc; color: #90a4ae; }
        """)
        btn_historial.clicked.connect(self.ver_historial_vehiculo)
        botones_layout.addWidget(btn_historial)

        main_layout.addLayout(botones_layout)

        # Separador
        separador = QFrame()
        separador.setFrameShape(QFrame.Shape.HLine)
        separador.setStyleSheet("background-color: #cfd8dc;")
        separador.setFixedHeight(2)
        main_layout.addWidget(separador)

        # SECCIÓN: RADIOS DISPONIBLES (MÁS ESPACIO)
        titulo_radios = QLabel("📻 Radios Disponibles")
        titulo_radios.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        titulo_radios.setStyleSheet("color: #1976d2;")
        main_layout.addWidget(titulo_radios)

        # Tabla de radios con 4 columnas — stretch=3 para MUCHO más espacio
        self.tabla_radios_disponibles = QTableWidget()
        self.tabla_radios_disponibles.setColumnCount(5)
        self.tabla_radios_disponibles.setHorizontalHeaderLabels(
            ["ID Equipo", "Marca", "Modelo","N° Serie", "Escala"])
        self.tabla_radios_disponibles.setEditTriggers(
            QAbstractItemView.EditTrigger.NoEditTriggers)
        self.tabla_radios_disponibles.setSelectionBehavior(
            QAbstractItemView.SelectionBehavior.SelectRows)
        self.tabla_radios_disponibles.setSelectionMode(
            QAbstractItemView.SelectionMode.SingleSelection)
        self.tabla_radios_disponibles.setAlternatingRowColors(True)
        self.tabla_radios_disponibles.setStyleSheet("""
            QTableWidget {
                border: 2px solid #cfd8dc;
                border-radius: 8px;
                background-color: white;
                font-size: 9pt;
            }
            QTableWidget::item {
                padding: 4px;
            }
            QTableWidget::item:selected {
                background-color: #bbdefb;
                color: #0d47a1;
            }
            QHeaderView::section {
                background-color: #1976d2;
                color: white;
                padding: 5px;
                font-weight: bold;
                font-size: 9pt;
            }
        """)

        header_radios = self.tabla_radios_disponibles.horizontalHeader()
        header_radios.setSectionResizeMode(
            0, QHeaderView.ResizeMode.ResizeToContents)  # ID_EQUIPO (oculto)
        header_radios.setSectionResizeMode(
            1, QHeaderView.ResizeMode.ResizeToContents)  # Marca
        header_radios.setSectionResizeMode(
            2, QHeaderView.ResizeMode.Stretch)  # Modelo
        header_radios.setSectionResizeMode(
            3, QHeaderView.ResizeMode.Stretch)  # Serie
        header_radios.setSectionResizeMode(
            4, QHeaderView.ResizeMode.ResizeToContents)  # Escala

        # Anchos iniciales
        self.tabla_radios_disponibles.setColumnWidth(0, 75)
        self.tabla_radios_disponibles.setColumnWidth(1, 70)
        self.tabla_radios_disponibles.setColumnWidth(2, 75)

        self.tabla_radios_disponibles.verticalHeader().setDefaultSectionSize(26)
        self.tabla_radios_disponibles.itemSelectionChanged.connect(
            self.on_radio_seleccionado)

        # Habilitar menú contextual para copiar
        self.tabla_radios_disponibles.setContextMenuPolicy(
            Qt.ContextMenuPolicy.CustomContextMenu)
        self.tabla_radios_disponibles.customContextMenuRequested.connect(
            lambda pos: self.mostrar_menu_contextual(
                self.tabla_radios_disponibles, pos)
        )

        # stretch=3 para que la tabla ocupe MUCHO más espacio vertical
        main_layout.addWidget(self.tabla_radios_disponibles, 3)

        self.cargar_radios_disponibles()

        # Botones de gestión
        botones_radio_layout = QGridLayout()
        botones_radio_layout.setSpacing(4)

        self.btn_ver_historial = QPushButton("📜 Historial")
        self.btn_ver_historial.setFixedHeight(26)
        self.btn_ver_historial.setEnabled(False)
        self.btn_ver_historial.setStyleSheet("""
            QPushButton {
                background-color: #7b1fa2;
                color: white;
                border-radius: 5px;
                font-weight: bold;
                font-size: 8pt;
            }
            QPushButton:hover { background-color: #6a1b9a; }
            QPushButton:disabled { background-color: #cfd8dc; color: #90a4ae; }
        """)
        self.btn_ver_historial.clicked.connect(self.ver_historial_equipo)
        botones_radio_layout.addWidget(self.btn_ver_historial, 0, 0)

        self.btn_asociar = QPushButton("🔗 Asociar")
        self.btn_asociar.setFixedHeight(26)
        self.btn_asociar.setEnabled(False)
        self.btn_asociar.setStyleSheet("""
            QPushButton {
                background-color: #1976d2;
                color: white;
                border-radius: 5px;
                font-weight: bold;
                font-size: 8pt;
            }
            QPushButton:hover { background-color: #1565c0; }
            QPushButton:disabled { background-color: #cfd8dc; color: #90a4ae; }
        """)
        self.btn_asociar.clicked.connect(self.asociar_radio_directo)
        botones_radio_layout.addWidget(self.btn_asociar, 0, 1)

        self.btn_desasociar = QPushButton("❌ Desasociar")
        self.btn_desasociar.setFixedHeight(26)
        self.btn_desasociar.setEnabled(False)
        self.btn_desasociar.setStyleSheet("""
            QPushButton {
                background-color: #c62828;
                color: white;
                border-radius: 5px;
                font-weight: bold;
                font-size: 8pt;
            }
            QPushButton:hover { background-color: #b71c1c; }
            QPushButton:disabled { background-color: #cfd8dc; color: #90a4ae; }
        """)
        self.btn_desasociar.clicked.connect(self.desasociar_radio)
        botones_radio_layout.addWidget(self.btn_desasociar, 1, 0, 1, 2)

        main_layout.addLayout(botones_radio_layout)

        col_frame.setLayout(main_layout)
        return col_frame

    def crear_columna_derecha(self):
        """Columna derecha: Vehículos Registrados + Imagen de la Radio (más grande)"""
        col_frame = QFrame()
        col_frame.setStyleSheet("""
            QFrame {
                background-color: white;
                border-radius: 10px;
                border: 2px solid #cfd8dc;
                color: black;
            }
        """)

        layout = QVBoxLayout()
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(8)

        # SECCIÓN: VEHÍCULOS REGISTRADOS
        titulo_tabla = QLabel("📋 Vehículos Registrados")
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
        self.input_buscar.setPlaceholderText("N° Interno...")
        self.input_buscar.setFixedHeight(30)
        self.input_buscar.setStyleSheet("""
            QLineEdit {
                border: 2px solid #cfd8dc;
                border-radius: 6px;
                padding: 5px;
                background-color: white;
                color: black;
            }
            QLineEdit:focus { border: 2px solid #1976d2; }
        """)
        self.input_buscar.textChanged.connect(self.aplicar_filtros)
        busqueda_layout.addWidget(self.input_buscar)

        btn_limpiar = QPushButton("🗑️ Limpiar")
        btn_limpiar.setFixedHeight(30)
        btn_limpiar.setStyleSheet("""
            QPushButton {
                background-color: #757575;
                color: white;
                border-radius: 6px;
                padding: 0 12px;
                font-weight: bold;
                font-size: 9pt;
            }
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
            QComboBox {
                border: 2px solid #cfd8dc;
                border-radius: 5px;
                padding: 4px;
                min-width: 90px;
                background-color: white;
                font-size: 9pt;
                color: black;
            }
            QComboBox:hover { border: 2px solid #1976d2; }
        """

        label_tipo_interno = QLabel("Tipo de vehiculo:")
        label_tipo_interno.setStyleSheet("color: black;")
        filtros_layout.addWidget(label_tipo_interno)
        self.combo_filtro_tipo = QComboBox()
        self.combo_filtro_tipo.addItem("Todos")
        self.combo_filtro_tipo.setFixedHeight(26)
        self.combo_filtro_tipo.setStyleSheet(estilo_combo)
        self.combo_filtro_tipo.currentTextChanged.connect(self.aplicar_filtros)
        filtros_layout.addWidget(self.combo_filtro_tipo)


        label_escala = QLabel("Escala:")
        label_escala.setStyleSheet("color: black;")
        filtros_layout.addWidget(label_escala)
        self.combo_filtro_escala = QComboBox()
        self.combo_filtro_escala.addItem("Todos")
        self.combo_filtro_escala.setFixedHeight(26)
        self.combo_filtro_escala.setStyleSheet(estilo_combo)
        self.combo_filtro_escala.currentTextChanged.connect(
            self.aplicar_filtros)
        filtros_layout.addWidget(self.combo_filtro_escala)
        
        label_modelo = QLabel("Modelo de radio:")
        label_modelo.setStyleSheet("color: black;")
        filtros_layout.addWidget(label_modelo)
        self.combo_filtro_modelo = QComboBox()
        self.combo_filtro_modelo.addItem("Todos")
        self.combo_filtro_modelo.setFixedHeight(26)
        self.combo_filtro_modelo.setStyleSheet(estilo_combo)
        self.combo_filtro_modelo.currentTextChanged.connect(
            self.aplicar_filtros)
        filtros_layout.addWidget(self.combo_filtro_modelo)

        filtros_layout.addStretch()
        layout.addLayout(filtros_layout)

        # Tabla de vehículos — stretch=1 para que ocupe el espacio principal
        self.crear_tabla()
        layout.addWidget(self.tabla, 1)

        # SECCIÓN: IMAGEN DE LA RADIO (MÁS GRANDE: 110px)
        imagen_frame = QFrame()
        imagen_frame.setStyleSheet("""
            QFrame {
                background-color: #fafafa;
                border: 2px solid #e0e0e0;
                border-radius: 8px;
                padding: 8px;
            }
        """)

        imagen_layout = QHBoxLayout()
        imagen_layout.setContentsMargins(8, 5, 8, 5)
        imagen_layout.setSpacing(12)

        lbl_imagen_titulo = QLabel("🖼️ Imagen\nde la\nRadio:")
        lbl_imagen_titulo.setFont(QFont("Arial", 9, QFont.Weight.Bold))
        lbl_imagen_titulo.setStyleSheet("color: #1976d2;")
        lbl_imagen_titulo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl_imagen_titulo.setFixedWidth(130)
        imagen_layout.addWidget(lbl_imagen_titulo)

        self.label_imagen = QLabel("📷  Seleccione una radio de la lista")
        self.label_imagen.setFixedHeight(150)  # Aumentado de 80 a 110
        self.label_imagen.setStyleSheet("""
            QLabel {
                border: 2px dashed #cfd8dc;
                border-radius: 8px;
                background-color: white;
                color: #90a4ae;
                font-size: 10pt;
                font-weight: bold;
                padding: 10px;
            }
        """)
        self.label_imagen.setAlignment(Qt.AlignmentFlag.AlignCenter)
        imagen_layout.addWidget(self.label_imagen, 1)

        imagen_frame.setLayout(imagen_layout)
        layout.addWidget(imagen_frame)

        col_frame.setLayout(layout)
        return col_frame

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

    def copiar_tabla_completa(self, tabla):
        """Copia toda la tabla al portapapeles"""
        filas = []

        # Encabezados
        encabezados = []
        for col in range(tabla.columnCount()):
            encabezados.append(tabla.horizontalHeaderItem(col).text())
        filas.append("\t".join(encabezados))

        # Datos
        for fila in range(tabla.rowCount()):
            textos = []
            for col in range(tabla.columnCount()):
                item = tabla.item(fila, col)
                if item:
                    textos.append(item.text())
                else:
                    textos.append("")
            filas.append("\t".join(textos))

        texto_completo = "\n".join(filas)
        from PyQt6.QtWidgets import QApplication
        QApplication.clipboard().setText(texto_completo)
        QMessageBox.information(
            self, "✅ Copiado", f"Tabla completa copiada ({tabla.rowCount()} filas)")

    def cargar_radios_disponibles(self):
        self.datos_radios_disponibles = []
        try:
            radios = self.api.get("radios_vehiculos.php")
            if radios:
                self.datos_radios_disponibles = radios
                self.tabla_radios_disponibles.setRowCount(len(self.datos_radios_disponibles))
                for fila, radio in enumerate(self.datos_radios_disponibles):
                    for col, campo in enumerate(['id_equipo', 'marca', 'modelo_equipo','numero_serie', 'escala']):
                        self.tabla_radios_disponibles.hideColumn(0)  # Ocultar columna de ID_EQUIPO
                        item = QTableWidgetItem(str(radio.get(campo, '') or ''))
                        item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                        self.tabla_radios_disponibles.setItem(fila, col, item)
            else:
                self.datos_radios_disponibles = []
        except Exception as e:
            self.tabla_radios_disponibles.setRowCount(0)
            self.datos_radios_disponibles = []
        except SesionExpirada:
                    QMessageBox.warning(self, "Sesión expirada",
                                        "Tu sesión venció. Cerrá y volvé a iniciar sesión.")
                    self.tabla_radios_disponibles.setRowCount(0)
                    self.datos_radios_disponibles = []
        except ApiError as e:
                    QMessageBox.critical(self, "Error", f"No se pudo obtener radios:\n{e}")
                    self.tabla_radios_disponibles.setRowCount(0)
                    self.datos_radios_disponibles = []
            
    def get_internos(self):
        """Obtener lista de internos"""
        try:
            internos = self.api.get("internos.php")
            if internos:
                self.datos_completos = internos
                self.datos_filtrados = self.datos_completos.copy()
                self.cargar_tabla()
            else:
                self.datos_completos = []
                self.datos_filtrados = []
                self.cargar_tabla()
        except Exception as e:
            self.datos_completos = []
            self.datos_filtrados = []
            self.cargar_tabla()
        except SesionExpirada:
                    QMessageBox.warning(self, "Sesión expirada",
                                        "Tu sesión venció. Cerrá y volvé a iniciar sesión.")
                    self.datos_completos = []
                    self.datos_filtrados = []
                    self.cargar_tabla()
        except ApiError as e:
                    QMessageBox.critical(self, "Error", f"No se pudo obtener internos:\n{e}")
                    self.datos_completos = []
                    self.datos_filtrados = []
                    self.cargar_tabla()



    def on_radio_seleccionado(self):
        """Maneja selección de radio"""
        hay_seleccion = len(self.tabla_radios_disponibles.selectedItems()) > 0
        self.btn_asociar.setEnabled(hay_seleccion)
        self.btn_ver_historial.setEnabled(hay_seleccion)

        if hay_seleccion:
            fila = self.tabla_radios_disponibles.currentRow()
            marca = self.tabla_radios_disponibles.item(fila, 1).text()
            modelo = self.tabla_radios_disponibles.item(fila, 2).text()
            serie = self.tabla_radios_disponibles.item(fila, 3).text()
            escala = self.tabla_radios_disponibles.item(fila, 4).text()
            self.label_imagen.setText(
                f"📻  {marca} {modelo}\n\nSerie: {serie}\nEscala: {escala}")
            self.label_imagen.setStyleSheet("""
                QLabel {
                    border: 2px solid #1976d2;
                    border-radius: 8px;
                    background-color: #e3f2fd;
                    color: #1976d2;
                    font-size: 9pt;
                    font-weight: bold;
                    padding: 10px;
                }
            """)
            self.capturar_modelo_actual(modelo)  # Guardar modelo para imagen
            self.cargar_imagen_modelo(modelo)  # Cargar imagen del modelo
        else:
            self.label_imagen.setText("📷\n\nSeleccione una radio\nde la lista")
            self.label_imagen.setStyleSheet("""
                QLabel {
                    border: 2px dashed #cfd8dc;
                    border-radius: 8px;
                    background-color: white;
                    color: #90a4ae;
                    font-size: 10pt;
                    font-weight: bold;
                    padding: 10px;
                }
            """)

    def crear_tabla(self):
        """Crea tabla de vehículos con columnas redimensionables"""
        self.tabla = QTableWidget()
        self.tabla.setColumnCount(7)
        self.tabla.hideColumn(0)  # Ocultar columna de orden (N°)
        self.tabla.hideColumn(1)  # Ocultar columna de ID_VEHICULO
        self.tabla.setHorizontalHeaderLabels([
            "N°", "ID Vehículo", "Tipo", "N° Interno", "Escala", "Modelo", "N° de Serie"
        ])
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
                background-color: white;
                font-size: 9pt;
                color: black;
            }
            QTableWidget::item {
                padding: 5px;
                color: black;
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
                padding: 6px;
                font-weight: bold;
                font-size: 9pt;
                border: none;
                border-right: 1px solid #607d8b;
            }
            QHeaderView::section:last {
                border-right: none;
            }
        """)

        # Configurar columnas redimensionables + doble clic para ajustar
        header_tabla = self.tabla.horizontalHeader()
        header_tabla.setSectionResizeMode(
            0, QHeaderView.ResizeMode.ResizeToContents)  # N° de Orden 
        header_tabla.setSectionResizeMode(
            1, QHeaderView.ResizeMode.ResizeToContents)  # ID Vehículo
        header_tabla.setSectionResizeMode(
            2, QHeaderView.ResizeMode.ResizeToContents)  # Tipo de vehiculo
        header_tabla.setSectionResizeMode(
            3, QHeaderView.ResizeMode.ResizeToContents)  # Indentificaion de vehiculo
        header_tabla.setSectionResizeMode(
            4, QHeaderView.ResizeMode.ResizeToContents)  # Escala
        header_tabla.setSectionResizeMode(
            5, QHeaderView.ResizeMode.Stretch)  # Modelo
        header_tabla.setSectionResizeMode(
            6, QHeaderView.ResizeMode.Stretch)  # N° de Serie
        
        
        # Anchos iniciales
        self.tabla.setColumnWidth(0, 40)
        self.tabla.setColumnWidth(1, 80)
        self.tabla.setColumnWidth(2, 100)
        self.tabla.setColumnWidth(3, 70)
        self.tabla.setColumnWidth(4, 100)

        self.tabla.verticalHeader().setDefaultSectionSize(32)
        self.tabla.itemSelectionChanged.connect(self.on_seleccion_cambiada)

        # Habilitar menú contextual para copiar
        self.tabla.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.tabla.customContextMenuRequested.connect(
            lambda pos: self.mostrar_menu_contextual(self.tabla, pos)
        )

    def cargar_tabla(self):
        """Carga datos en tabla"""
        self.tabla.setRowCount(len(self.datos_filtrados))
        for fila, vehiculo in enumerate(self.datos_filtrados):
            item_orden = QTableWidgetItem(str(fila + 1))
            item_orden.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            item_orden.setFont(QFont("Arial", 9, QFont.Weight.Bold))

            if vehiculo.get('radio_serie'):
                item_orden.setBackground(QBrush(QColor("#4caf50")))
                item_orden.setForeground(QBrush(QColor("white")))
            else:
                item_orden.setBackground(QBrush(QColor("#f44336")))
                item_orden.setForeground(QBrush(QColor("white")))
            self.tabla.setItem(fila, 0, item_orden)

            for col, campo in enumerate(['id_vehiculo', 'tipo', 'identificacion', 'escala', 'radio_modelo', 'radio_serie'], 1):
                valor = vehiculo.get(campo, '') or '-'
                item = QTableWidgetItem(str(valor))
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                item.setFont(QFont("Arial", 9))
                self.tabla.setItem(fila, col, item)

    def aplicar_filtros(self):
        """Aplica filtros"""
        self.datos_filtrados = self.datos_completos.copy()

        texto = self.input_buscar.text().strip().upper()
        if texto:
            self.datos_filtrados = [v for v in self.datos_filtrados if texto in v.get(
                'identificacion', '').upper()]

        tipo = self.combo_filtro_tipo.currentText()
        if tipo != "Todos":
            self.datos_filtrados = [
                v for v in self.datos_filtrados if v.get('tipo', '') == tipo]

        escala = self.combo_filtro_escala.currentText()
        if escala != "Todos":
            self.datos_filtrados = [
                v for v in self.datos_filtrados if v.get('escala', '') == escala]
        
        modelo = self.combo_filtro_modelo.currentText()
        if modelo != "Todos":
            self.datos_filtrados = [
                v for v in self.datos_filtrados if v.get('radio_modelo', '') == modelo]

        self.cargar_tabla()

    def limpiar_filtros(self):
        """Limpia filtros"""
        self.input_buscar.clear()
        self.combo_filtro_tipo.setCurrentIndex(0)
        self.combo_filtro_escala.setCurrentIndex(0)
        self.datos_filtrados = self.datos_completos.copy()
        self.cargar_tabla()

    def on_seleccion_cambiada(self):
        """Maneja selección en tabla"""
        fila = self.tabla.currentRow()
        if fila >= 0 and fila < len(self.datos_filtrados) :
            vehiculo = self.datos_filtrados[fila]
            self.btn_desasociar.setEnabled(bool(vehiculo.get('radio_serie')))
            self.combo_tipo.setCurrentText(vehiculo.get('tipo', ''))
            self.input_interno.setText(vehiculo.get('identificacion', ''))
            self.input_interno.setEnabled(False)  # No se puede modificar el N° Interno
            self.combo_escala.setCurrentText(vehiculo.get('escala', ''))
        else:
            self.btn_desasociar.setEnabled(False)
            self.datos_filtrados = []
            

    def modificar_vehiculo(self):
        """Modifica vehículo"""
        fila = self.tabla.currentRow()
        if fila < 0:
            QMessageBox.warning(self, "⚠️ Sin Selección",
                                "Seleccione un vehículo de la tabla.")
            return
        
        if fila >= len(self.datos_filtrados):
            return
        
        vehiculo = self.datos_filtrados[fila]
        respuesta = QMessageBox.question(
                self,
                "Confirmar",
                f"¿Desea modificar el vehículo?\n\nN° Interno: {vehiculo.get('identificacion', '')} ",
                QMessageBox. StandardButton.Yes | QMessageBox.StandardButton.No
            )
        if respuesta == QMessageBox.StandardButton.Yes:
            try:
                resultado = self.api.post("modificar_interno.php", datos={
                    "identificacion": self.input_interno.text().strip(),
                    "nuevo_tipo": self.combo_tipo.currentText(),
                    "nueva_escala": self.combo_escala.currentText()
                })
                if resultado:
                    self.cargar_tabla()
                    QMessageBox.information(
                        self, "✅ Modificado", f"Vehículo modificado correctamente.")
                    
                    self.get_internos()
                    self.borrar_campos()
                else:
                    QMessageBox.warning(self, "Error", f"Error al modificar vehículo: {resultado.get('message')}")
            except SesionExpirada:
                                        QMessageBox.warning(self, "Sesión expirada",
                                                            "Tu sesión venció. Cerrá y volvé a iniciar sesión.")
            except ApiError as e:
                                        QMessageBox.critical(self, "Error", f"No se pudo modificar el vehículo:\n{e}")

    def borrar_campos(self):
        """Borra campos del vehículo"""
        fila = self.tabla.currentRow()
        if fila < 0:
            return
        else:
            self.combo_tipo.setCurrentText("")
            self.input_interno.clear()
            self.combo_escala.setCurrentText("")
            self.tabla_radios_disponibles.clearSelection()
            self.tabla.clearSelection()
            self.btn_desasociar.setEnabled(False)
            self.input_interno.setEnabled(True)
            self.limpiar_formulario()
            self.tabla.setCurrentCell(-1, -1)

    def asociar_radio_directo(self):
        """Asocia radio"""
        fila_vehiculo = self.tabla.currentRow()
        fila_radio = self.tabla_radios_disponibles.currentRow()

        if fila_vehiculo < 0:
            QMessageBox.warning(self, "⚠️ Sin Vehículo",
                                "Seleccione un vehículo de la tabla.")
            return

        if fila_radio < 0:
            QMessageBox.warning(self, "⚠️ Sin Radio",
                                "Seleccione una radio de la lista.")
            return

        serie = self.tabla_radios_disponibles.item(fila_radio, 3).text()
        vehiculo = self.datos_filtrados[fila_vehiculo]
        respuesta = QMessageBox.question(
            self, "🔗 Confirmar Asociación",
            f"¿Desea asociar la radio {serie} al vehículo {vehiculo.get('identificacion', '')}?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if respuesta == QMessageBox.StandardButton.Yes:
            try:

                resultado = self.api.post("asociar_radio.php", datos={
                        "numero_serie": serie,
                        "identificacion": vehiculo.get('identificacion', '')
                    }
                )
                if resultado:
                    self.get_internos()
                    self.btn_desasociar.setEnabled(True)
                    QMessageBox.information(
                        self, "✅ Asociado", f"Radio {serie} asociada correctamente.")
                else:
                    QMessageBox.warning(self, "Error", f"Error al asociar radio: {resultado.get('message')}")
            except SesionExpirada:
                                        QMessageBox.warning(self, "Sesión expirada",
                                                            "Tu sesión venció. Cerrá y volvé a iniciar sesión.")
            except ApiError as e:
                                        QMessageBox.critical(self, "Error", f"No se pudo asociar la radio:\n{e}")

    def desasociar_radio(self):
        """Desasocia radio"""
        fila = self.tabla.currentRow()
        if fila < 0:
            return

        vehiculo = self.datos_filtrados[fila]

        respuesta = QMessageBox.question(
            self, "❌ Confirmar Desasociación",
            f"¿Desea desasociar la radio {vehiculo.get('radio_serie', '')} del vehículo {vehiculo.get('identificacion', '')}?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        

        if respuesta == QMessageBox.StandardButton.Yes:
            try:
                resultado = self.api.post("desasociar_radio.php", datos={
                    "identificacion": vehiculo.get('identificacion', '')
                })
                if resultado:
                    self.get_internos()
                    self.btn_desasociar.setEnabled(False)
                    QMessageBox.information(
                        self, "✅ Desasociado", "Radio desasociada correctamente.")
                else:
                    QMessageBox.warning(self, "Error", f"Error al asociar radio: {resultado.get('message')}")
            except SesionExpirada:
                                        QMessageBox.warning(self, "Sesión expirada",
                                                            "Tu sesión venció. Cerrá y volvé a iniciar sesión.")
            except ApiError as e:
                                        QMessageBox.critical(self, "Error", f"No se desasoció la radio:\n{e}")


    def limpiar_formulario(self):
        """Limpia formulario"""
        self.combo_tipo.setCurrentText("")
        self.input_interno.clear()
        self.combo_escala.setCurrentText("")
        self.tabla_radios_disponibles.clearSelection()
        self.label_imagen.setText("📷\n\nSeleccione una radio\nde la lista")
        self.label_imagen.setStyleSheet("""
            QLabel {
                border: 2px dashed #cfd8dc;
                border-radius: 8px;
                background-color: white;
                color: #90a4ae;
                font-size: 10pt;
                font-weight: bold;
                padding: 10px;
            }
        """) 
        
    def capturar_modelo_actual(self, modelo):
        return modelo
    
    def consulta_ruta_imagen(self, modelo):
            """Consulta la ruta de la imagen desde la API"""
            try:
                if not modelo or modelo.strip() == "":
                    return None
                
                # Limpiar el modelo
                modelo_limpio = modelo.strip()
    
                # Obtener la respuesta como texto
                resultado = self.api.get("imagen.php", {"imagen_modelo": modelo_limpio})
            
                # Verificar si hay error
                if not resultado or "Error" in resultado or "No se encontró" in resultado:
                    return None
            
                return resultado  # Retorna la ruta (ej: "motorola_xtl2500.jpg")
            
            except SesionExpirada:
                        QMessageBox.warning(self, "Sesión expirada",
                                            "Tu sesión venció. Cerrá y volvé a iniciar sesión.")
                        return None
            except ApiError as e:
                        #QMessageBox.critical(self, "Error", f"No se pudo cargar la imagen:\n{e}")
                        return None
    
    def cargar_imagen_modelo(self, modelo=None):
        """Carga la imagen del modelo seleccionado"""
    
        if not modelo or modelo == "":
            self.mostrar_placeholder()
            return

        print(f"Intentando cargar imagen para modelo: {modelo}")
    
        # 1. Consultar la API para obtener el nombre del archivo
        nombre_archivo = self.consulta_ruta_imagen(modelo)
    
        if not nombre_archivo:
            print(f"No se obtuvo nombre de archivo de la API")
            self.mostrar_placeholder(modelo)
            return
    
        # 2. Construir la ruta completa local
        ruta_imagenes = direcciones.URL.IMG_BASE_URL  # Carpeta local de imágenes
        ruta_completa = os.path.join(ruta_imagenes, nombre_archivo)
    
        print(f"Ruta completa: {ruta_completa}")
    
        # 3. Verificar si el archivo existe
        if not os.path.exists(ruta_completa):
            print(f"Archivo no encontrado en: {ruta_completa}")
            self.mostrar_placeholder(modelo)
            return
    
        # 4. Cargar la imagen
        pixmap = QPixmap(ruta_completa)
        if pixmap.isNull():
            print(f"Error al cargar imagen desde: {ruta_completa}")
            self.mostrar_placeholder(modelo)
            return
    
        # 5. Mostrar la imagen escalada
        pixmap_scaled = pixmap.scaled(
            140, 140,
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation
        )
        self.label_imagen.setPixmap(pixmap_scaled)
        self.label_imagen.setStyleSheet("""
        QLabel {
            border: 2px solid #cfd8dc;
            border-radius: 8px;
            background-color: white;
            padding: 5px;
        }
        """)
        print(f"✓ Imagen cargada exitosamente")
        
    def llenar_combo(self, endpoint, combo, campo_json,
                         incluir_todos=False, incluir_escriba=False):
            """
            endpoint: archivo PHP (ej. 'marcas.php')
            combo: el objeto QComboBox
            campo_json: nombre de la clave en el JSON (ej. 'marca')
            incluir_todos: agrega el item "Todos"
            incluir_escriba: agrega el item "Escriba o seleccione"
            """
            data = []
     
            try:
                # El token se adjunta solo y la URL base ya la sabe el cliente.
                data = self.api.get(endpoint)
     
                items = [str(obj[campo_json]) for obj in data]
     
                combo.clear()
                if incluir_todos:
                    combo.addItem("Todos")
                elif incluir_escriba:
                    combo.addItem("Escriba o seleccione")
     
                combo.addItems(items)
     
            except SesionExpirada:
                # Se propaga: la maneja llenar_desplegables() una sola vez,
                # así no aparecen seis carteles seguidos.
                raise
     
            except ApiError as e:
                # Antes esto era un print() invisible para el usuario.
                QMessageBox.warning(self, "Error al cargar datos",
                                    f"No se pudo cargar '{endpoint}':\n{e}")
     
            except KeyError:
                QMessageBox.warning(
                    self, "Error de datos",
                    f"El campo '{campo_json}' no existe en la respuesta de {endpoint}.")
     
            return data
    
    def llenar_desplegables(self):
        """Llena todos los combos de la pestaña"""
        self.llenar_combo("tipo_vehiculo.php", self.combo_tipo, "tipo_vehiculo", incluir_escriba=False)
        self.llenar_combo("escalas.php", self.combo_escala, "escala", incluir_escriba=False)
        self.llenar_combo("tipo_vehiculo.php", self.combo_filtro_tipo, "tipo_vehiculo", incluir_todos=True)
        self.llenar_combo("escalas.php", self.combo_filtro_escala, "escala", incluir_todos=True)
        self.llenar_combo("modelo_internos.php", self.combo_filtro_modelo, "modelo_equipo", incluir_todos=True)

    def guardar_vehiculo(self):
        tipo = self.combo_tipo.currentText()
        identificacion = self.input_interno.text().strip()
        escala = self.combo_escala.currentText()
        if not tipo or not identificacion or not escala:
            QMessageBox.warning(self, "⚠️ Campos Requeridos", "Por favor complete todos los campos para dar de alta un vehículo.")
            return
        try:
            resultado = self.api.post("alta_interno.php", datos={
                "tipo": tipo,
                "identificacion": identificacion,
                "escala": escala
            })
            if resultado:
                QMessageBox.information(self, "✅ Vehículo Agregado", f"El vehículo {identificacion} ha sido agregado exitosamente.")
                self.get_internos()
                self.limpiar_formulario()
            else:
                QMessageBox.warning(self, "Error", f"No se pudo agregar el vehículo: {resultado.get('message')}")
        except SesionExpirada:
            QMessageBox.warning(self, "Sesión expirada",
                "Tu sesión venció. Cerrá y volvé a iniciar sesión.")
        except ApiError as e:
            QMessageBox.critical(self, "Error", f"Alta de interno:\n{e}")

    def ver_historial_vehiculo(self):
        """Ver historial del equipo"""
        fila = self.tabla.currentRow()
        if fila < 0:
            QMessageBox.warning(self, "Aviso", "Debe seleccionar un vehículo.")
            return 
        identificacion = self.datos_filtrados[fila].get("identificacion", "")
        vehiculo = {
            "tipo": self.datos_filtrados[fila].get("tipo", ""),
            "identificacion": identificacion,
        }
        try:
            historial_internos = self.api.get("historialVehiculos.php", {"identificacion": identificacion})

            if historial_internos:
                    df_historial = pd.DataFrame(historial_internos)
                    equipo = None
                    dialogo = DialogoHistorial(df_historial, equipo, vehiculo, self) 
                    dialogo.showMaximized()
                    dialogo.exec()
            else:
                    QMessageBox.information(self, "Info", "No hay historial para este vehículo.")

        except SesionExpirada:
                    QMessageBox.warning(self, "Sesión expirada",
                                        "Tu sesión venció. Cerrá y volvé a iniciar sesión.")
        except ApiError as e:
                    QMessageBox.critical(self, "Error", f"No se pudo cargar el historial:\n{e}")
            
    def ver_historial_equipo(self):
        """Ver historial del equipo"""
        fila_radio = self.tabla_radios_disponibles.currentRow()
        if fila_radio < 0:
            QMessageBox.warning(self, "Aviso", "Debe seleccionar un equipo.")
            return
    
        id_equipo = self.tabla_radios_disponibles.item(fila_radio, 0).text()
        equipo = {
            "id_equipo": id_equipo,
            "marca": self.tabla_radios_disponibles.item(fila_radio, 1).text(),
            "modelo_equipo": self.tabla_radios_disponibles.item(fila_radio, 2).text(),
            "numero_serie": self.tabla_radios_disponibles.item(fila_radio, 3).text(),
            "escala": self.tabla_radios_disponibles.item(fila_radio, 4).text()
        }
        
        try:
            historial_radios = self.api.get("historialEquipo.php", {"id_equipo": id_equipo})

            if historial_radios:
                    df_historial = pd.DataFrame(historial_radios)
                    vehiculo=None
                    dialogo = DialogoHistorial(df_historial, equipo, vehiculo, self) 
                    dialogo.showMaximized()
                    dialogo.exec()
            else:
                    QMessageBox.information(self, "Info", "No hay historial para este equipo.")

        except SesionExpirada:
                    QMessageBox.warning(self, "Sesión expirada",
                                        "Tu sesión venció. Cerrá y volvé a iniciar sesión.")
        except ApiError as e:
                    QMessageBox.critical(self, "Error", f"No se pudo cargar el historial:\n{e}")
          
    def baja_vehiculo(self):
        """Da de baja un vehículo"""
        fila = self.tabla.currentRow()
        if fila < 0:
            QMessageBox.warning(self, "⚠️ Sin Selección",
                                "Seleccione un vehículo de la tabla.")
            return
        
        if fila >= len(self.datos_filtrados):
            return
        
        vehiculo = self.datos_filtrados[fila]
        id_vehiculo = vehiculo.get('id_vehiculo', '')
        identificacion = vehiculo.get('idenficacion', '')
        print(f"vehiclo seleccionado{self.datos_filtrados[fila]}")
        respuesta = QMessageBox.question(
                self,
                "Confirmar Baja",
                f"¿Desea dar de baja el vehículo?\n\nN° Interno: {vehiculo.get('identificacion', '')} ",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
        if respuesta == QMessageBox.StandardButton.Yes:
            dialogo = DialogoMotivoPapelera(identificacion=identificacion, parent= self)
            if dialogo.exec() == QDialog.DialogCode.Accepted:
                motivo = dialogo.get_motivo()
                try:
                    resultado = self.api.post("baja_interno.php", datos={
                        "id_vehiculo": id_vehiculo,
                        "motivo": motivo,
                        "identificacion": vehiculo.get('identificacion', '')
                    })
                    if resultado:
                        self.cargar_tabla()
                        QMessageBox.information(
                            self, "✅ Vehículo dado de baja", f"El vehículo {vehiculo.get('identificacion', '')} ha sido dado de baja correctamente.")
                    
                        self.get_internos()
                        self.borrar_campos()
                    else:
                        QMessageBox.warning(self, "Error", f"Error al dar de baja el vehículo: {resultado.get('message')}")
                except SesionExpirada:
                    QMessageBox.warning(self, "Sesión expirada",
                        "Tu sesión venció. Cerrá y volvé a iniciar sesión.")
                except ApiError as e:
                    QMessageBox.critical(self, "Error", f"Baja interno:\n{e}")

    def mostrar_placeholder(self, modelo=None):
            self.label_imagen.clear()
            if modelo:
                self.label_imagen.setText(
                    f"📷\n\n{modelo}\n\nSin imagen\ndisponible")
            else:
                self.label_imagen.setText("📷\n\nSin imagen\ndisponible")
    
            self.label_imagen.setStyleSheet("""
                QLabel {
                    border: 3px dashed #cfd8dc;
                    border-radius: 8px;
                    background-color:  #fafafa;
                    color: #90a4ae;
                    font-size: 9pt;
                    font-weight: bold;
                }
            """)
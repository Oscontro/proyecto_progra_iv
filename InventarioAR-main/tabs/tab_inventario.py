"""
Pestaña:   Inventario
Versión:  4.1 - ICONOS ACTUALIZADOS
Fecha: 2025-12-14
Autor: lucasarsa2015-cpu
Descripción: Pestaña de inventario con filtros, búsqueda y tabla
"""
import time
import requests
import pandas as pd
import direcciones # type: ignore
from base_tab import ApiTab
from api_client import ApiError, SesionExpirada
from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QFrame, QComboBox, QTableWidget, QTableWidgetItem,
    QHeaderView, QMessageBox, QFileDialog, QAbstractItemView, QDialog, QScrollArea,
    QGridLayout, QTextEdit, QMenu, QSpinBox, QCheckBox, QMessageBox
)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QAction, QFont, QColor, QBrush
from openpyxl import load_workbook
from openpyxl.utils import get_column_letter



from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QLabel, 
                             QTextEdit, QPushButton, QHBoxLayout)



class DialogEnviarTaller(QDialog):
    def __init__(self, api, equipo=None, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Enviar a Taller")
        self.setMinimumWidth(300)
        self.api = api
        layout = QVBoxLayout()
        self.id_equipo = equipo.get("id_equipo", "")
        self.numero_serie = equipo.get("numero_serie", "")
        # Mensaje
        layout.addWidget(QLabel("Por favor, seleccione el taller:"))
        
        # ComboBox
        self.combo_taller = QComboBox()
        self.cargar_talleres()
        layout.addWidget(self.combo_taller)
        
        self.txt_motivo = QTextEdit()
        self.txt_motivo.setMaximumHeight(100)
        layout.addWidget(self.txt_motivo)
        
        # Botones
        btn_layout = QHBoxLayout()
        btn_aceptar = QPushButton("Aceptar")
        btn_cancelar = QPushButton("Cancelar")
        btn_aceptar.clicked.connect(self.enviar_a_taller)
        btn_cancelar.clicked.connect(self.reject)
        btn_layout.addWidget(btn_aceptar)
        btn_layout.addWidget(btn_cancelar)
        layout.addLayout(btn_layout)
        
        self.setLayout(layout)
    
    def cargar_talleres(self):
        try:
            data = self.api.get("talleres.php")
            for taller in data:
                self.combo_taller.addItem(taller['taller'], taller['id_taller'])
        except SesionExpirada:
            QMessageBox.warning(self, "Sesión expirada",
                                "Tu sesión venció. Cerrá y volvé a iniciar sesión.")
            self.reject()          
        except ApiError as e:
            QMessageBox.warning(self, "Error", f"No se pudieron cargar los talleres:\n{e}")
            
    
    def get_id_taller(self):
        return self.combo_taller.currentData()
    
    def enviar_a_taller(self):
        taller = self.get_id_taller()
        observaciones = self.txt_motivo.toPlainText().strip()
        try:
            respuesta = self.api.post("enviar_a_taller.php", {
                "id_equipo": self.id_equipo,
                "id_taller": taller,
                "observaciones": observaciones,
            })
            # Si llegamos acá, fue 2xx. El ApiClient ya validó el código
            # y desenvolvió el "data". Si algo falló, saltó una excepción.
            QMessageBox.information(
                self, "Enviado",
                f"Equipo {self.numero_serie} enviado a taller correctamente.")

            # Refrescar la tabla de la pestaña que abrió este diálogo:
            if self.parent() and hasattr(self.parent(), "obtener_datos_iniciales"):
                self.parent().obtener_datos_iniciales()

            self.accept()
            
            

        except SesionExpirada:
            QMessageBox.warning(self, "Sesión expirada",
                                "Tu sesión venció. Cerrá y volvé a iniciar sesión.")
            self.reject()
        except ApiError as e:
            QMessageBox.warning(self, "Error", f"No se pudo enviar a taller:\n{e}")
                
            
    
    
class DialogoMotivoPapelera(QDialog):
    def __init__(self, numero_serie=None, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Enviar a papelera")
        self.setMinimumWidth(400)
        
        layout = QVBoxLayout(self)
        
        layout.addWidget(QLabel(f"¿Enviar equipo {numero_serie} a la papelera?"))
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
    def __init__(self, datos_historial=None, dato_equipo=None, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Registros de historial")
        self.setModal(True)
        
        self.marca = dato_equipo.get("marca", "")
        self.modelo = dato_equipo.get("modelo_equipo", "")
        self.serie = dato_equipo.get("numero_serie", "")        
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
        
        header = QLabel(f"📜 Historial de {self.marca} {self.modelo} {self.serie}")
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
            7, QHeaderView.ResizeMode.ResizeToContents)  # ip usuario

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



class DialogoProgramacionModi(QDialog):
    """Ventana modal para configurar frecuencias y canales"""

    def __init__(self, api,  parent=None, programacion_actual=None, nombre_config=None, numero_serie=None):
        super().__init__(parent)
        self.setWindowTitle("⚙️ Programación de Frecuencias y Canales")
        self.setModal(True)
        self.api = api

        self.programacion_data = programacion_actual if programacion_actual else {
            'cantidad_canales': 16,
            'canales': []
        }
        self.canales_data = []
        self.crear_interfaz()
        self.llenar_desplegables()
        self.cargar_datos_existentes()
        self.cargar_datos_programacion(numero_serie)
        
        

    def crear_interfaz(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        header = QLabel("⚙️ CONFIGURACIÓN DE CANALES")
        header.setFont(QFont("Arial", 18, QFont.Weight.Bold))
        header.setAlignment(Qt.AlignmentFlag. AlignCenter)
        header.setFixedHeight(60)
        header.setStyleSheet("""
            QLabel {
                background:  qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop: 0 #7b1fa2, stop:1 #9c27b0);
                color:  white;
                padding: 15px;
                border-radius:  8px;
            }
        """)
        layout.addWidget(header)

        controles_layout = QHBoxLayout()

        lbl_cant = QLabel("Cantidad de Canales:")
        lbl_cant.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        lbl_cant.setStyleSheet("color: white;")
        controles_layout.addWidget(lbl_cant)

        self.spin_canales = QSpinBox()
        self.spin_canales.setRange(1, 999)
        self.spin_canales.setValue(self.programacion_data['cantidad_canales'])
        self.spin_canales.setFont(QFont("Arial", 13, QFont.Weight.Bold))
        self.spin_canales.setFixedSize(80, 40)
        self.spin_canales.setStyleSheet("""
            QSpinBox {
                border: 2px solid #cfd8dc;
                border-radius: 6px;
                padding: 5px;
                background-color: white;
                color: grey;
            }
            QSpinBox: focus {
                border: 2px solid #7b1fa2;
            }
        """)
        controles_layout.addWidget(self.spin_canales)

        btn_generar = QPushButton("🔄 Generar Tabla")
        btn_generar.setAutoDefault(False) 
        btn_generar.setDefault(False)    
        btn_generar.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        btn_generar.setFixedHeight(40)
        btn_generar.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_generar.setStyleSheet("""
            QPushButton {
                background-color: #7b1fa2;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 0 20px;
            }
            QPushButton:hover {
                background-color: #6a1b9a;
            }
        """)
        btn_generar.clicked.connect(self.generar_tabla)
        controles_layout.addWidget(btn_generar)
        
        estilo_label = "color: #37474f; font-weight: bold; font-size: 11pt;"

        controles_layout.addStretch()

        layout.addLayout(controles_layout)

        self.tabla_canales = QTableWidget()
        self.tabla_canales.setColumnCount(5)
        self.tabla_canales.setHorizontalHeaderLabels([
            "Canal #",
            "TX (MHz)",
            "RX (MHz)",
            "Codificación",
            "Código"
        ])

        self.tabla_canales.setStyleSheet("""
            QTableWidget {
                border: 2px solid #cfd8dc;
                border-radius: 8px;
                gridline-color: #eceff1;
                font-size: 11pt;
                background-color: white;
                color: grey;
            }
            QTableWidget::item {
                padding: 10px;
            }
            QTableWidget::item:selected {
                background-color: #e1bee7;
                color: #4a148c;
            }
            QHeaderView::section {
                background-color: #7b1fa2;
                color: white;
                font-size: 11pt;
                font-weight: bold;
                padding: 12px;
                border:  none;
            }
        """)

        header = self.tabla_canales.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode. Stretch)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.Stretch)

        self.tabla_canales.verticalHeader().setDefaultSectionSize(50)
        self.tabla_canales.setAlternatingRowColors(True)

        layout.addWidget(self. tabla_canales)

        plantillas_layout = QHBoxLayout()
        plantillas_layout.setSpacing(15)
        
        estilo_label = "color: #37474f; font-weight: bold; font-size: 11pt;"
        estilo_input = """
            QLineEdit, QComboBox {
                border: 2px solid #cfd8dc;
                border-radius: 6px;
                padding: 12px 10px;
                font-size:  11pt;
                background-color: white;
                min-height: 18px;
                color: black;
            }
            QLineEdit:focus, QComboBox:focus {
                border:  2px solid #1976d2;
                background-color: white;
                color: black;
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
            QComboBox QAbstractItemView {
                background-color: white;
                color: black;
                border: 1px solid #cfd8dc;
                selection-background-color: #1976d2;
                selection-color: white;
            }
        """
        
        lbl = QLabel("Plantilla:")
        lbl.setStyleSheet(estilo_label)
        lbl.setAlignment(Qt.AlignmentFlag.AlignRight |
                         Qt.AlignmentFlag.AlignVCenter)
        plantillas_layout.addWidget(lbl, 0)

        self.combo_plantilla = QComboBox()
        self.combo_plantilla.setEditable(True)
        self.combo_plantilla.setPlaceholderText("Seleccione o escriba...")
        self.combo_plantilla.lineEdit().setPlaceholderText("Seleccione o escriba...")
        self.combo_plantilla.setFixedHeight(45)
        self.combo_plantilla.setStyleSheet(estilo_input)
        plantillas_layout.addWidget(self.combo_plantilla, 1)

        self.combo_plantilla.view().setStyleSheet("""
        QAbstractItemView {
        background-color: white;
        color: black;
        border: 1px solid #cfd8dc;
        outline: 0;
        }
        QAbstractItemView::item {
        padding: 8px 10px;
        color: black;
        }
        QAbstractItemView::item:hover {
        background-color: #e3f2fd;
        color: black;
        }
        QAbstractItemView::item:selected {
        background-color: #1976d2;
        color: white;
        }
        """)
        
        btn_cargar_plantilla = QPushButton("🔄 Cargar Plantilla")
        btn_cargar_plantilla.setAutoDefault(False) 
        btn_cargar_plantilla.setDefault(False)  
        btn_cargar_plantilla.setFont(QFont("Arial", 11, QFont.Weight.Bold))
        btn_cargar_plantilla.setFixedHeight(40)
        btn_cargar_plantilla.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_cargar_plantilla.setStyleSheet("""
            QPushButton {
                background-color:  #f57c00;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 0 20px;
            }
            QPushButton:hover {
                background-color: #e65100;
            }
        """)
        btn_cargar_plantilla.clicked.connect(self.cargar_plantilla)
        plantillas_layout.addWidget(btn_cargar_plantilla)
        
        nombre_plantilla = QLineEdit()
        nombre_plantilla.setPlaceholderText("Nombre de la plantilla")
        nombre_plantilla.setFixedHeight(45)
        nombre_plantilla.setFixedWidth(324)
        nombre_plantilla.setStyleSheet(estilo_input)
        plantillas_layout.addWidget(nombre_plantilla, 2)
        self.nombre_config = nombre_plantilla
        

        btn_guardar = QPushButton("💾 Guardar Plantilla")
        btn_guardar.hide()
        btn_guardar.setAutoDefault(False) 
        btn_guardar.setDefault(False)  
        btn_guardar.setFont(QFont("Arial", 11, QFont.Weight.Bold))
        btn_guardar.setFixedHeight(40)
        btn_guardar.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_guardar.setStyleSheet("""
            QPushButton {
                background-color:  #f57c00;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 0 20px;
            }
            QPushButton:hover {
                background-color: #e65100;
            }
        """)
        btn_guardar.clicked.connect(self.guardar_plantilla)
        plantillas_layout.addWidget(btn_guardar)
        plantillas_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        plantillas_layout.addStretch()

        layout.addLayout(plantillas_layout)

        botones_layout = QHBoxLayout()
        botones_layout.setSpacing(12)

        btn_cancelar = QPushButton("❌ Cancelar")
        btn_cancelar.setAutoDefault(False) 
        btn_cancelar.setDefault(False)  
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
        btn_cancelar.clicked.connect(self.reject)
        botones_layout.addWidget(btn_cancelar)

        btn_aceptar = QPushButton("✅ Aceptar y Aplicar")
        btn_aceptar.setAutoDefault(False) 
        btn_aceptar.setDefault(False)  
        btn_aceptar.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        btn_aceptar.setFixedHeight(45)
        btn_aceptar.setCursor(Qt.CursorShape. PointingHandCursor)
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
        btn_aceptar.clicked.connect(self.aceptar)
        botones_layout.addWidget(btn_aceptar)

        layout.addLayout(botones_layout)

        self.setLayout(layout)

        self.generar_tabla()
        
        
    def generar_tabla(self):
        cantidad = self.spin_canales.value()
        self.tabla_canales.setRowCount(0)
        self.tabla_canales.setRowCount(cantidad)

        for fila in range(cantidad):
            item_canal = QTableWidgetItem(str(fila + 1))
            item_canal.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            item_canal.setFont(QFont("Arial", 11, QFont.Weight.Bold))
            item_canal.setFlags(item_canal.flags() & ~
                                Qt.ItemFlag.ItemIsEditable)
            self.tabla_canales.setItem(fila, 0, item_canal)

            tx_edit = QLineEdit()
            tx_edit.setPlaceholderText("000.000")
            tx_edit.setAlignment(Qt.AlignmentFlag.AlignCenter)
            tx_edit.setFont(QFont("Arial", 11))
            tx_edit.returnPressed.connect(lambda: self.focusNextChild())
            tx_edit.setStyleSheet("""
                QLineEdit {
                    border: 1px solid #cfd8dc;
                    padding: 5px;
                    background-color: white;
                    color: grey;
                }
                QLineEdit:focus {
                    border: 2px solid #7b1fa2;
                }
            """)
            tx_edit.textChanged.connect(
                lambda text, row=fila: self.replicar_tx_a_rx(row, text))
            self.tabla_canales.setCellWidget(fila, 1, tx_edit)

            rx_edit = QLineEdit()
            rx_edit.setPlaceholderText("000.000")
            rx_edit.setAlignment(Qt.AlignmentFlag.AlignCenter)
            rx_edit.setFont(QFont("Arial", 11))
            rx_edit.returnPressed.connect(lambda: self.focusNextChild())
            rx_edit.setStyleSheet("""
                QLineEdit {
                    border: 1px solid #cfd8dc;
                    padding: 5px;
                    background-color: white;
                    color: grey;
                }
                QLineEdit:focus {
                    border: 2px solid #7b1fa2;
                }
            """)
            self.tabla_canales.setCellWidget(fila, 2, rx_edit)

            checkbox_widget = QWidget()
            checkbox_layout = QHBoxLayout(checkbox_widget)
            checkbox_layout.setContentsMargins(5, 0, 5, 0)
            checkbox_layout.setSpacing(10)

            cb_sql = QCheckBox("SQL")
            cb_sql.setFont(QFont("Arial", 10, QFont.Weight.Bold))
            cb_sql.setStyleSheet("color: grey;")
            cb_dpl = QCheckBox("DPL")
            cb_dpl.setFont(QFont("Arial", 10, QFont.Weight. Bold))
            cb_dpl.setStyleSheet("color: grey;")
            cb_tpl = QCheckBox("TPL")
            cb_tpl.setFont(QFont("Arial", 10, QFont.Weight.Bold))
            cb_tpl.setStyleSheet("color: grey;")

            cb_sql.stateChanged.connect(
                lambda state, row=fila, tipo='SQL': self.checkbox_changed(row, tipo, state))
            cb_dpl.stateChanged.connect(
                lambda state, row=fila, tipo='DPL': self.checkbox_changed(row, tipo, state))
            cb_tpl.stateChanged.connect(
                lambda state, row=fila, tipo='TPL': self.checkbox_changed(row, tipo, state))

            checkbox_layout.addWidget(cb_sql)
            checkbox_layout.addWidget(cb_dpl)
            checkbox_layout.addWidget(cb_tpl)
            checkbox_layout.addStretch()

            self.tabla_canales.setCellWidget(fila, 3, checkbox_widget)

            codigo_edit = QLineEdit()
            codigo_edit.setEnabled(False)
            codigo_edit.setPlaceholderText("Código")
            codigo_edit.setFont(QFont("Arial", 11))
            codigo_edit.returnPressed.connect(lambda: self.focusNextChild())
            codigo_edit.setAlignment(Qt.AlignmentFlag.AlignCenter)
            codigo_edit.setStyleSheet("""
                QLineEdit {
                    border: 1px solid #cfd8dc;
                    background-color: #eceff1;
                    padding:  5px;
                    color: black;
                }
                QLineEdit:enabled {
                    border: 1px solid #7b1fa2;
                    background-color: white;
                }
                QLineEdit:enabled:focus {
                    border:  2px solid #7b1fa2;
                }
            """)
            self.tabla_canales.setCellWidget(fila, 4, codigo_edit)
              
                
    def replicar_tx_a_rx(self, row, text):
        """Replica el valor de TX en RX automáticamente"""
        rx_widget = self.tabla_canales.cellWidget(row, 2)
        if rx_widget and isinstance(rx_widget, QLineEdit):
            current_rx = rx_widget.text()
            if not current_rx or not rx_widget.isModified():
                rx_widget.setText(text)

    def checkbox_changed(self, row, tipo, state):
        checkbox_widget = self.tabla_canales.cellWidget(row, 3)
        codigo_widget = self.tabla_canales.cellWidget(row, 4)

        if state == Qt.CheckState.Checked.value:
            for cb in checkbox_widget.findChildren(QCheckBox):
                if cb.text() != tipo:
                    cb.blockSignals(True)
                    cb.setChecked(False)
                    cb.blockSignals(False)

            if tipo in ['DPL', 'TPL']:
                codigo_widget.setEnabled(True)
                codigo_widget.setFocus()
            else:
                codigo_widget.setEnabled(False)
                codigo_widget.clear()
        else:
            codigo_widget.setEnabled(False)
            codigo_widget.clear()

    def cargar_plantilla(self):
        self.canales_data = []
        plantilla_seleccionada = self.combo_plantilla.currentText()
        if not plantilla_seleccionada:
            QMessageBox.warning(self, "Error", "Por favor, seleccione una plantilla válida.")
            return
        try:
                        plantilla_data = self.api.get("cargar_plantillas.php",
                                                      {"nombre_config": plantilla_seleccionada})
                        self.programacion_data = plantilla_data
                        self.cargar_datos_existentes()
                        QMessageBox.information(self, "Éxito",
                            f"Plantilla '{plantilla_seleccionada}' cargada correctamente.")

        except SesionExpirada:
            QMessageBox.warning(self, "Sesión expirada",
                                "Tu sesión venció. Cerrá y volvé a iniciar sesión.")
        except ApiError as e:
            QMessageBox.critical(self, "Error", f"No se pudo cargar la plantilla:\n{e}")

    def guardar_plantilla(self):
        self.canales_data = []

        for fila in range(self.tabla_canales.rowCount()):
            tx_widget = self.tabla_canales.cellWidget(fila, 1)
            rx_widget = self.tabla_canales.cellWidget(fila, 2)
            checkbox_container = self.tabla_canales.cellWidget(fila, 3)
            cod_widget = self.tabla_canales.cellWidget(fila, 4)
            
            tipo_cod = "Ninguno"
            if checkbox_container:
                for cb in checkbox_container.findChildren(QCheckBox):
                    if cb.isChecked():
                        tipo_cod = cb.text()
                        break    

            canal = {
                "nombre_config": self.nombre_config.text(),
                "numero_canal": fila + 1,
                "frecuencia_tx": tx_widget.text() if tx_widget else "",
                "frecuencia_rx": rx_widget.text() if rx_widget else "",
                "codificacion" : tipo_cod,
                "codigo_squelch": cod_widget.text() if cod_widget else ""
            }
            self.canales_data.append(canal)

        self.programacion_data['cantidad_canales'] = self.spin_canales.value()
        self.programacion_data['canales'] = self.canales_data
        self.subir_programacion_api(self.programacion_data)
            
    def get_programacion(self):
        """Devuelve la programación de canales configurada"""
        return self.programacion_data
            
    def cargar_datos_existentes(self):
        canales = self.programacion_data.get('canales', [])
        cantidad_canales = self.programacion_data.get('cantidad_canales') or len(canales) or 16

        # Sincronizamos el spin SIN disparar señales de más.
        self.spin_canales.blockSignals(True)
        self.spin_canales.setValue(cantidad_canales)
        self.spin_canales.blockSignals(False)

        # Clave del arreglo: regeneramos la tabla con la cantidad exacta.
        # Esto BORRA las filas y widgets viejos y crea todo de nuevo, limpio.
        print(f"cantidad_canales: {cantidad_canales}, len(canales): {len(canales)}")
        self.generar_tabla()

        if not canales:
            return

        for canal in canales:
            fila = canal['numero_canal'] - 1
            if fila >= self.tabla_canales.rowCount():
                continue

            tx_widget = self.tabla_canales.cellWidget(fila, 1)
            if tx_widget:
                tx_widget.setText(canal.get('frecuencia_tx', ''))

            rx_widget = self.tabla_canales.cellWidget(fila, 2)
            if rx_widget:
                rx_widget.setText(canal.get('frecuencia_rx', ''))

            tipo = canal.get('codificacion', '')
            checkbox_container = self.tabla_canales.cellWidget(fila, 3)
            if checkbox_container and tipo:
                for cb in checkbox_container.findChildren(QCheckBox):
                    if cb.text() == tipo:
                        cb.setChecked(True)
                        break

            codigo_widget = self.tabla_canales.cellWidget(fila, 4)
            if codigo_widget:
                codigo_widget.setText(canal.get('codigo_squelch', ''))

        if canales and canales[0].get('nombre_config'):
            self.nombre_config.setText(canales[0]['nombre_config'])
            
    def cargar_datos_programacion(self, numero_serie):
        self.canales_data = []
        """Función para cargar datos de programacion de frecuencias."""
        if not numero_serie:
            return
        
        try:
            self.programacion_data = self.api.get("cargar_programacion.php", {"numero_serie": numero_serie})
            self.cargar_datos_existentes()
        except SesionExpirada:
                    QMessageBox.warning(self, "Sesión expirada",
                                        "Tu sesión venció. Cerrá y volvé a iniciar sesión.")
        except ApiError as e:
                    QMessageBox.critical(self, "Error", f"No se pudo cargar la programación:\n{e}")
            
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
        try:
            self.llenar_combo("plantillas.php", self.combo_plantilla, "nombre_plantilla", incluir_escriba=False)
        except SesionExpirada:
            self.window().sesion_expirada()

    def subir_programacion_api(self, programacion_data=None):
        """Envía la programación de canales a la API"""
        try:
            resultado = self.api.post("programacion_canales.php", self.programacion_data)

            # Si llegamos a esta línea, el servidor respondió 2xx: se guardó bien.
            # Cualquier error (validación, base, token) ya habría saltado como excepción.
            QMessageBox.information(self, "Éxito",
                                    "Programación de canales guardada correctamente.")

        except SesionExpirada:
            QMessageBox.warning(self, "Sesión expirada",
                                "Tu sesión venció. Cerrá y volvé a iniciar sesión.")
        except ApiError as e:
            QMessageBox.critical(self, "Error", f"No se pudo guardar la programación:\n{e}")
            
    def aceptar(self):
        self.canales_data = []
        
        for fila in range(self.tabla_canales.rowCount()):
                    tx_widget = self.tabla_canales.cellWidget(fila, 1)
                    rx_widget = self.tabla_canales.cellWidget(fila, 2)
                    checkbox_container = self.tabla_canales.cellWidget(fila, 3)
                    cod_widget = self.tabla_canales.cellWidget(fila, 4)
                    
                    tipo_cod = "Ninguno"
                    if checkbox_container:
                        for cb in checkbox_container.findChildren(QCheckBox):
                            if cb.isChecked():
                                tipo_cod = cb.text()
                                break    
        
                    canal = {
                        "nombre_config": self.nombre_config.text(),
                        "numero_canal": fila + 1,
                        "frecuencia_tx": tx_widget.text() if tx_widget else "",
                        "frecuencia_rx": rx_widget.text() if rx_widget else "",
                        "codificacion" : tipo_cod,
                        "codigo_squelch": cod_widget.text() if cod_widget else ""
                    }
                    self.canales_data.append(canal)
        
        self.programacion_data['cantidad_canales'] = self.spin_canales.value()
        self.programacion_data['canales'] = self.canales_data
        # No hace falta crear nada más acá: get_programacion() ya expone
        # self.programacion_data, y abrir_programacion() en la pestaña lo lee
        # con dialogo.get_programacion() después de este accept().
        self.accept()


# ═══════════════════════════════════════════════════════════
#
# VENTANA MODAL: MODIFICAR EQUIPO
#
# ═══════════════════════════════════════════════════════════
class ModalModiEquipo(QDialog):
    def __init__(self, api, equipo_seleccionado, frecuencias, parent = None):
        super().__init__(parent)
        self.setWindowTitle("Modificar equipo")
        self.showMaximized()
        self.setModal(True)
        self.api = api
        self.equipo_seleccionado = equipo_seleccionado
        self.frecuencias = frecuencias or {'cantidad_canales': 0, 'canales': []}
        print("Equipo seleccionado para modificar:", self.equipo_seleccionado)
        self.programacion_data = {
            'cantidad_canales': 16,
            'canales': []
        }
        
        self.setWindowFlags(
            Qt.WindowType.Window |
            Qt.WindowType.WindowMinMaxButtonsHint |
            Qt.WindowType.WindowCloseButtonHint
        )
        
        self.crear_interfaz(equipo_seleccionado)
        self.llenar_desplegables() 
        self.cargar_valores_combo(equipo_seleccionado)
        #self.cargar_datos_programacion(self.equipo_seleccionado[3])


    
    def crear_interfaz(self, equipo_seleccionado):
        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        header = QLabel("📋 Datos de equipo")
        header.setFont(QFont("Arial", 18, QFont.Weight.Bold))
        header.setAlignment(Qt.AlignmentFlag.AlignCenter)
        header.setFixedHeight(60)
        header.setStyleSheet("""
            QLabel {
                background-color: #1976d2;
                color: white;
                border-radius: 8px;
                padding: 10px;
            }
        """)
        layout.addWidget(header)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)

        form_widget = QWidget()
        form_main_layout = QHBoxLayout()
        form_main_layout. setSpacing(20)

        left_column = self.crear_formulario()
        form_main_layout.addWidget(left_column, 2)

        form_widget.setLayout(form_main_layout)
        scroll.setWidget(form_widget)

        layout.addWidget(scroll, 1)

        botones_layout = self.crear_botones_inferiores()
        layout.addLayout(botones_layout)
        


        self.setLayout(layout)


    def crear_formulario(self):
        """Crea la columna del formulario"""
        column = QFrame()
        column.setStyleSheet("""
            QFrame {
                background-color: white;
                border-radius: 10px;
                border: 2px solid #cfd8dc;
                color: black;
            }
        """)

        form_layout = QGridLayout()
        form_layout.setContentsMargins(20, 20, 20, 20)
        form_layout.setSpacing(12)
        form_layout.setColumnMinimumWidth(0, 140)
        form_layout.setColumnStretch(1, 1)

        estilo_label = "color: #37474f; font-weight: bold; font-size: 11pt;"
        estilo_input = """
            QLineEdit, QComboBox {
                border: 2px solid #cfd8dc;
                border-radius: 6px;
                padding: 12px 10px;
                font-size:  11pt;
                background-color: #fafafa;
                min-height: 18px;
                color: black;
            }
            QLineEdit:focus, QComboBox:focus {
                border:  2px solid #1976d2;
                background-color: white;
                color: black;
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

        row = 1

        lbl = QLabel("📻 Tipo de equipo:")
        lbl.setStyleSheet(estilo_label)
        lbl.setAlignment(Qt.AlignmentFlag.AlignRight |
                         Qt.AlignmentFlag.AlignVCenter)
        form_layout.addWidget(lbl, row, 0)

        self.combo_tipo = QComboBox()
        self.combo_tipo.setEditable(True)
        self.combo_tipo.setPlaceholderText("Seleccione o escriba...")
        self.combo_tipo.lineEdit()#.setPlaceholderText("Seleccione o escriba...")
        self.combo_tipo.setFixedHeight(45)
        self.combo_tipo.setStyleSheet(estilo_input)
        form_layout.addWidget(self.combo_tipo, row, 1)
        row += 1

        lbl = QLabel("🏢 Marca:")
        lbl.setStyleSheet(estilo_label)
        lbl.setAlignment(Qt.AlignmentFlag.AlignRight |
                         Qt.AlignmentFlag.AlignVCenter)
        form_layout.addWidget(lbl, row, 0)

        self.combo_marca = QComboBox()
        self.combo_marca.setEditable(True)
        self.combo_marca.setPlaceholderText("Seleccione o escriba...")
        self.combo_marca.lineEdit()#.setPlaceholderText("Seleccione o escriba...")
        self.combo_marca.setFixedHeight(45)
        self.combo_marca.setStyleSheet(estilo_input)
        form_layout.addWidget(self.combo_marca, row, 1)
        row += 1

        lbl = QLabel("📱 Modelo:")
        lbl.setStyleSheet(estilo_label)
        lbl.setAlignment(Qt.AlignmentFlag.AlignRight |
                         Qt.AlignmentFlag.AlignVCenter)
        form_layout.addWidget(lbl, row, 0)

        self.combo_modelo = QComboBox()
        self.combo_modelo.setEditable(True)
        self.combo_modelo.setPlaceholderText("Seleccione o escriba...")
        self.combo_modelo.lineEdit()#.setPlaceholderText("Seleccione o escriba...")
        self.combo_modelo.setFixedHeight(45)
        self.combo_modelo.setStyleSheet(estilo_input)
        #self.combo_modelo.currentTextChanged.connect(self.cargar_imagen_modelo)
        form_layout. addWidget(self.combo_modelo, row, 1)
        row += 1

        lbl = QLabel("🔢 N° de Serie:")
        lbl.setStyleSheet(
            "color: #c62828; font-weight: bold; font-size: 11pt;")
        lbl.setAlignment(Qt.AlignmentFlag.AlignRight |
                         Qt.AlignmentFlag.AlignVCenter)
        form_layout.addWidget(lbl, row, 0)

        self.input_serie = QLineEdit()
        self.input_serie.setReadOnly(True)
        self.input_serie.setFixedHeight(45)
        self.input_serie.setStyleSheet("""
            QLineEdit {
                border: 2px solid #c62828;
                border-radius: 6px;
                padding: 12px 10px;
                font-size: 11pt;
                font-weight: bold;
                background-color: #ffebee;
                min-height: 18px;
                color: grey;
            }
            QLineEdit: focus {
                border: 2px solid #b71c1c;
                background-color: white;
            }
        """)
        #self.input_serie.textChanged.connect(self.formatear_numero_serie)
        form_layout.addWidget(self.input_serie, row, 1)
        row += 1

        lbl = QLabel("📊 Escala:")
        lbl.setStyleSheet(estilo_label)
        lbl.setAlignment(Qt.AlignmentFlag.AlignRight |
                         Qt.AlignmentFlag.AlignVCenter)
        form_layout.addWidget(lbl, row, 0)

        self.combo_escala = QComboBox()
        self.combo_escala.setEditable(True)
        self.combo_escala.setPlaceholderText("Seleccione o escriba...")
        self.combo_escala.lineEdit().setMaxLength(3)
        self.combo_escala.setFixedHeight(45)
        self.combo_escala.setStyleSheet(estilo_input)
        form_layout.addWidget(self.combo_escala, row, 1)
        row += 1

        lbl = QLabel("🏭 Sector:")
        lbl.setStyleSheet(estilo_label)
        lbl.setAlignment(Qt.AlignmentFlag.AlignRight |
                         Qt.AlignmentFlag.AlignVCenter)
        form_layout.addWidget(lbl, row, 0)

        self.combo_sector = QComboBox()
        self.combo_sector.setEditable(True)
        self.combo_sector.setPlaceholderText("Seleccione o escriba...")
        self.combo_sector.lineEdit()#.setPlaceholderText("Seleccione o escriba...")
        self.combo_sector.setFixedHeight(45)
        self.combo_sector.setStyleSheet(estilo_input)
        form_layout.addWidget(self. combo_sector, row, 1)
        row += 1

        lbl = QLabel("✅ Estado:")
        lbl.setStyleSheet(estilo_label)
        lbl.setAlignment(Qt.AlignmentFlag.AlignRight |
                         Qt.AlignmentFlag.AlignVCenter)
        form_layout.addWidget(lbl, row, 0)

        self.combo_estado = QComboBox()
        self.combo_estado.setEditable(True)
        self.combo_estado.setPlaceholderText("Seleccione o escriba...")
        self.combo_estado.lineEdit()#.setPlaceholderText("Seleccione o escriba...")
        self.combo_estado.setFixedHeight(45)
        self.combo_estado.setStyleSheet(estilo_input)
        form_layout.addWidget(self. combo_estado, row, 1)
        row += 1

        lbl = QLabel("⚡ Potencia:")
        lbl.setStyleSheet(estilo_label)
        lbl.setAlignment(Qt.AlignmentFlag.AlignRight |
                         Qt. AlignmentFlag.AlignVCenter)
        form_layout. addWidget(lbl, row, 0)

        self.combo_potencia = QComboBox()
        self.combo_potencia.setEditable(True)
        self.combo_potencia.setPlaceholderText("Seleccione o escriba...")
        self.combo_potencia.lineEdit().setPlaceholderText("Seleccione o escriba...")
        self.combo_potencia.setFixedHeight(45)
        self.combo_potencia.setStyleSheet(estilo_input)
        form_layout.addWidget(self.combo_potencia, row, 1)
        row += 1
        
        lbl = QLabel("⚙️ Programación:")
        lbl.setStyleSheet(estilo_label)
        lbl.setAlignment(Qt.AlignmentFlag.AlignRight |
                         Qt.AlignmentFlag.AlignTop)
        form_layout.addWidget(lbl, row, 0)

        prog_layout = QVBoxLayout()
        prog_layout.setSpacing(5)

        self.btn_programacion = QPushButton("⚙️ Configurar Canales")
        self.btn_programacion.setFont(QFont("Arial", 11, QFont.Weight.Bold))
        self.btn_programacion.setFixedHeight(45)
        self.btn_programacion.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_programacion.setStyleSheet("""
            QPushButton {
                background-color: #7b1fa2;
                color:  white;
                border: none;
                border-radius: 6px;
            }
            QPushButton:hover {
                background-color: #6a1b9a;
            }
        """)
        self.btn_programacion.clicked.connect(self.abrir_programacion)
        prog_layout.addWidget(self.btn_programacion)

        
        cantidad = self.frecuencias.get('cantidad_canales', '')

        # Creamos el label UNA sola vez, antes del if. Las dos ramas
        # solo configuran texto y color; ninguna crea el widget.
        self.label_prog_info = QLabel()
        self.label_prog_info.setFont(QFont("Arial", 9))

        if cantidad > 0:
            self.label_prog_info.setText(f"✅ Configurado ({cantidad} canales)")
            self.label_prog_info.setStyleSheet(
                "color: #1e8449; font-style: normal; font-weight: bold;")
        else:
            self.label_prog_info.setText("(No configurado)")
            self.label_prog_info.setStyleSheet(
                "color: #c62828; font-style: italic;")

        prog_layout.addWidget(self.label_prog_info)
        
        self.label_prog_name = QLabel("Sin plantilla cargada")
        self.label_prog_name.setFont(QFont("Arial", 10))
        self.label_prog_name.setStyleSheet(
            "color: black;")
        prog_layout.addWidget(self.label_prog_name)

        form_layout.addLayout(prog_layout, row, 1)
        row += 1

        lbl = QLabel("📝 Observaciones:")
        lbl.setStyleSheet(estilo_label)
        lbl.setAlignment(Qt.AlignmentFlag.AlignRight |
                         Qt.AlignmentFlag.AlignTop)
        form_layout.addWidget(lbl, row, 0)

        self.text_observaciones = QTextEdit()
        self.text_observaciones.setPlaceholderText(
            "Observaciones adicionales...")
        self.text_observaciones.setFont(QFont("Arial", 10))
        self.text_observaciones.setMaximumHeight(100)
        self.text_observaciones.setStyleSheet("""
            QTextEdit {
                border: 2px solid #cfd8dc;
                border-radius: 6px;
                padding: 8px;
                background-color: #fafafa;
            }
            QTextEdit: focus {
                border: 2px solid #1976d2;
                background-color: white;
            }
        """)
        form_layout.addWidget(self.text_observaciones, row, 1)

        column.setLayout(form_layout)
        return column

    def crear_botones_inferiores(self):
        """Crea los botones de acción inferiores"""
        botones_layout = QHBoxLayout()
        botones_layout.setSpacing(15)

        btn_cancelar = QPushButton("❌ Cancelar")
        btn_cancelar.setFont(QFont("Arial", 11, QFont.Weight.Bold))
        btn_cancelar.setFixedHeight(45)
        btn_cancelar.setCursor(Qt.CursorShape. PointingHandCursor)
        btn_cancelar.setStyleSheet("""
            QPushButton {
                background-color: #757575;
                color:  white;
                border: none;
                border-radius: 8px;
                padding: 0 25px;
            }
            QPushButton:hover {
                background-color: #2e7d32;
            }
        """)
        btn_cancelar.clicked.connect(self.reject)
        botones_layout.addWidget(btn_cancelar)

        botones_layout.addStretch()

        btn_guardar = QPushButton("💾 Modificar Equipo")
        btn_guardar.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        btn_guardar.setFixedHeight(45)
        btn_guardar.setCursor(Qt.CursorShape. PointingHandCursor)
        btn_guardar.setStyleSheet("""
            QPushButton {
                background:  qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #1e8449, stop:1 #27ae60);
                color: white;
                border: none;
                border-radius: 8px;
                padding: 0 35px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop: 0 #186a3b, stop:1 #1e8449);
            }
        """)
        btn_guardar.clicked.connect(self.modificar_equipo)
        botones_layout.addWidget(btn_guardar)

        return botones_layout
    
    def cargar_valores_combo(self, datos):

        widgets = [
            self.combo_tipo, self.combo_marca, self.combo_modelo, 
            self.input_serie,
            self.combo_escala, self.combo_sector, self.combo_estado, 
            self.combo_potencia, self.label_prog_name, self.text_observaciones
        ]
    
        for widget, valor in zip(widgets, datos):
            if valor is None:
                valor = ""
        
            if isinstance(widget, QLineEdit):
                widget.setText(str(valor))
            elif isinstance(widget, QComboBox):
                # Buscar el índice del valor, si no existe, agregarlo
                index = widget.findText(str(valor))
                if index >= 0:
                    widget.setCurrentIndex(index)
                else:
                    widget.setCurrentText(str(valor))
            elif isinstance(widget, QLabel):
                widget.setText(str(valor)) 
            elif isinstance(widget, QTextEdit):
                widget.setPlainText(str(valor))
    
                
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
            self.llenar_combo("sectores.php", self.combo_sector, "sector", incluir_escriba=False)
            self.llenar_combo("estados.php", self.combo_estado, "estado", incluir_escriba=False)
            self.llenar_combo("escalas.php", self.combo_escala, "escala", incluir_escriba=False)
            self.llenar_combo("potencias.php", self.combo_potencia, "potencia", incluir_escriba=False)
    
            self.datos_tipos = self.llenar_combo("tipos.php", self.combo_tipo, "tipo", incluir_escriba=False)
    
            # id_tipo actualmente seleccionado, guardado aparte — NO se vuelve
            # a derivar del índice de otro combo más adelante.
            self.id_tipo_actual = None
            self.datos_marcas = []   # se llena recién cuando el usuario elige un tipo
            # currentIndexChanged, no currentTextChanged: actualizar_marcas espera
            # un número (posición en la lista), no el texto del ítem.
            self.combo_tipo.currentIndexChanged.connect(self.actualizar_marcas)
            self.combo_marca.currentIndexChanged.connect(self.actualizar_modelos)
    
            self.combo_marca.clear()
            self.combo_marca.addItem("Primero seleccione el tipo")
            self.combo_modelo.clear()
            self.combo_modelo.addItem("Primero seleccione marca")
    
    def actualizar_marcas(self, index):
            """Filtra las marcas según el tipo seleccionado."""
            # Bloqueamos señales mientras repoblamos: si no, cada clear()/addItems()
            # de más abajo dispara currentIndexChanged sobre combo_marca y llama a
            # actualizar_modelos con datos a medio actualizar.
            self.combo_marca.blockSignals(True)
            self.combo_modelo.blockSignals(True)
    
            self.combo_marca.clear()
            self.combo_modelo.clear()
            self.combo_modelo.addItem("Primero seleccione marca")
    
            if index < 0 or index >= len(self.datos_tipos):
                self.combo_marca.addItem("Primero seleccione el tipo")
                self.id_tipo_actual = None
                self.datos_marcas = []
            else:
                self.id_tipo_actual = self.datos_tipos[index].get("id_tipo")
                endpoint = f"marcas.php?id_tipo={self.id_tipo_actual}"
                print(f"ENDPOINT ARMADO: {endpoint}") 
                # Guardamos el resultado: self.datos_marcas ahora SÍ refleja
                # exactamente lo que se muestra en combo_marca, en el mismo orden.
                self.datos_marcas = self.llenar_combo(
                    f"marcas.php?id_tipo={self.id_tipo_actual}",
                    self.combo_marca,
                    "marca",
                    incluir_escriba=False
                )
    
            self.combo_marca.blockSignals(False)
            self.combo_modelo.blockSignals(False)
    
    def actualizar_modelos(self, index):
            """Filtra los modelos según tipo Y marca seleccionados."""
            self.combo_modelo.clear()
    
            if index < 0 or index >= len(self.datos_marcas) or self.id_tipo_actual is None:
                self.combo_modelo.addItem("Primero seleccione marca")
                return
    
            id_marca = self.datos_marcas[index].get("id_marca")
    
            # & en vez de coma: así los dos parámetros llegan bien a $_GET.
            # id_tipo sale de self.id_tipo_actual, NO de indexar otra lista.
            datos_modelos = self.llenar_combo(
                f"modelos.php?id_marca={id_marca}&id_tipo={self.id_tipo_actual}",
                self.combo_modelo,
                "modelo_equipo",
                incluir_escriba=False
            )
    
            # La combinación es válida, pero puede no tener modelos cargados.
            # Distinguimos eso de un error: es información correcta, no un fallo.
            if not datos_modelos:
                self.combo_modelo.clear()
                self.combo_modelo.addItem("Sin modelos para esta marca y tipo")
        
    def abrir_programacion(self):
        numero_serie = self.equipo_seleccionado[3]
        dialogo = DialogoProgramacionModi(
                            self.api,
                            parent=self,
                            programacion_actual=self.programacion_data,
                            nombre_config=self.label_prog_name.text(),
                            numero_serie = numero_serie
                        )
        dialogo.showMaximized()
        if dialogo.exec() == QDialog.DialogCode.Accepted:
            self.programacion_data = dialogo.get_programacion()
            cantidad = self.programacion_data['cantidad_canales']
            canales = self.programacion_data.get('canales', [])
            nombre_config = canales[0].get('nombre_config')
            print(f"programacion para modi:{self.programacion_data}")
            print(f"nombre_plantilla:{nombre_config}")
            print(f"cantidad de canales desde frecuencias:{cantidad}")
            self.label_prog_info.setText(f"✅ Configurado ({cantidad} canales)")
            self.label_prog_info.setStyleSheet(
                "color: #1e8449; font-style: normal; font-weight: bold;")
            self.label_prog_name.setText(nombre_config)
            
    def modificar_equipo(self):
        equipo_modificado = self.get_modi_equipo()
        try:
            payload = {
                "equipo" : equipo_modificado,
                "frecuencias" : self.programacion_data,
            }
            self.api.post("modiEquipo.php", payload)
            print(payload)

            QMessageBox.information(self, "Éxito", "Equipo modificado correctamente.")
            self.accept()
        except SesionExpirada:
            QMessageBox.warning(self, "Sesión expirada",
                "Tu sesión venció. Cerrá y volvé a iniciar sesión.")
        except ApiError as e:
            QMessageBox.critical(self, "Error", f"No se pudo cargar la programación:\n{e}")

        
    def get_modi_equipo(self):
        """Devuelve los datos modificados del equipo"""
        # Obtener nombre_config de los canales si existe
        nombre_plantilla = ""
        if self.programacion_data.get('canales'):
            nombre_plantilla = self.programacion_data['canales'][0].get('nombre_config', '')
        elif hasattr(self, 'label_prog_name'):
            nombre_plantilla = self.label_prog_name.text()

    
        equipo_modificado = {
            "tipo": self.combo_tipo.currentText(),
            "marca": self.combo_marca.currentText(),
            "modelo_equipo": self.combo_modelo.currentText(),
            "numero_serie": self.input_serie.text(),
            "escala": self.combo_escala.currentText(),
            "sector": self.combo_sector.currentText(),
            "estado": self.combo_estado.currentText(),
            "potencia": self.combo_potencia.currentText(),
            "nombre_plantilla": nombre_plantilla,
            "observaciones": self.text_observaciones.toPlainText()
        }
        return equipo_modificado
        
    

# ═══════════════════════════════════════════════════════════
#
# PESTAÑA PRINCIPAL: INVENTARIO
#
# ═══════════════════════════════════════════════════════════

class InventarioTab(ApiTab):
    """Pestaña de inventario con filtros y tabla"""

    def __init__(self, api):
        super().__init__(api)
        self.api = api
        self.papelera_tab = None
        self.vehiculos_tab = None
        self.datos_completos = []  # SIN datos precargados
        self.datos_filtrados = []
        self.API_BASE_URL = direcciones.URL.API_BASE_URL  # URL base de la API
        self._actualizando = False

        self.crear_interfaz()
        self.llenar_desplegables()
        self.obtener_datos_iniciales()  # Cargar datos al iniciar
        
    def set_papelera_tab(self, papelera_tab):
        self.papelera_tab = papelera_tab

    def crear_interfaz(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(15)

        # === HEADER ===
        header = QLabel("📦 INVENTARIO")
        header.setFont(QFont("Arial", 20, QFont.Weight.Bold))
        header.setAlignment(Qt.AlignmentFlag.AlignCenter)
        header.setFixedHeight(60)
        header.setStyleSheet("""
            QLabel {
                background:   qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop: 0 #1565c0, stop:1 #1976d2);
                color: white;
                padding: 15px;
                border-radius:   10px;
                border: 3px solid #0d47a1;
            }
        """)
        layout.addWidget(header)

        # === BARRA DE BÚSQUEDA ===
        busqueda_layout = self.crear_barra_busqueda()
        layout.addLayout(busqueda_layout)

        # === FILTROS ===
        filtros_layout = self.crear_filtros()
        layout.addLayout(filtros_layout)

        # === TABLA ===
        self.crear_tabla()
        layout.addWidget(self.tabla, 1)

        # === BOTONES INFERIORES ===
        botones_layout = self.crear_botones()
        layout.addLayout(botones_layout)

        self.setLayout(layout)

        # Cargar tabla vacía
        self.renderizar_tabla()

    def crear_barra_busqueda(self):
        """Crea la barra de búsqueda"""
        busqueda_layout = QHBoxLayout()
        busqueda_layout.setSpacing(10)

        lbl_buscar = QLabel("🔍 Buscar:")
        lbl_buscar.setFont(QFont("Arial", 11, QFont.Weight. Bold))
        lbl_buscar.setStyleSheet("color: #37474f;")
        busqueda_layout.addWidget(lbl_buscar)

        self.input_buscar = QLineEdit()
        self.input_buscar.setPlaceholderText("N° Serie...")
        self.input_buscar.setFixedHeight(38)
        self.input_buscar.setStyleSheet("""
            QLineEdit {
                border: 2px solid #cfd8dc;
                border-radius: 6px;
                padding: 8px;
                font-size: 11pt;
                background-color:  white;
                color: black;
            }
            QLineEdit:focus {
                border: 2px solid #1976d2;
            }
        """)
        self.input_buscar.textChanged.connect(self.aplicar_filtros)
        busqueda_layout.addWidget(self.input_buscar)

        btn_limpiar = QPushButton("🗑️ Limpiar Filtros")
        btn_limpiar.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        btn_limpiar.setFixedHeight(38)
        btn_limpiar.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_limpiar.setStyleSheet("""
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
        btn_limpiar.clicked.connect(self.limpiar_filtros)
        busqueda_layout.addWidget(btn_limpiar)
        
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
        
        busqueda_layout.addStretch()

        return busqueda_layout

    def crear_filtros(self):
        """Crea la fila de filtros"""
        filtros_layout = QHBoxLayout()
        filtros_layout.setSpacing(10)

        lbl_filtros = QLabel("Filtros")
        lbl_filtros.setFont(QFont("Arial", 11, QFont.Weight.Bold))
        lbl_filtros.setStyleSheet("color: #37474f;")
        filtros_layout.addWidget(lbl_filtros)

        estilo_combo = """
            QComboBox {
            border: 2px solid #cfd8dc;
            border-radius: 6px;
            padding: 6px 10px;
            background-color: white;
            min-width: 100px;
            font-size: 10pt;
            color: black;
        }
        QComboBox:hover {
            border: 2px solid #1976d2;
        }
        QComboBox QAbstractItemView {
            background-color: white;
            color: black;
            selection-background-color: #1976d2;
            selection-color: black;
        }
        """

        # Tipo
        label_tipo = QLabel("Tipo:")
        label_tipo.setStyleSheet("color: black;")
        filtros_layout.addWidget(label_tipo)
        self.combo_filtro_tipo = QComboBox()
        self.combo_filtro_tipo.setFixedHeight(35)
        self.combo_filtro_tipo.setStyleSheet(estilo_combo)
        self.combo_filtro_tipo.currentTextChanged.connect(
            lambda: self.aplicar_filtros())
        filtros_layout.addWidget(self.combo_filtro_tipo)

        # Marca
        label_marca = QLabel("Marca:")
        label_marca.setStyleSheet("color: black;")
        filtros_layout.addWidget(label_marca)
        self.combo_filtro_marca = QComboBox()
        self.combo_filtro_marca.setFixedHeight(35)
        self.combo_filtro_marca.setStyleSheet(estilo_combo)
        self.combo_filtro_marca.currentTextChanged.connect(
            lambda: self.aplicar_filtros())
        filtros_layout.addWidget(self.combo_filtro_marca)

        # Modelo
        label_modelo = QLabel("Modelo:")
        label_modelo.setStyleSheet("color: black;")
        filtros_layout.addWidget(label_modelo)
        self.combo_filtro_modelo = QComboBox()
        self.combo_filtro_modelo.setFixedHeight(35)
        self.combo_filtro_modelo.setStyleSheet(estilo_combo)
        self.combo_filtro_modelo.currentTextChanged.connect(
            lambda: self.aplicar_filtros())
        filtros_layout.addWidget(self.combo_filtro_modelo)

        # Escala
        label_escala = QLabel("Escala:")
        label_escala.setStyleSheet("color: black;")
        filtros_layout.addWidget(label_escala)
        self.combo_filtro_escala = QComboBox()
        self.combo_filtro_escala.setFixedHeight(35)
        self.combo_filtro_escala.setStyleSheet(estilo_combo)
        self.combo_filtro_escala.currentTextChanged.connect(
            lambda: self.aplicar_filtros())
        filtros_layout.addWidget(self.combo_filtro_escala)

        # Sector
        label_sector = QLabel("Sector:")
        label_sector.setStyleSheet("color: black;")
        filtros_layout.addWidget(label_sector)
        self.combo_filtro_sector = QComboBox()
        self.combo_filtro_sector.setFixedHeight(35)
        self.combo_filtro_sector.setStyleSheet(estilo_combo)
        self.combo_filtro_sector.currentTextChanged.connect(
            lambda: self.aplicar_filtros())
        filtros_layout.addWidget(self.combo_filtro_sector)

        # Estado
        label_estado = QLabel("Estado:")
        label_estado.setStyleSheet("color: black;")
        filtros_layout.addWidget(label_estado)
        self.combo_filtro_estado = QComboBox()
        self.combo_filtro_estado.setFixedHeight(35)
        self.combo_filtro_estado.setStyleSheet(estilo_combo)
        self.combo_filtro_estado.currentTextChanged.connect(
            lambda: self.aplicar_filtros())
        filtros_layout.addWidget(self.combo_filtro_estado)

        filtros_layout.addStretch()

        return filtros_layout

    def crear_tabla(self):
        """Crea la tabla de inventario"""
        self.tabla = QTableWidget()
        self.tabla.setColumnCount(10)
        self.tabla.hideColumn(7) # Oculta Potencia
        self.tabla.hideColumn(8) # Oculta Nombre Plantilla
        self.tabla.setHorizontalHeaderLabels([
            "Tipo",
            "Marca",
            "Modelo",
            "N° Serie",
            "Escala",
            "Sector",
            "Estado",
            "Potencia",
            "Nombre Plantilla",
            "Observaciones"
        ])
        self.tabla.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.tabla.customContextMenuRequested.connect(
            lambda pos: self.mostrar_menu_contextual(self.tabla, pos))
        

        # No editable
        self.tabla.setEditTriggers(
            QAbstractItemView.EditTrigger.NoEditTriggers)

        # Selección por filas
        self.tabla.setSelectionBehavior(
            QAbstractItemView.SelectionBehavior.SelectRows)
        self.tabla.setSelectionMode(
            QAbstractItemView.SelectionMode.SingleSelection)

        # Alternar colores
        self.tabla.setAlternatingRowColors(True)
        
        # Ajustar columnas al contenido
        self.tabla.resizeColumnsToContents()

        # Estilo
        self.tabla.setStyleSheet("""
            QTableWidget {
                border: 2px solid #cfd8dc;
                border-radius: 8px;
                gridline-color: #eceff1;
                background-color:  white;
                font-size: 11pt;
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
            QTableWidget::item:alternate:selected {
                background-color: #bbdefb;
                color: #0d47a1;
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
            0, QHeaderView.ResizeMode.ResizeToContents)  # Tipo
        header.setSectionResizeMode(
            1, QHeaderView.ResizeMode.ResizeToContents)  # Marca
        header.setSectionResizeMode(
            2, QHeaderView.ResizeMode.ResizeToContents)  # Modelo
        header.setSectionResizeMode(
            3, QHeaderView.ResizeMode.Stretch)  # N° Serie
        header.setSectionResizeMode(
            4, QHeaderView.ResizeMode.ResizeToContents)  # Escala
        header.setSectionResizeMode(
            5, QHeaderView.ResizeMode.Stretch)  # Sector
        header.setSectionResizeMode(
            6, QHeaderView.ResizeMode.ResizeToContents)  # Estado
        header.setSectionResizeMode(
            7, QHeaderView.ResizeMode.ResizeToContents)  # Potencia
        header.setSectionResizeMode(
            8, QHeaderView.ResizeMode.ResizeToContents)  # Nombre Plantilla
        header.setSectionResizeMode(
            9, QHeaderView.ResizeMode.ResizeToContents) # Observaciones

        # Altura de filas
        self.tabla.verticalHeader().setDefaultSectionSize(45)

        # Conectar selección
        self.tabla.itemSelectionChanged.connect(self.on_seleccion_cambiada)

    def crear_botones(self):
        """Crea los botones inferiores"""
        botones_main = QVBoxLayout()
        botones_main.setSpacing(10)

        # Fila 1
        fila1_layout = QHBoxLayout()
        fila1_layout.setSpacing(12)

        self.btn_editar = QPushButton("📝 Editar Item")
        self.btn_editar.setEnabled(False)
        self.btn_editar.setFont(QFont("Arial", 11, QFont.Weight.Bold))
        self.btn_editar.setFixedHeight(45)
        self.btn_editar.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_editar.setStyleSheet("""
            QPushButton {
                background-color: #1976d2;
                color:  white;
                border: none;
                border-radius: 6px;
                padding: 0 25px;
            }
            QPushButton:hover {
                background-color: #1565c0;
            }
            QPushButton:disabled {
                background-color: #cfd8dc;
                color: #90a4ae;
            }
        """)
        self.btn_editar.clicked.connect(self.editar_item)
        fila1_layout.addWidget(self.btn_editar)

        self.btn_historial = QPushButton("📜 Ver Historial")
        self.btn_historial.setEnabled(False)
        self.btn_historial.setFont(QFont("Arial", 11, QFont.Weight.Bold))
        self.btn_historial.setFixedHeight(45)
        self.btn_historial.setCursor(Qt.CursorShape. PointingHandCursor)
        self.btn_historial. setStyleSheet("""
            QPushButton {
                background-color: #7b1fa2;
                color:  white;
                border: none;
                border-radius: 6px;
                padding: 0 25px;
            }
            QPushButton:hover {
                background-color: #6a1b9a;
            }
            QPushButton:disabled {
                background-color: #cfd8dc;
                color:  #90a4ae;
            }
        """)
        self.btn_historial.clicked. connect(self.ver_historial)
        fila1_layout.addWidget(self.btn_historial)

        btn_excel = QPushButton("📊 Generar Excel")
        btn_excel.setFont(QFont("Arial", 11, QFont.Weight.Bold))
        btn_excel.setFixedHeight(45)
        btn_excel.setCursor(Qt. CursorShape.PointingHandCursor)
        btn_excel.setStyleSheet("""
            QPushButton {
                background-color: #388e3c;
                color:  white;
                border: none;
                border-radius: 6px;
                padding: 0 25px;
            }
            QPushButton:hover {
                background-color: #2e7d32;
            }
        """)
        btn_excel.clicked.connect(self.generar_excel)
        fila1_layout.addWidget(btn_excel)

        fila1_layout.addStretch()

        self.btn_papelera = QPushButton("🗑️ Enviar a Papelera")
        self.btn_papelera.setEnabled(False)
        self.btn_papelera.setFont(QFont("Arial", 11, QFont.Weight.Bold))
        self.btn_papelera.setFixedHeight(45)
        self.btn_papelera.setCursor(Qt. CursorShape.PointingHandCursor)
        self.btn_papelera.setStyleSheet("""
            QPushButton {
                background-color: #c62828;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 0 25px;
            }
            QPushButton:hover {
                background-color: #b71c1c;
            }
            QPushButton:disabled {
                background-color: #cfd8dc;
                color:  #90a4ae;
            }
        """)
        self.btn_papelera.clicked.connect(self.enviar_a_papelera)
        fila1_layout.addWidget(self.btn_papelera)

        self.btn_reparacion = QPushButton("🔧 Enviar a Reparación")
        self.btn_reparacion.setEnabled(False)
        self.btn_reparacion.setFont(QFont("Arial", 11, QFont.Weight. Bold))
        self.btn_reparacion.setFixedHeight(45)
        self.btn_reparacion.setCursor(Qt.CursorShape. PointingHandCursor)
        self.btn_reparacion.setStyleSheet("""
            QPushButton {
                background-color: #f57c00;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 0 25px;
            }
            QPushButton:hover {
                background-color: #e65100;
            }
            QPushButton:disabled {
                background-color: #cfd8dc;
                color: #90a4ae;
            }
        """)
        self.btn_reparacion.clicked.connect(self. enviar_a_reparacion)
        fila1_layout.addWidget(self.btn_reparacion)

        # Agregar filas al layout principal
        botones_main.addLayout(fila1_layout)


        return botones_main

    def renderizar_tabla(self):
        """Carga los datos actualmente en self.datos_filtrados en la tabla."""
        t0 = time.time()
        # Se crean UNA sola vez, no en cada celda.
        fuente = QFont("Arial", 10)
        color_texto = QBrush(QColor("black"))

        self.tabla.setUpdatesEnabled(False)
        self.tabla.setSortingEnabled(False)

        try:
            self.tabla.setRowCount(0)
            self.tabla.setRowCount(len(self.datos_filtrados))

            campos = ["tipo", "marca", "modelo_equipo", "numero_serie", "escala",
                 "sector", "estado", "potencia", "nombre_plantilla", "ult_observacion"]

            for fila, equipo in enumerate(self.datos_filtrados):
                for col, campo in enumerate(campos):
                    item = QTableWidgetItem(str(equipo.get(campo, "")))
                    item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                    item.setFont(fuente)          # reusa el mismo objeto
                    item.setForeground(color_texto)  # reusa el mismo objeto
                    self.tabla.setItem(fila, col, item)

        except Exception as e:
            print(f"ERROR en renderizar_tabla: {e}")

        finally:
            self.tabla.setSortingEnabled(True)
            self.tabla.setUpdatesEnabled(True)
                
    def obtener_datos_iniciales(self):
        """Obtiene TODOS los datos de la API una sola vez al inicio."""
        self._actualizando = True  # ← Bloquear
        try:
            # El token se adjunta solo y la URL base la conoce el cliente.
            self.datos_completos = self.api.get("consultaInventario.php")

            self.datos_filtrados = self.datos_completos.copy()
            self.datos_excel = self.datos_completos.copy()

        except SesionExpirada:
            # Este método corre dentro del __init__, cuando la ventana
            # principal todavía no existe. Por eso avisamos acá en vez
            # de delegar en self.window().
            QMessageBox.warning(self, "Sesión expirada",
                                "Tu sesión venció. Cerrá y volvé a iniciar sesión.")
            self.datos_completos = []
            self.datos_filtrados = []
            self.datos_excel = []

        except ApiError as e:
            QMessageBox.warning(self, "Error",
                                f"No se pudieron cargar los datos del inventario:\n{e}")
            self.datos_completos = []
            self.datos_filtrados = []
            self.datos_excel = []

        finally:
            # En un finally: si algo inesperado falla, el flag no queda
            # trabado en True y la pestaña sigue usable.
            self.renderizar_tabla()
            self._actualizando = False  # ← Desbloquear
        
    def aplicar_filtros(self):
        """Aplica los filtros seleccionados"""
        if self._actualizando:  # ← Agregar esta verificación
            return
        # 1. EMPEZAR SIEMPRE DESDE LA LISTA COMPLETA
        self.datos_filtrados = self.datos_completos.copy()

        # 2. Filtro por búsqueda
        texto_busqueda = self.input_buscar.text().strip().upper()
        if texto_busqueda:
            self.datos_filtrados = [
                e for e in self.datos_filtrados
                if texto_busqueda in e.get('numero_serie', '').upper()
            ]

        # 3. Filtros por combos
        filtros = {
            'tipo': self.combo_filtro_tipo.currentText(),
            'marca': self.combo_filtro_marca.currentText(),
            'modelo_equipo': self.combo_filtro_modelo.currentText(),
            'escala': self.combo_filtro_escala.currentText(),
            'sector': self.combo_filtro_sector.currentText(),
            'estado': self.combo_filtro_estado.currentText()
        }
        valores_sin_filtro = {
        "Todos",
        "Primero seleccione el tipo",
        "Primero seleccione marca",
        "Sin modelos para esta marca y tipo",
        }

        for campo, valor in filtros.items():
            if valor not in valores_sin_filtro:
                self.datos_filtrados = [
                    e for e in self.datos_filtrados
                    if e.get(campo, '') == valor
                    ]

        self.renderizar_tabla()

    def limpiar_filtros(self):
        """Limpia todos los filtros"""
        self.input_buscar.clear()
        self.combo_filtro_tipo.setCurrentIndex(0)
        self.combo_filtro_marca.setCurrentIndex(0)
        self.combo_filtro_modelo.setCurrentIndex(0)
        self.combo_filtro_escala.setCurrentIndex(0)
        self.combo_filtro_sector.setCurrentIndex(0)
        self.combo_filtro_estado.setCurrentIndex(0)
        self.datos_filtrados = self.datos_completos.copy()
        #self.renderizar_tabla()

    def on_seleccion_cambiada(self):
        """Maneja el cambio de selección en la tabla"""
        hay_seleccion = len(self.tabla.selectedItems()) > 0
        self.btn_editar.setEnabled(hay_seleccion)
        self.btn_historial.setEnabled(hay_seleccion)
        self.btn_papelera.setEnabled(hay_seleccion)
        self.btn_reparacion.setEnabled(hay_seleccion)

    def get_equipo_seleccionado(self):
        """Retorna el equipo seleccionado"""
        fila = self.tabla.currentRow()
        if fila >= 0 and fila < len(self.datos_filtrados):
            return self.datos_filtrados[fila]
        return None

    def editar_item(self):
        fila_actual = self.tabla.currentRow()
        if fila_actual == -1:
            return

        datos_equipo = []
        for columna in range(self.tabla.columnCount()):
            item = self.tabla.item(fila_actual, columna)
            datos_equipo.append(item.text() if item else "")

        datos_para_modal = datos_equipo[0:]
        frec = self.cargar_datos_programacion(datos_equipo[3])

        try:
            modal = ModalModiEquipo(self.api, datos_para_modal, frec, self)
            modal.showMaximized()
            resultado = modal.exec()
    
            if resultado:
                self.tabla.clearSelection()
                self.tabla.setCurrentCell(-1, -1)
                self.obtener_datos_iniciales()
        except Exception as e:
            print(f"ERROR: {e}")

    def ver_historial(self):
        """Ver historial del equipo"""
        equipo = self.get_equipo_seleccionado()
        if not equipo:
            QMessageBox.warning(self, "Aviso", "Debe seleccionar un equipo.")
            return

        id_equipo = equipo.get("id_equipo", "")

        try:
            historial = self.api.get("historialEquipo.php", {"id_equipo": id_equipo})

            # historial YA es la lista de registros. Si la petición hubiera
            # fallado, habría saltado una excepción antes de esta línea.
            if historial:
                df_historial = pd.DataFrame(historial)
                dialogo = DialogoHistorial(df_historial, equipo, self)
                dialogo.showMaximized()
                dialogo.exec()
            else:
                QMessageBox.information(self, "Info", "No hay historial para este equipo.")

        except SesionExpirada:
            QMessageBox.warning(self, "Sesión expirada",
                                "Tu sesión venció. Cerrá y volvé a iniciar sesión.")
        except ApiError as e:
            QMessageBox.critical(self, "Error", f"No se pudo cargar el historial:\n{e}")

    def generar_excel(self):
        
        datos_a_excel = self.datos_filtrados
        df1 = pd.DataFrame(datos_a_excel)
        
        """Genera reporte Excel"""
        archivo, _ = QFileDialog.getSaveFileName(
            self,
            "Guardar Reporte Excel",
            f"invent",
            "Archivos Excel (*.xlsx)"
        )

        if archivo:
            df1.to_excel(archivo, index=False)
            wb = load_workbook(archivo)
            ws=wb.active
            for col in ws.columns:
                max_length = 0
                column = col[0].column_letter
                for cell in col:
                    try:
                        if len(str(cell.value)) > max_length:
                            max_length = len(str(cell.value))
                    except:
                        pass
                adjusted_width = (max_length + 3)
                ws.column_dimensions[column].width = adjusted_width
            
            wb.save(archivo)
            QMessageBox.information(self, "Excel Generado",
                                    f"Reporte generado correctamente:\n\n{archivo}")

    def enviar_a_papelera(self):
        """Envía el equipo a la papelera"""
        equipo = self.get_equipo_seleccionado()
        if not equipo:
            QMessageBox.warning(self, "Aviso", "Debe seleccionar un equipo.")
            return

        id_equipo    = equipo.get("id_equipo", "")
        numero_serie = equipo.get("numero_serie", "")
        marca        = equipo.get("marca", "")
        modelo       = equipo.get("modelo_equipo", "")

        confirmar = QMessageBox.question(
            self, "Confirmar",
            f"¿Enviar a papelera el equipo?\n\nN° Serie: {numero_serie} {marca} {modelo}",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if confirmar != QMessageBox.StandardButton.Yes:
            return

        dialogo = DialogoMotivoPapelera(numero_serie=numero_serie, parent=self)
        if dialogo.exec() != QDialog.DialogCode.Accepted:
            return

        motivo = dialogo.get_motivo()
        try:
            self.api.post("enviar_papelera.php", {
                "id_equipo": id_equipo,
                "motivo": motivo,
                "numero_serie": numero_serie,
            })

            QMessageBox.information(
                self, "Enviado",
                f"Equipo {numero_serie} enviado a papelera correctamente.")

            self.obtener_datos_iniciales()
            if self.papelera_tab:
                self.papelera_tab.obtener_datos_iniciales()

        except SesionExpirada:
            QMessageBox.warning(self, "Sesión expirada",
                                "Tu sesión venció. Cerrá y volvé a iniciar sesión.")
        except ApiError as e:
            QMessageBox.critical(self, "Error", f"No se pudo enviar a la papelera:\n{e}")
                    

    def enviar_a_reparacion(self):
        """Envía el equipo a reparación"""
        equipo = self.get_equipo_seleccionado()
        id_equipo = equipo.get("id_equipo", "")
        numero_serie = equipo.get("numero_serie", "")
        marca = equipo.get("marca", "")
        modelo = equipo.get("modelo_equipo", "")
        equipo_modal = {
            "id_equipo": id_equipo,
            "numero_serie": numero_serie
        }
        if equipo:
            self.obtener_datos_iniciales()
            respuesta = QMessageBox.question(
                self,
                "Confirmar",
                f"¿Enviar a taller el equipo?\n\nN° Serie: {numero_serie} {marca} {modelo}",
                QMessageBox. StandardButton.Yes | QMessageBox.StandardButton.No
            )
            if respuesta == QMessageBox.StandardButton.Yes:
                
                dialogo = DialogEnviarTaller(self.api, equipo_modal, self)
                if dialogo.exec() == QDialog.DialogCode.Accepted:
                    self.obtener_datos_iniciales()  # Refrescar tabla

            
            
            
            
 # ═══════════════════════════════════════════════════════════ Métodos para cargar filtros desde la API ══════════════════════════════════════════════════════════   
            
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
            self.llenar_combo("sectores.php", self.combo_filtro_sector, "sector", incluir_todos=True)
            self.llenar_combo("estados.php", self.combo_filtro_estado, "estado", incluir_todos=True)
            self.llenar_combo("escalas.php", self.combo_filtro_escala, "escala", incluir_todos=True)
            #self.llenar_combo("potencias.php", self.com, "potencia", incluir_todos=True)
    
            self.datos_tipos = self.llenar_combo("tipos.php", self.combo_filtro_tipo, "tipo", incluir_todos=True)
    
            # id_tipo actualmente seleccionado, guardado aparte — NO se vuelve
            # a derivar del índice de otro combo más adelante.
            self.id_tipo_actual = None
            self.datos_marcas = []   # se llena recién cuando el usuario elige un tipo
            # currentIndexChanged, no currentTextChanged: actualizar_marcas espera
            # un número (posición en la lista), no el texto del ítem.
            self.combo_filtro_tipo.currentIndexChanged.connect(self.actualizar_marcas)
            self.combo_filtro_marca.currentIndexChanged.connect(self.actualizar_modelos)
    
            self.combo_filtro_marca.clear()
            self.combo_filtro_marca.addItem("Primero seleccione el tipo")
            self.combo_filtro_modelo.clear()
            self.combo_filtro_modelo.addItem("Primero seleccione marca")
    
    def actualizar_marcas(self, index):
        """Filtra las marcas según el tipo seleccionado."""
        self.combo_filtro_marca.blockSignals(True)
        self.combo_filtro_modelo.blockSignals(True)

        self.combo_filtro_marca.clear()
        self.combo_filtro_modelo.clear()
        self.combo_filtro_modelo.addItem("Primero seleccione marca")

        # El combo tiene "Todos" en la posición 0 (incluir_todos=True), pero
        # self.datos_tipos es la lista cruda de la API, SIN ese ítem. Por eso
    #    el índice real dentro de datos_tipos va corrido en -1.
        indice_real = index - 1

        if indice_real < 0 or indice_real >= len(self.datos_tipos):
            # index == 0 corresponde a "Todos": no hay tipo seleccionado.
            self.combo_filtro_marca.addItem("Primero seleccione el tipo")
            self.id_tipo_actual = None
            self.datos_marcas = []
        else:
            self.id_tipo_actual = self.datos_tipos[indice_real].get("id_tipo")

            self.datos_marcas = self.llenar_combo(
                f"marcas.php?id_tipo={self.id_tipo_actual}",
                self.combo_filtro_marca,
                "marca",
                incluir_todos=True
            )

        self.combo_filtro_marca.blockSignals(False)
        self.combo_filtro_modelo.blockSignals(False)
    
    def actualizar_modelos(self, index):
        """Filtra los modelos según tipo Y marca seleccionados."""
        self.combo_filtro_modelo.clear()

        # Mismo desfasaje: combo_filtro_marca también tiene "Todos" en la
        # posición 0, y self.datos_marcas no lo incluye.
        indice_real = index - 1

        if indice_real < 0 or indice_real >= len(self.datos_marcas) or self.id_tipo_actual is None:
            self.combo_filtro_modelo.addItem("Primero seleccione marca")
            return

        id_marca = self.datos_marcas[indice_real].get("id_marca")

        datos_modelos = self.llenar_combo(
            f"modelos.php?id_marca={id_marca}&id_tipo={self.id_tipo_actual}",
            self.combo_filtro_modelo,
            "modelo_equipo",
            incluir_todos=True
        )

        if not datos_modelos:
            self.combo_filtro_modelo.clear()
            self.combo_filtro_modelo.addItem("Sin modelos para esta marca y tipo")
        
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

    def cargar_datos_programacion(self, numero_serie):
                self.canales_data = []
                """Función para cargar datos de programacion de frecuencias."""
                if not numero_serie:
                    return
                
                try:
                    self.programacion_data = self.api.get("cargar_programacion.php", {"numero_serie": numero_serie})
                    print(f"programacion inventario tab para llenar modi:{self.programacion_data}")
                    return self.programacion_data
                    #self.cargar_datos_existentes()
                except SesionExpirada:
                    QMessageBox.warning(self, "Sesión expirada",
                        "Tu sesión venció. Cerrá y volvé a iniciar sesión.")
                except ApiError as e:
                    QMessageBox.critical(self, "Error", f"No se pudo cargar la programación:\n{e}")



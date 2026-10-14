"""
Pestaña:   Taller
Versión:  4.0 - COMPLETA
Fecha: 2025-12-14
Autor: lucasarsa2015-cpu
Descripción: Gestión de equipos en reparación en talleres AEP y EZE
"""
import requests
import pandas as pd
import direcciones # type: ignore
from base_tab import ApiTab
from api_client import ApiError, SesionExpirada
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QFrame, QComboBox, QTableWidget, QTableWidgetItem,
    QHeaderView, QMessageBox, QAbstractItemView, QDialog,
    QCheckBox, QTextEdit, QScrollArea, QGridLayout, QMenu, QApplication
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont, QColor, QBrush, QAction
from datetime import datetime


# ═══════════════════════════════════════════════════════════
# DIÁLOGO 1: INGRESO A TALLER
# ═══════════════════════════════════════════════════════════

class DialogoIngresoTaller(QDialog):
    """Ventana modal para ingreso de equipo a taller"""
    ingreso_exitoso = pyqtSignal()
    def __init__(self, api, equipo= None, parent=None):
        super().__init__(parent)
        self.serie = equipo.get("serie", "")
        self.setWindowTitle(f"🛠️ Ingreso a Taller {self.serie}")
        self.setModal(True)
        self.setFixedSize(450, 400)
        self.elementos_seleccionados = []
        self.crear_interfaz()
        self.input_detalle.setEnabled(False)
        self.cb_otros.stateChanged.connect(self.actualizar_estado_detalle)
        self.api = api
        
        self.taller = equipo.get("taller", "")
        self.estado = equipo.get("estado_taller", "")
        self.id_equipo = equipo.get("id_equipo", "")
        self.id_recepcion = equipo.get("id_recepcion")
        self.id_estado = equipo.get("id_estado", "")
        self.id_taller = equipo.get("id_taller", "")
        
    def crear_interfaz(self):
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(25, 25, 25, 25)
        main_layout.setSpacing(20)
        
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        
        contenedor = QWidget()
        layout = QVBoxLayout()
        layout.setContentsMargins(25, 25, 25, 25)
        layout.setSpacing(20)

        # N° de SD (opcional)
        lbl_sd = QLabel("N° de SD:")
        lbl_sd.setFont(QFont("Arial", 11, QFont.Weight.Bold))
        lbl_sd.setStyleSheet("color: #1976d2;")
        layout.addWidget(lbl_sd)

        self.input_sd = QLineEdit()
        self.input_sd.setPlaceholderText("Opcional")
        self.input_sd.setFixedHeight(40)
        self.input_sd.setStyleSheet("""
            QLineEdit {
                border: 2px solid #bbdefb;
                border-radius:  6px;
                padding: 8px;
                font-size:  11pt;
                background-color: white;
                color: black;
            }
            QLineEdit:focus {
                border: 2px solid #1976d2;
            }
        """)
        layout.addWidget(self.input_sd)

        # Elementos de ingreso
        lbl_elementos = QLabel("Elementos de ingreso")
        lbl_elementos.setFont(QFont("Arial", 11, QFont.Weight.Bold))
        lbl_elementos. setStyleSheet("color: #37474f;")
        layout.addWidget(lbl_elementos)

        # Frame con checkboxes
        elementos_frame = QFrame()
        elementos_frame.setStyleSheet("""
            QFrame {
                background-color: #f5f5f5;
                border: 2px solid #cfd8dc;
                border-radius: 8px;
                padding: 15px;
            }
        """)

        elementos_layout = QGridLayout()
        elementos_layout.setSpacing(12)

        # Checkboxes
        self.cb_equipo = QCheckBox("Equipo")
        self.cb_antena = QCheckBox("Antena")
        self.cb_cargador = QCheckBox("Cargador")
        self.cb_bateria = QCheckBox("Batería")
        self.cb_fuente = QCheckBox("Fuente")
        self.cb_cables = QCheckBox("Cables")
        self.cb_otros = QCheckBox("Otros")
        checkboxes = [
            self.cb_equipo, self.cb_antena, self.cb_cargador,
            self.cb_bateria, self.cb_fuente, self.cb_cables,
            self.cb_otros
        ]

        for cb in checkboxes:
            cb.setFont(QFont("Arial", 10))
            cb.setStyleSheet("""
                QCheckBox {
                    color: #37474f;
                    spacing: 8px;
                }
                QCheckBox:: indicator {
                    width: 20px;
                    height:  20px;
                    border: 2px solid #78909c;
                    border-radius:  4px;
                    background-color: white;
                }
                QCheckBox::indicator:checked {
                    background-color: #1976d2;
                    border-color: #1976d2;
                    image: none;
                }
            """)

        elementos_layout.addWidget(self.cb_equipo, 0, 0)
        elementos_layout.addWidget(self.cb_antena, 0, 1)
        elementos_layout.addWidget(self.cb_cargador, 1, 0)
        elementos_layout.addWidget(self.cb_bateria, 1, 1)
        elementos_layout.addWidget(self.cb_fuente, 2, 0)
        elementos_layout.addWidget(self.cb_otros, 2, 1)
        elementos_layout.addWidget(self.cb_cables, 3, 0)
        

        elementos_frame.setLayout(elementos_layout)
        layout.addWidget(elementos_frame)

        # Detalle otros
        lbl_detalle = QLabel("Detalle otros:")
        lbl_detalle. setFont(QFont("Arial", 10, QFont.Weight.Bold))
        lbl_detalle.setStyleSheet("color: #1976d2;")
        layout.addWidget(lbl_detalle)

        self.input_detalle = QTextEdit()
        self.input_detalle.setFixedHeight(100)
        self.input_detalle.setStyleSheet("""
            QTextEdit {
                border: 2px solid #bbdefb;
                border-radius: 6px;
                padding: 8px;
                font-size: 10pt;
                background-color:  white;
                color: black;
            }
            QTextEdit:focus {
                border: 2px solid #1976d2;
            }
        """)
        layout.addWidget(self.input_detalle)

        layout.addStretch()

        # Botones
        botones_layout = QHBoxLayout()
        botones_layout.setSpacing(15)

        btn_cancelar = QPushButton("Cancelar")
        btn_cancelar.setFont(QFont("Arial", 11, QFont.Weight.Bold))
        btn_cancelar.setFixedHeight(45)
        btn_cancelar.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_cancelar.setStyleSheet("""
            QPushButton {
                background-color:  #78909c;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 0 30px;
            }
            QPushButton:hover {
                background-color: #607d8b;
            }
        """)
        btn_cancelar.clicked.connect(self.reject)
        botones_layout.addWidget(btn_cancelar)

        btn_guardar = QPushButton("Ingresar equipo")
        btn_guardar.setFont(QFont("Arial", 11, QFont.Weight.Bold))
        btn_guardar.setFixedHeight(45)
        btn_guardar.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_guardar.setStyleSheet("""
            QPushButton {
                background-color: #1976d2;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 0 30px;
            }
            QPushButton:hover {
                background-color: #1565c0;
            }
        """)
        btn_guardar.clicked.connect(self.guardar)
        botones_layout.addWidget(btn_guardar)

        contenedor.setLayout(layout)
        scroll.setWidget(contenedor)

        main_layout.addWidget(scroll)
        main_layout.addLayout(botones_layout)


        self.setLayout(main_layout)

    def guardar(self):
        """Guarda el ingreso a taller"""
        elementos = []
        
        if self.cb_equipo.isChecked():
            elementos.append("componente_equipo")
        if self.cb_antena.isChecked():
            elementos.append("componente_antena")
        if self.cb_cargador.isChecked():
            elementos.append("componente_cargador")
        if self.cb_bateria.isChecked():
            elementos.append("componente_bateria")
        if self.cb_fuente.isChecked():
            elementos.append("componente_fuente")
        if self.cb_cables.isChecked():
            elementos.append("componente_cables")
        if self.cb_otros.isChecked():
            elementos.append("componente_otros")
            

        if not elementos:
            QMessageBox.warning(
                self, "Atención", "Debe seleccionar al menos un elemento.")
            return

        self.elementos_seleccionados = elementos
        try:
            datos = {
                "id_estado": self.id_estado,
                "estado": self.estado,
                "nro_sd": self.input_sd.text().strip(),
                "elementos": self.elementos_seleccionados,
                "detalle_otros": self.input_detalle.toPlainText().strip(),
                "id_equipo": self.id_equipo,
                "id_recepcion": self.id_recepcion,
                "id_taller" : self.id_taller
            }
            
            self.api.post("ingreso_taller.php", datos)

            self.ingreso_exitoso.emit()
            QMessageBox.information(
                    self, "✅ Ingresado", f"El equipo {self.serie} ha sido ingresado correctamente.")
            self.accept()

        except SesionExpirada:
                    QMessageBox.warning(self, "Sesión expirada",
                                        "Tu sesión venció. Cerrá y volvé a iniciar sesión.")
        except ApiError as e:
                    QMessageBox.critical(self, "Error", f"No se pudo realizar el ingreso al taller:\n{e}")
        
        

    def get_datos(self):
        """Retorna los datos del ingreso"""
        return {
            'nro_sd': self.input_sd.text().strip(),
            'elementos': self.elementos_seleccionados,
            'detalle_otros':  self.input_detalle.toPlainText().strip(),
        }
        
    def actualizar_estado_detalle(self):
        self.input_detalle.setEnabled(self.cb_otros.isChecked())
    
        if not self.cb_otros.isChecked():
            self.input_detalle.clear()
        


# ═══════════════════════════════════════════════════════════
# DIÁLOGO 2: VER HISTORIAL
# ═══════════════════════════════════════════════════════════

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


# ═══════════════════════════════════════════════════════════
# DIÁLOGO 3: EGRESO DE TALLER
# ═══════════════════════════════════════════════════════════

class DialogoEgresoTaller(QDialog):
    def __init__(self, api, equipo_data, parent=None): #stock_service
        super().__init__(parent)
        self.api = api
        self.equipo_data = equipo_data     # dict con tipo, marca, modelo_equipo, serie, id_modelo, taller, estado
        #self.stock = stock_service
        self.movimientos = None
        self.otro_repuesto = ""
        self.tareas = []
        self.repuestos_cb = []             # [(id_repuesto, nombre, checkbox), ...]
        self.setWindowTitle("✅ Egreso de Taller")
        self.setModal(True)
        self.setFixedSize(580, 760)
        self.crear_interfaz()
        self.input_otro_repuesto.setEnabled(False)
        self.input_detalle_tareas.setEnabled(False)
        self.cb_otros_tareas.stateChanged.connect(
            lambda: self.actualizar_estado_detalle(self.cb_otros_tareas, self.input_detalle_tareas))
        self.cb_otro_rep.stateChanged.connect(
            lambda: self.actualizar_estado_detalle(self.cb_otro_rep, self.input_otro_repuesto))

    def crear_interfaz(self):
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        contenedor = QWidget()
        layout = QVBoxLayout()
        layout.setContentsMargins(25, 25, 25, 25)
        layout.setSpacing(16)

        estilo_lbl_sec = "color: #37474f; font-weight: bold;"
        estilo_input = ("QLineEdit { border: 2px solid #bbdefb; border-radius: 6px; padding: 8px;"
                        " font-size: 10pt; background: white; color: black; }"
                        "QLineEdit:disabled { background: #e0e0e0; color: #9e9e9e; }"
                        "QLineEdit:focus { border: 2px solid #1976d2; }")
        estilo_cb = ("QCheckBox { color: #263238; font-size: 10pt; spacing: 8px; }"
                     "QCheckBox::indicator { width: 18px; height: 18px; border: 2px solid #90a4ae;"
                     " border-radius: 3px; background: white; }"
                     "QCheckBox::indicator:hover { border: 2px solid #1976d2; }"
                     "QCheckBox::indicator:checked { background: #1976d2; border: 2px solid #1976d2; }")

        # ── Datos del equipo ──
        datos_frame = QFrame()
        datos_frame.setStyleSheet("QFrame { background: #e8f5e9; border: 2px solid #4caf50;"
                                  " border-radius: 8px; }")
        dlay = QVBoxLayout(datos_frame)
        dlay.setContentsMargins(15, 12, 15, 12)
        td = QLabel("Datos del equipo")
        td.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        td.setStyleSheet("color: #2e7d32; border: none;")
        dlay.addWidget(td)
        d = self.equipo_data
        info = QLabel(
            f"<b>Tipo:</b> {d.get('tipo','N/A')}<br>"
            f"<b>Marca:</b> {d.get('marca','N/A')}<br>"
            f"<b>Modelo:</b> {d.get('modelo_equipo','N/A')}<br>"
            f"<b>N° de Serie:</b> {d.get('serie','N/A')}<br>"
            f"<b>Taller:</b> {d.get('taller','N/A')}   ·   "
            f"<b>Estado actual:</b> {d.get('estado','En taller')}")
        info.setStyleSheet("color: #2e7d32; border: none;")
        info.setWordWrap(True)
        dlay.addWidget(info)
        layout.addWidget(datos_frame)

        # ── Número guía ──
        lg = QLabel("Número guía (opcional):")
        lg.setStyleSheet(estilo_lbl_sec)
        layout.addWidget(lg)
        self.input_guia = QLineEdit()
        self.input_guia.setMaximumHeight(35)
        self.input_guia.setStyleSheet(estilo_input)
        layout.addWidget(self.input_guia)

        # ── Número SD ──
        ls = QLabel("N° de SD:")
        ls.setStyleSheet(estilo_lbl_sec)
        layout.addWidget(ls)
        self.input_sd = QLineEdit()
        self.input_sd.setMaximumHeight(35)
        self.input_sd.setStyleSheet(estilo_input)
        layout.addWidget(self.input_sd)

        # ── Tareas realizadas ──
        lt = QLabel("Tareas realizadas")
        lt.setFont(QFont("Arial", 11, QFont.Weight.Bold))
        lt.setStyleSheet(estilo_lbl_sec)
        layout.addWidget(lt)
        tareas_frame = QFrame()
        tareas_frame.setStyleSheet("QFrame { background: #f5f5f5; border: 2px solid #cfd8dc;"
                                   " border-radius: 8px; }")
        tlay = QGridLayout(tareas_frame)
        tlay.setContentsMargins(15, 12, 15, 12)
        tlay.setSpacing(10)
        self.cb_soldadura = QCheckBox("Soldadura SMD")
        self.cb_verificacion = QCheckBox("Verificación RF")
        self.cb_reprogramacion = QCheckBox("Reprogramación")
        self.cb_otros_tareas = QCheckBox("Otros")
        for cb in (self.cb_soldadura, self.cb_verificacion, self.cb_reprogramacion, self.cb_otros_tareas):
            cb.setStyleSheet(estilo_cb)
        tlay.addWidget(self.cb_soldadura, 0, 0)
        tlay.addWidget(self.cb_verificacion, 0, 1)
        tlay.addWidget(self.cb_reprogramacion, 1, 0)
        tlay.addWidget(self.cb_otros_tareas, 1, 1)
        layout.addWidget(tareas_frame)
        self.input_detalle_tareas = QLineEdit()
        self.input_detalle_tareas.setPlaceholderText("Detalle de otras tareas...")
        self.input_detalle_tareas.setStyleSheet(estilo_input)
        layout.addWidget(self.input_detalle_tareas)

        # ── Repuestos utilizados (DINÁMICO por modelo) ──
        lr = QLabel("Repuestos utilizados")
        lr.setFont(QFont("Arial", 11, QFont.Weight.Bold))
        lr.setStyleSheet(estilo_lbl_sec)
        layout.addWidget(lr)

        sub = QLabel(f"(los que corresponden al modelo {d.get('modelo_equipo','')}, desde Stock)")
        sub.setStyleSheet("color: #607d8b; font-style: italic; font-size: 9pt;")
        layout.addWidget(sub)

        repuestos_frame = QFrame()
        repuestos_frame.setStyleSheet("QFrame { background: #f5f5f5; border: 2px solid #cfd8dc;"
                                      " border-radius: 8px; }")
        rlay = QGridLayout(repuestos_frame)
        rlay.setContentsMargins(15, 12, 15, 12)
        rlay.setSpacing(10)

        vinculados = self.stock.repuestos_de_modelo(d.get("id_modelo"))
        fila = col = 0
        for rep in vinculados:
            cb = QCheckBox(rep["nombre"].capitalize())
            cb.setStyleSheet(estilo_cb)
            rlay.addWidget(cb, fila, col)
            self.repuestos_cb.append((rep["id_repuesto"], rep["nombre"], cb))
            col += 1
            if col == 2:
                col = 0
                fila += 1
        if not vinculados:
            vac = QLabel("Este modelo no tiene repuestos vinculados en Stock.")
            vac.setStyleSheet("color: #90a4ae; font-style: italic; border: none;")
            rlay.addWidget(vac, 0, 0, 1, 2)
            fila = 1
        # "Otro" al final, ocupando las dos columnas
        self.cb_otro_rep = QCheckBox("Otro")
        self.cb_otro_rep.setStyleSheet(estilo_cb)
        rlay.addWidget(self.cb_otro_rep, fila, 0, 1, 2)
        layout.addWidget(repuestos_frame)

        # Detalle "Otro" repuesto
        self.input_otro_repuesto = QLineEdit()
        self.input_otro_repuesto.setPlaceholderText("Detalle de 'Otro' (no descuenta stock)...")
        self.input_otro_repuesto.setStyleSheet(estilo_input)
        layout.addWidget(self.input_otro_repuesto)

        layout.addStretch()
        contenedor.setLayout(layout)
        scroll.setWidget(contenedor)
        main_layout.addWidget(scroll)

        # ── Botones ──
        botones = QHBoxLayout()
        botones.setContentsMargins(25, 12, 25, 16)
        botones.setSpacing(15)
        btn_cancelar = QPushButton("Cancelar")
        btn_cancelar.setFont(QFont("Arial", 11, QFont.Weight.Bold))
        btn_cancelar.setFixedHeight(45)
        btn_cancelar.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_cancelar.setStyleSheet("QPushButton { background: #78909c; color: white; border: none;"
                                   " border-radius: 6px; padding: 0 30px; }"
                                   "QPushButton:hover { background: #607d8b; }")
        btn_cancelar.clicked.connect(self.reject)
        botones.addWidget(btn_cancelar)
        btn_guardar = QPushButton("Guardar egreso")
        btn_guardar.setFont(QFont("Arial", 11, QFont.Weight.Bold))
        btn_guardar.setFixedHeight(45)
        btn_guardar.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_guardar.setStyleSheet("QPushButton { background: #1976d2; color: white; border: none;"
                                  " border-radius: 6px; padding: 0 30px; }"
                                  "QPushButton:hover { background: #1565c0; }")
        btn_guardar.clicked.connect(self.guardar)
        botones.addWidget(btn_guardar)
        main_layout.addLayout(botones)

        self.setLayout(main_layout)

    def actualizar_estado_detalle(self, cb, campo):
        campo.setEnabled(cb.isChecked())
        if not cb.isChecked():
            campo.clear()

    def guardar(self):
        """Igual que el egreso de siempre, pero los repuestos son los del modelo
        y al guardar impactan el stock."""
        taller = self.equipo_data.get("taller")

        # Repuestos catalogados tildados (afectan stock) + "Otro" (texto, no toca stock)
        marcados = [(id_r, nombre) for id_r, nombre, cb in self.repuestos_cb if cb.isChecked()]
        otro = self.input_otro_repuesto.text().strip() if self.cb_otro_rep.isChecked() else ""

        if not marcados and not otro:
            QMessageBox.warning(self, "Atención", "Debe seleccionar al menos un repuesto.")
            return
        if self.cb_otro_rep.isChecked() and not otro:
            QMessageBox.warning(self, "Atención", "Marcó 'Otro' pero no escribió el detalle.")
            return

        # Tareas (igual que siempre)
        tareas = []
        if self.cb_soldadura.isChecked():
            tareas.append("Soldadura SMD")
        if self.cb_verificacion.isChecked():
            tareas.append("Verificación RF")
        if self.cb_reprogramacion.isChecked():
            tareas.append("Reprogramación")
        if self.cb_otros_tareas.isChecked():
            det = self.input_detalle_tareas.text().strip()
            if not det:
                QMessageBox.warning(self, "Atención", "Marcó 'Otros' en tareas pero no escribió el detalle.")
                return
            tareas.append(f"Otros: {det}")
        if not tareas:
            QMessageBox.warning(self, "Atención", "Debe seleccionar al menos una tarea.")
            return

        # Validar stock del taller
        sin_stock = [n for id_r, n in marcados if self.stock.stock_taller(id_r, taller) <= 0]
        if sin_stock:
            QMessageBox.warning(self, "⚠️ Sin stock",
                                f"No hay stock en {taller} de: {', '.join(sin_stock)}.\n"
                                "Registrá un ingreso o desmarcá esos repuestos.")
            return

        # Con backend: self.api.post("egreso_taller.php", {
        #     "id_equipo": d['id_equipo'], "id_taller": <id>,
        #     "repuestos": [id for id, _ in marcados],   # cada uno cantidad 1
        #     "detalle_otros": otro, "elementos_tareas": tareas, ...})
        # y el PHP, en una transacción: -stock, +en_uso, +fuera_servicio por repuesto.
        self.movimientos = self.stock.aplicar_egreso([id_r for id_r, _ in marcados], taller)
        self.otro_repuesto = otro
        self.tareas = tareas
        self.taller_usado = taller
        self.accept()



# ═══════════════════════════════════════════════════════════
# DIÁLOGO 4 : ACTUALIZAR ESTADO DE REPARACIÓN
# ═══════════════════════════════════════════════════════════
class DialogoActualizarEstado(QDialog):

    def __init__(self, equipo_data, parent=None):
        super().__init__(parent)
        self.equipo_data = equipo_data
        self.setWindowTitle("Modificar estado de equipo")
        self.setModal(True)
        self.API_BASE_URL = direcciones.URL.API_BASE_URL  # URL base de la API
        #self.setFixedSize(450, 400)
        self.crear_interfaz()
        self.llenar_desplegables()
        self.cargar_valor_combo([self.equipo_data.get('estado_taller', 'N/A')])

    def crear_interfaz(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(25, 25, 25, 25)
        layout.setSpacing(20)

        # Detalle del equipo
        detalle_frame = QFrame()
        detalle_frame.setStyleSheet("""
            QFrame {
                background-color: #e3f2fd;
                border:  2px solid #1976d2;
                border-radius: 8px;
                padding: 15px;
            }
        """)

        detalle_layout = QVBoxLayout()
        detalle_layout.setSpacing(8)

        titulo_detalle = QLabel("Detalle")
        titulo_detalle.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        titulo_detalle. setStyleSheet("color: #0d47a1;")
        detalle_layout.addWidget(titulo_detalle)

        info_html = f"""
        <p style='margin: 5px 0; color: #1976d2;'><b>N° de Orden:</b> {self.equipo_data. get('orden', 'N/A')}</p>
        <p style='margin: 5px 0; color: #1976d2;'><b>Tipo de equipo:</b> {self.equipo_data.get('tipo', 'N/A')}</p>
        <p style='margin: 5px 0; color: #1976d2;'><b>Marca:</b> {self.equipo_data.get('marca', 'N/A')}</p>
        <p style='margin: 5px 0; color:  #1976d2;'><b>Modelo:</b> {self.equipo_data.get('modelo_equipo', 'N/A')}</p>
        <p style='margin: 5px 0; color: #1976d2;'><b>N° de Serie:</b> {self.equipo_data.get('serie', 'N/A')}</p>
        <p style='margin: 5px 0; color:  #1976d2;'><b>Estado actual:</b> {self.equipo_data.get('estado_taller', 'N/A')}</p>
        """
        lbl_info = QLabel(info_html)
        lbl_info.setFont(QFont("Arial", 10))
        lbl_info.setWordWrap(True)
        detalle_layout.addWidget(lbl_info)

        detalle_frame.setLayout(detalle_layout)
        layout.addWidget(detalle_frame)

        layout.addWidget(QLabel("Cambiar estado a:"))
        self.combo_estado = QComboBox()
        self.combo_estado.setEditable(True)
        self.combo_estado.setCurrentText(self.equipo_data.get('estado_taller', 'N/A'))
        layout.addWidget(self.combo_estado)

        # Botón cerrar
        btn_cerrar = QPushButton("Cerrar")
        btn_cerrar.setFont(QFont("Arial", 11, QFont.Weight.Bold))
        btn_cerrar. setFixedHeight(45)
        btn_cerrar.setCursor(Qt.CursorShape. PointingHandCursor)
        btn_cerrar.setStyleSheet("""
            QPushButton {
                background-color: #1976d2;
                color:  white;
                border: none;
                border-radius: 6px;
                padding: 0 40px;
            }
            QPushButton:hover {
                background-color: #1565c0;
            }
        """)
        btn_cerrar.clicked.connect(self.accept)
        
        # Botón Actualizar
        btn_udpate = QPushButton("Actualizar")
        btn_udpate.setFont(QFont("Arial", 11, QFont.Weight.Bold))
        btn_udpate.setFixedHeight(45)
        btn_udpate.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_udpate.setStyleSheet("""
            QPushButton {
                background-color: #1976d2;
                color:  white;
                border: none;
                border-radius: 6px;
                padding: 0 40px;
            }
            QPushButton:hover {
                background-color: #1565c0;
            }
        """)
        btn_udpate.clicked.connect(self.actualizar_estado)

        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        btn_layout.addWidget(btn_cerrar)
        btn_layout.addWidget(btn_udpate)
        btn_layout.addStretch()

        layout.addLayout(btn_layout)
        self.adjustSize()

        self.setLayout(layout)
        
    def llenar_combo(self, endpoint, combo, campo_json, incluir_todos=False, incluir_escriba=False):
        """
        api_url: URL base (ej. http://api.com)
        endpoint: Archivo PHP (ej. marcas.php)
        combo: El objeto QComboBox
        campo_json: El nombre de la clave en el JSON (ej. 'marca')
        incluir_todos: Si agrega el item "Todos"
        """
        api_url = direcciones.URL.API_BASE_URL
        data = []
    
        try:
            response = requests.get(f"{api_url}/{endpoint}")
            response.raise_for_status()
            data = response.json()
        
            # Extraemos la lista de valores
            items = [str(obj[campo_json]) for obj in data]
        
            combo.clear()
            if incluir_todos:
                combo.addItem("Todos")
            elif incluir_escriba:
                combo.addItem("Escriba o seleccione")
        
            combo.addItems(items)
        
        except requests.exceptions.HTTPError as errh:
            print(f"Error HTTP: {response.status_code}. Detalle: {errh}")
            print(f"Respuesta del servidor: {response.text}")
        except requests.exceptions.RequestException as e:
            print(f"Error de conexión: {e}")
        except KeyError as e:
            print(f"Campo '{campo_json}' no encontrado en el JSON: {e}")
        except Exception as e:
            print(f"Error inesperado: {e}")
    
        return data
    
    def llenar_desplegables(self):
        """Llena todos los combos de la pestaña"""
        self.llenar_combo("estados_taller.php", self.combo_estado, "estado", incluir_todos= False)
        
    def cargar_valor_combo(self, datos):

        widgets = [self.combo_estado]
    
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
                
    def actualizar_estado(self):
        payload = {
            "id" : self.equipo_data.get("id_estado", ""),
            "id_equipo" : self.equipo_data.get("id_equipo", ""),
            "estado" : self.combo_estado.currentText().strip()
        }  
        serie = self.equipo_data.get("serie", "")
        print(payload)
        
        try:
            response = requests.post(
                f"{self.API_BASE_URL}/actualizar_estado.php",
                data= payload
            )
            resultado = response.json()
            print(resultado)
            if resultado.get("success") and response.status_code == 200:
                QMessageBox.information(
                    self, "✅ Estado actualizado", f"El estado del equipo {serie} se actualizó correctamente.")
                self.accept()
            else:
                QMessageBox.warning(self, "Error", f"Error al ingresar equipo: {resultado.get('message')}")
                self.accept()
        except Exception as e:
                    QMessageBox.critical(self, "Error de Conexión", f"No se pudo conectar con la API: {str(e)}")


class DialogoTextoAutomatico(QDialog):
    """Ventana modal para ver el texto automático generado para correo"""

    def __init__(self, texto_automatico, parent=None):
        super().__init__(parent)
        self.setModal(True)
        self.setWindowTitle("Texto automático para correo")
        self.API_BASE_URL = direcciones.URL.API_BASE_URL  # URL base de la API
        #self.setFixedSize(450, 400)
        self.texto_automatico = texto_automatico
        self.crear_interfaz()

    def crear_interfaz(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(25, 25, 25, 25)
        layout.setSpacing(20)

        # Detalle del equipo
        detalle_frame = QFrame()
        detalle_frame.setStyleSheet("""
            QFrame {
                background-color: #e3f2fd;
                border:  2px solid #1976d2;
                border-radius: 8px;
                padding: 15px;
            }
        """)

        detalle_layout = QVBoxLayout()
        detalle_layout.setSpacing(8)

        titulo_detalle = QLabel("Texto automático generado para correo")
        titulo_detalle.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        titulo_detalle.setStyleSheet("color: #0d47a1;")
        detalle_layout.addWidget(titulo_detalle)

        texto_correo = f""" {self.texto_automatico}"""
        lbl_info = QLabel(texto_correo)
        lbl_info.setFont(QFont("Arial", 10))
        lbl_info.setStyleSheet("color: black;")
        lbl_info.setWordWrap(True)
        detalle_layout.addWidget(lbl_info)

        detalle_frame.setLayout(detalle_layout)
        layout.addWidget(detalle_frame)

        # Botón cerrar
        btn_cerrar = QPushButton("Cerrar")
        btn_cerrar.setFont(QFont("Arial", 11, QFont.Weight.Bold))
        btn_cerrar. setFixedHeight(45)
        btn_cerrar.setCursor(Qt.CursorShape. PointingHandCursor)
        btn_cerrar.setStyleSheet("""
            QPushButton {
                background-color: #1976d2;
                color:  white;
                border: none;
                border-radius: 6px;
                padding: 0 40px;
            }
            QPushButton:hover {
                background-color: #1565c0;
            }
        """)
        btn_cerrar.clicked.connect(self.accept)
        
        # Botón Actualizar
        btn_copiar = QPushButton("Copiar texto")
        btn_copiar.setFont(QFont("Arial", 11, QFont.Weight.Bold))
        btn_copiar.setFixedHeight(45)
        btn_copiar.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_copiar.setStyleSheet("""
            QPushButton {
                background-color: #1976d2;
                color:  white;
                border: none;
                border-radius: 6px;
                padding: 0 40px;
            }
            QPushButton:hover {
                background-color: #1565c0;
            }
        """)
        btn_copiar.clicked.connect(self.copiar_texto)

        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        btn_layout.addWidget(btn_cerrar)
        btn_layout.addWidget(btn_copiar)
        btn_layout.addStretch()

        layout.addLayout(btn_layout)
        self.adjustSize()

        self.setLayout(layout)
        
    def copiar_texto(self):
        clipboard = QApplication.clipboard()
        clipboard.setText(self.texto_automatico)
        QMessageBox.information(self, "Copiado", "El texto se ha copiado al portapapeles.")
            
            
# ═══════════════════════════════════════════════════════════
# PESTAÑA PRINCIPAL:  TALLER
# ═══════════════════════════════════════════════════════════

class TallerTab(ApiTab):
    """Pestaña de gestión de taller"""

    def __init__(self, api):
        super().__init__(api)
        self.api = api
        self.datos_completos = []  # SIN datos precargados
        self.datos_filtrados = []
        self.crear_interfaz()
        self.API_BASE_URL = direcciones.URL.API_BASE_URL  # URL base de la API
        self.obtener_datos()
        self.llenar_desplegables()
        
    def crear_interfaz(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(15)

        # Header
        header = QLabel("🛠️ TALLER")
        header.setFont(QFont("Arial", 20, QFont.Weight.Bold))
        header.setAlignment(Qt.AlignmentFlag. AlignCenter)
        header.setFixedHeight(60)
        header.setStyleSheet("""
            QLabel {
                background:  qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #1565c0, stop:1 #1976d2);
                color: white;
                padding: 15px;
                border-radius:  10px;
                border: 3px solid #0d47a1;
            }
        """)
        layout.addWidget(header)

        # Barra de búsqueda
        busqueda_layout = QHBoxLayout()
        busqueda_layout.setSpacing(10)

        lbl_buscar = QLabel("🔍 Buscar:")
        lbl_buscar.setFont(QFont("Arial", 11, QFont.Weight.Bold))
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
        btn_limpiar. setFixedHeight(38)
        btn_limpiar.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_limpiar. setStyleSheet("""
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
        btn_limpiar. clicked.connect(self.limpiar_filtros)
        busqueda_layout.addWidget(btn_limpiar)

        busqueda_layout.addStretch()

        layout.addLayout(busqueda_layout)

        # Filtros
        filtros_layout = QHBoxLayout()
        filtros_layout.setSpacing(10)

        lbl_filtros = QLabel("Filtros:")
        lbl_filtros.setFont(QFont("Arial", 11, QFont.Weight.Bold))
        lbl_filtros.setStyleSheet("color: black;")
        filtros_layout.addWidget(lbl_filtros)

        estilo_combo = """
            QComboBox {
            border: 2px solid #cfd8dc;
            border-radius: 6px;
            padding: 6px 10px;
            background-color: white;
            min-width: 150px;
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
        
        estilo_label = "color: black; font-weight: bold;"

        lbl_taller = QLabel("Taller:")
        lbl_taller.setStyleSheet(estilo_label)
        filtros_layout.addWidget(lbl_taller)
        self.combo_filtro_taller = QComboBox()
        self.combo_filtro_taller.setFixedHeight(35)
        self.combo_filtro_taller.setStyleSheet(estilo_combo)
        self.combo_filtro_taller.currentTextChanged.connect(
            lambda: self.aplicar_filtros())
        filtros_layout. addWidget(self.combo_filtro_taller)

        lbl_estado = QLabel("Estado:")
        lbl_estado.setStyleSheet(estilo_label)
        filtros_layout.addWidget(lbl_estado)
        self.combo_filtro_estado = QComboBox()
        self.combo_filtro_estado.setFixedHeight(35)
        self.combo_filtro_estado.setStyleSheet(estilo_combo)
        self.combo_filtro_estado.currentTextChanged.connect(
            lambda: self.aplicar_filtros())
        filtros_layout.addWidget(self.combo_filtro_estado)

        filtros_layout.addStretch()

        layout. addLayout(filtros_layout)

        # Tabla
        self.crear_tabla()
        layout.addWidget(self.tabla, 1)

        # Botones inferiores
        botones_layout = self.crear_botones()
        layout.addLayout(botones_layout)

        self.setLayout(layout)

        self.cargar_tabla()

    def crear_tabla(self):
        """Crea la tabla de equipos en taller"""
        self.tabla = QTableWidget()
        self.tabla.setColumnCount(11)
        self.tabla.hideColumn(0)
        self.tabla.setHorizontalHeaderLabels([
            "N° Orden",
            "Tipo",
            "Marca",
            "Modelo",
            "N° Serie",
            "Taller",
            "Fecha Recepción",
            "Fecha Ingreso",
            "Días",
            "Estado",
            "Observaciones"
        ])
        
        self.tabla.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.tabla.customContextMenuRequested.connect(
            lambda pos: self.mostrar_menu_contextual(self.tabla, pos))

        self.tabla.setEditTriggers(
            QAbstractItemView.EditTrigger.NoEditTriggers)
        self.tabla.setSelectionBehavior(
            QAbstractItemView.SelectionBehavior.SelectRows)
        self.tabla.setSelectionMode(
            QAbstractItemView. SelectionMode.SingleSelection)
        self.tabla.setAlternatingRowColors(True)

        self.tabla.setStyleSheet("""
            QTableWidget {
                border: 2px solid #cfd8dc;
                border-radius: 8px;
                gridline-color: #eceff1;
                background-color: white;
                font-size: 11pt;
                color: black;
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
            QHeaderView::section:hover {
                background-color: #607d8b;
            }
        """)

        header = self.tabla.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents) # N° Orden
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents) # Tipo
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents) # Marca
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents) # Modelo
        header.setSectionResizeMode(4, QHeaderView.ResizeMode. Stretch) # N° Serie
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.ResizeToContents) # Taller
        header.setSectionResizeMode(6, QHeaderView.ResizeMode.ResizeToContents) # Fecha Recepción
        header.setSectionResizeMode(7, QHeaderView.ResizeMode.ResizeToContents) # Fecha Ingreso
        header.setSectionResizeMode(8, QHeaderView.ResizeMode.ResizeToContents) # Días
        header.setSectionResizeMode(9, QHeaderView.ResizeMode. Stretch) # Estado
        header.setSectionResizeMode(10, QHeaderView.ResizeMode. Stretch) # Observaciones
        self. tabla.verticalHeader().setDefaultSectionSize(45)
        self.tabla.itemSelectionChanged.connect(self.on_seleccion_cambiada)

    def crear_botones(self):
        """Crea los botones inferiores"""
        botones_layout = QHBoxLayout()
        botones_layout.setSpacing(15)

        self.btn_ingreso = QPushButton("🔧 Ingreso a Taller")
        self.btn_ingreso.setFont(QFont("Arial", 11, QFont.Weight.Bold))
        self.btn_ingreso.setFixedHeight(50)
        self.btn_ingreso.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_ingreso.setStyleSheet("""
            QPushButton {
                background-color: #1976d2;
                color: white;
                border: none;
                border-radius: 8px;
                padding: 0 30px;
            }
            QPushButton:hover {
                background-color: #1565c0;
            }
        """)
        self.btn_ingreso.clicked.connect(self.ingreso_taller)
        botones_layout.addWidget(self.btn_ingreso)

        self.btn_historial = QPushButton("📜 Ver Historial")
        self.btn_historial.setEnabled(False)
        self.btn_historial.setFont(QFont("Arial", 11, QFont.Weight.Bold))
        self.btn_historial.setFixedHeight(50)
        self.btn_historial.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_historial.setStyleSheet("""
            QPushButton {
                background-color: #7b1fa2;
                color: white;
                border: none;
                border-radius: 8px;
                padding: 0 30px;
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
        botones_layout.addWidget(self.btn_historial)
        
        self.btn_estado = QPushButton("Actualizar estado")
        self.btn_estado.setEnabled(False)
        self.btn_estado.hide()
        self.btn_estado.setFont(QFont("Arial", 11, QFont.Weight.Bold))
        self.btn_estado.setFixedHeight(50)
        self.btn_estado.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_estado.setStyleSheet("""
            QPushButton {
                background-color: #7b1fa2;
                color: white;
                border: none;
                border-radius: 8px;
                padding: 0 30px;
            }
            QPushButton:hover {
                background-color: #6a1b9a;
            }
            QPushButton:disabled {
                background-color: #cfd8dc;
                color: #90a4ae;
            }
        """)
        self.btn_estado.clicked.connect(self.actualizar_estado)
        botones_layout.addWidget(self.btn_estado)

        botones_layout.addStretch()

        self.btn_egreso = QPushButton("✅ Egreso del Taller")
        self.btn_egreso.setEnabled(False)
        self.btn_egreso.setFont(QFont("Arial", 11, QFont.Weight.Bold))
        self.btn_egreso.setFixedHeight(50)
        self.btn_egreso.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_egreso.setStyleSheet("""
            QPushButton {
                background-color: #388e3c;
                color:  white;
                border: none;
                border-radius: 8px;
                padding: 0 30px;
            }
            QPushButton:hover {
                background-color: #2e7d32;
            }
            QPushButton:disabled {
                background-color: #cfd8dc;
                color: #90a4ae;
            }
        """)
        self.btn_egreso.clicked.connect(self.egreso_taller)
        botones_layout.addWidget(self.btn_egreso)

        return botones_layout

    def cargar_tabla(self):
        """Carga datos en la tabla"""
        self.tabla.setRowCount(len(self.datos_filtrados))

        for fila, equipo in enumerate(self.datos_filtrados):
            item_orden = QTableWidgetItem(str(fila + 1))
            item_orden.setTextAlignment(Qt.AlignmentFlag. AlignCenter)
            item_orden.setFont(QFont("Arial", 11, QFont.Weight.Bold))

            taller = equipo.get('taller', '')
            if 'Taller de radio AEP' in taller:
                item_orden.setBackground(QBrush(QColor("#1976d2")))
                item_orden.setForeground(QBrush(QColor("white")))
            elif 'Taller de radio EZE' in taller:
                item_orden.setBackground(QBrush(QColor("#388e3c")))
                item_orden.setForeground(QBrush(QColor("white")))

            self.tabla.setItem(fila, 0, item_orden)

            for col, campo in enumerate(["tipo", "marca", "modelo_equipo", "serie", "taller", "fecha_recepcion", "fecha_ingreso", "dias", "estado_taller", "observaciones"], 1):
                item = QTableWidgetItem(str(equipo.get(campo, ""))) or ''
                item.setTextAlignment(Qt.AlignmentFlag. AlignCenter)
                item.setFont(QFont("Arial", 10))
                self.tabla.setItem(fila, col, item)
                
    def obtener_datos(self):
        """Obtiene TODOS los datos de la API una sola vez al inicio."""
        self._actualizando = True  # ← Bloquear
        try:
            self.datos_completos = self.api.get("vista_taller.php")
            self.datos_filtrados = self.datos_completos.copy()
            self.datos_excel = self.datos_completos.copy()
        
        except SesionExpirada:
            QMessageBox.warning(self, "Sesión expirada",
                                "Tu sesión venció. Cerrá y volvé a iniciar sesión.")
            self.datos_completos = []
            self.datos_filtrados = []

        except ApiError as e:
            QMessageBox.warning(self, "Error",
                                            f"No se pudieron cargar los datos del taller:\n{e}")
            self.datos_completos = []
            self.datos_filtrados = []

        finally:
            self.cargar_tabla()
            self._actualizando = False  # ← Desbloquear

    def aplicar_filtros(self):
        """Aplica filtros"""
        self.datos_filtrados = self.datos_completos.copy()

        texto_busqueda = self.input_buscar.text().strip().upper()
        if texto_busqueda:
            self.datos_filtrados = [
                e for e in self.datos_filtrados if texto_busqueda in e.get('serie', '').upper()]

        taller = self.combo_filtro_taller.currentText()
        if taller != "Todos":
            self. datos_filtrados = [
                e for e in self.datos_filtrados if e.get('taller', '') == taller]

        estado = self.combo_filtro_estado.currentText()
        if estado != "Todos":
            self.datos_filtrados = [e for e in self. datos_filtrados if e.get(
                'estado_taller', '') == estado]

        self.cargar_tabla()

    def limpiar_filtros(self):
        """Limpia filtros"""
        self.input_buscar.clear()
        self.combo_filtro_taller.setCurrentIndex(0)
        self.combo_filtro_estado.setCurrentIndex(0)
        self.datos_filtrados = self.datos_completos.copy()
        #self.cargar_tabla()

    def on_seleccion_cambiada(self):
        """Maneja selección"""
        hay_seleccion = len(self.tabla.selectedItems()) > 0
        self.btn_historial.setEnabled(hay_seleccion)
        self.btn_egreso.setEnabled(hay_seleccion)
        self.btn_estado.setEnabled(hay_seleccion)

    def get_equipo_seleccionado(self):
        """Retorna equipo seleccionado"""
        fila = self.tabla.currentRow()
        if fila >= 0 and fila < len(self. datos_filtrados):
            return self.datos_filtrados[fila]
        return None

    def ingreso_taller(self):
        """Abre diálogo de ingreso"""
        equipo = self.get_equipo_seleccionado()
    
        if not equipo:
            QMessageBox.warning(self, "Aviso", "Debe seleccionar un equipo primero.")
            return
    
        respuesta = QMessageBox.question(
            self,
            "Ingresar equipo",
            f"¿Desea ingresar el equipo {equipo.get('serie', '')} al taller?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
    
        if respuesta == QMessageBox.StandardButton.Yes:
            dialogo = DialogoIngresoTaller(api=self.api, equipo=equipo, parent=self)
            dialogo.ingreso_exitoso.connect(self.cargar_tabla)
            dialogo.exec()
            self.obtener_datos()

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

    def egreso_taller(self):
        """Abre diálogo de egreso"""
        equipo = self.get_equipo_seleccionado()
        # Verificamos el estado ANTES de abrir el diálogo.
        if equipo.get("estado_taller", "") == "No ingresado":
            QMessageBox.warning(self, "Atención",
                "Este equipo no está ingresado al taller, no se puede egresar.")
            return   # no abrimos nada

        if equipo:
            DialogoEgresoTaller(api= self.api, equipo_data=equipo, parent=self).exec()
            self.obtener_datos()
            
    def actualizar_estado(self):
        """Abre diálogo de actualización de estado"""
        equipo = self.get_equipo_seleccionado()
        if equipo:
            DialogoActualizarEstado(equipo, self).exec()
            
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
            self.llenar_combo("talleres.php", self.combo_filtro_taller, "taller", incluir_todos= True)
            self.llenar_combo("estados_taller.php", self.combo_filtro_estado, "estado", incluir_todos= True)

        except SesionExpirada:
            self.window().sesion_expirada()
        
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


"""
Pestaña:  Ingreso de Equipos
Versión: 4.1 - MEJORADA Y ACTUALIZADA
Fecha: 2025-12-14
Autor: lucasarsa2015-cpu
Autor: Oscar Ariel Contro
Descripción: Formulario completo de ingreso de equipos con opciones, importación desde Excel, y configuración de programación de canales.
librerías: PyQt6, requests, pandas, direcciones
indice de clases:
- ModalImportarAlta(QDialog): Ventana modal para importar datos desde un archivo .xlsx      Comienzo linea 29 final linea 261
- DialogoProgramacion(QDialog): Ventana modal para configurar frecuencias y canales         Comienzo linea 267 final linea 667
- IngresoEquiposTab(QWidget): Pestaña principal para el ingreso de equipos                  Comienzo linea 671 final linea 1391
"""
from operator import index
from operator import index
from base_tab import ApiTab
from api_client import ApiError, SesionExpirada
import os
import requests
import pandas as pd
import direcciones # type: ignore
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QFrame, QGridLayout, QComboBox, QTextEdit,
    QDialog, QTableWidget, QTableWidgetItem, QSpinBox, QHeaderView,
    QMessageBox, QFileDialog, QScrollArea, QCheckBox, QProgressDialog, QApplication
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QPixmap

# ═══════════════════════════════════════════════════════════
#
# VENTANA MODAL: IMPORTAR ALTA DESDE XLSX (QDialog)
#
# ═══════════════════════════════════════════════════════════

class ModalImportarAlta(QDialog):
    def __init__(self, api, datos_df, parent=None):
        super().__init__(parent)
        self.api = api
        self.setWindowTitle("Ventana de registro de equipos .xlsx")
        self.showMaximized()
        self.setModal(True)
        self.crear_interfaz(datos_df)
        
        #self.obtener_duplicados()

    def crear_interfaz(self, datos_df):
        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        header = QLabel("📋 Datos importados desde archivo .xlsx")
        header.setFont(QFont("Arial", 18, QFont.Weight.Bold))
        header.setAlignment(Qt.AlignmentFlag.AlignCenter)
        header.setFixedHeight(60)
        header.setStyleSheet("""
            QLabel {
                background-color: #78909c;
                color: white;
                border-radius: 8px;
                padding: 10px;
            }
        """)
        layout.addWidget(header)
        
        # Crear la tabla
        self.tabla = QTableWidget()
        self.tabla.setRowCount(len(datos_df))
        self.tabla.setColumnCount(len(datos_df.columns))
        self.tabla.setHorizontalHeaderLabels(datos_df.columns)
        self.tabla.setHorizontalHeaderLabels([
            "Tipo",
            "Marca",
            "Modelo",
            "N° Serie",
            "Escala",
            "Sector",
            "Estado",
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
            0, QHeaderView.ResizeMode.ResizeToContents)  # N° Orden
        header.setSectionResizeMode(
            1, QHeaderView.ResizeMode.ResizeToContents)  # Tipo
        header.setSectionResizeMode(
            2, QHeaderView.ResizeMode.ResizeToContents)  # Marca
        header.setSectionResizeMode(
            3, QHeaderView.ResizeMode.ResizeToContents)  # Modelo
        header.setSectionResizeMode(
            4, QHeaderView.ResizeMode. Stretch)  # N° Serie
        header.setSectionResizeMode(
            5, QHeaderView.ResizeMode.ResizeToContents)  # Escala
        header.setSectionResizeMode(
            6, QHeaderView.ResizeMode. Stretch)  # Sector
        header.setSectionResizeMode(
            7, QHeaderView.ResizeMode.ResizeToContents)  # Estado

        # Altura de filas
        self.tabla.verticalHeader().setDefaultSectionSize(30)

        # Llenar datos
        for i in range(len(datos_df)):
            for j in range(len(datos_df.columns)):
                valor = str(datos_df.iat[i, j]) if pd.notna(datos_df.iat[i, j]) else ""
                self.tabla.setItem(i, j, QTableWidgetItem(valor))
        
        layout.addWidget(self.tabla)
        
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
        
        btn_insert = QPushButton("Insertar Registros")
        btn_insert.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        btn_insert.setFixedHeight(45)
        btn_insert.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_insert.setStyleSheet("""
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
        btn_insert.clicked.connect(self.subir_datos)
        botones_layout.addWidget(btn_insert)

        layout.addLayout(botones_layout)

        self.setLayout(layout)
        
    def get_datos(self):
        """Devuelve los datos importados como una lista de diccionarios"""
        datos = []
        columnas = self.tabla.columnCount()
        filas = self.tabla.rowCount()
    
        # 1. Obtener los nombres de las columnas
        headers = []
        for col in range(columnas):
            header_item = self.tabla.horizontalHeaderItem(col)
            headers.append(header_item.text() if header_item else f"Columna_{col}")

        # 2. Recorre las filas
        for fila in range(filas):
            dict_fila = {}
            for col in range(columnas):
                item = self.tabla.item(fila, col)
                valor = item.text().upper() if item else ""
                valor = valor.upper()
            
                # Asociamos el nombre de la columna con su valor
                dict_fila[headers[col]] = valor
        
            # 3. Guardamos el diccionario de la fila en nuestra lista final
            datos.append(dict_fila)
        return datos
         
    def subir_datos(self):
        """Envía los equipos uno por uno, mostrando progreso en tiempo real."""
        datos_tabla = self.get_datos()
        total = len(datos_tabla)
 
        if total == 0:
            QMessageBox.information(self, "Sin datos", "No hay registros para importar.")
            return
 
        # ── Barra de progreso ──
        progreso = QProgressDialog("Importando equipos...", "Cancelar", 0, total, self)
        progreso.setWindowTitle("Importación en curso")
        progreso.setWindowModality(Qt.WindowModality.WindowModal)
        progreso.setMinimumDuration(0)   # se muestra de inmediato, sin esperar
        progreso.setAutoClose(True)
        progreso.setAutoReset(True)
 
        errores = []
        exitos = 0
 
        for i, equipo in enumerate(datos_tabla):
            # El usuario puede cancelar a mitad de camino.
            if progreso.wasCanceled():
                break
 
            numero_serie = equipo.get("N° Serie", "")
 
            # Actualiza texto y número de la barra ANTES de procesar la fila,
            # así el usuario ve qué se está por insertar, no lo que ya pasó.
            progreso.setLabelText(f"Importando {i + 1} de {total}:  N° Serie {numero_serie}")
            progreso.setValue(i)
 
            payload = {
                "tipo": equipo.get("Tipo", ""),
                "marca": equipo.get("Marca", ""),
                "modelo": equipo.get("Modelo", ""),
                "numero_serie": numero_serie,
                "escala": equipo.get("Escala", ""),
                "sector": equipo.get("Sector", ""),
                "estado": equipo.get("Estado", ""),
                "potencia": equipo.get("Potencia", ""),
                "ult_observacion": equipo.get("Observaciones", ""),
            }
 
            try:
                self.api.post("ingreso_equipos.php", payload)
                exitos += 1
 
            except SesionExpirada:
                progreso.close()
                QMessageBox.warning(self, "Sesión expirada",
                    "Tu sesión venció. Cerrá y volvé a iniciar sesión.\n"
                    f"Se alcanzaron a guardar {exitos} equipos antes de cortar.")
                self._ofrecer_exportar_errores(errores)
                return
 
            except ApiError as e:
                errores.append({
                    "N° Serie": numero_serie,
                    "Tipo": payload["tipo"],
                    "Marca": payload["marca"],
                    "Modelo": payload["modelo"],
                    "Motivo del error": str(e),
                })
 
            # Procesar eventos de Qt para que la barra se repinte en cada vuelta,
            # en lugar de quedar congelada hasta terminar todo el bucle.
            QApplication.processEvents()
 
        progreso.setValue(total)   # completa la barra al 100%
        progreso.close()
 
        # Mensaje final
        if progreso.wasCanceled():
            QMessageBox.information(self, "Importación cancelada",
                f"Se cancelón la importación.\nSe alcanzaron a guardar {exitos} de {total} equipos.")
            self._ofrecer_exportar_errores(errores)
        elif not errores:
            QMessageBox.information(self, "Éxito",
                                    f"Se insertaron {exitos} registros correctamente.")
            self.accept()
        else:
            detalle = "\n".join(e["Motivo del error"] for e in errores[:5])
            QMessageBox.warning(self, "Resultado parcial",
                f"Éxitos: {exitos}\nErrores: {len(errores)}\n\nDetalle:\n{detalle}")
            self._ofrecer_exportar_errores(errores)

    def _ofrecer_exportar_errores(self, errores):
        """Pregunta si querés exportar los errores a Excel y lo genera."""
        if not errores:
            return

        respuesta = QMessageBox.question(
            self, "Exportar errores",
            f"Se registraron {len(errores)} errores.\n"
            "¿Querés exportarlos a un archivo Excel?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if respuesta != QMessageBox.StandardButton.Yes:
            return

        ruta, _ = QFileDialog.getSaveFileName(
            self, "Guardar errores de importación",
            "errores_importacion.xlsx",
            "Archivos Excel (*.xlsx)"
        )
        if not ruta:
            return   # el usuario canceló el diálogo de guardado

        try:
            df_errores = pd.DataFrame(errores)
            df_errores.to_excel(ruta, index=False)
            QMessageBox.information(self, "Exportado",
                f"Los errores se guardaron en:\n{ruta}")
        except Exception as e:
            QMessageBox.critical(self, "Error al exportar",
                f"No se pudo generar el archivo Excel:\n{e}")
            
    def obtener_duplicados(self):
        
        equipos = self.get_datos()
        numeros = []
        ubicacion = []
        comparar = None
        contador = 0
        ordenar = sorted(equipos, key=lambda x: x['N° Serie'])
        for fila in equipos:
            contador += 1
            serie_actual = fila["N° Serie"]
            if serie_actual == comparar:
                numeros.append((fila["N° Serie"]))
                ubicacion.append(contador)
                
            comparar = serie_actual
            
        duplicados = len(numeros)
        print(numeros, duplicados, contador, ubicacion)


# ═══════════════════════════════════════════════════════════
#
# VENTANA MODAL:  PROGRAMACIÓN DE CANALES (QDialog)
#
# ═══════════════════════════════════════════════════════════

class DialogoProgramacion(QDialog):
    """Ventana modal para configurar frecuencias y canales"""

    def __init__(self, api, parent=None, programacion_actual=None, serie_equipo=None):
        super().__init__(parent)
        self.setWindowTitle("⚙️ Programación de Frecuencias y Canales")
        self.setModal(True)
        self.api = api
        self.numero_serie = serie_equipo
        self.programacion_data = programacion_actual if programacion_actual else {
            'cantidad_canales': 16,
            'canales': []
        }

        self.canales_data = []
        self.crear_interfaz()
        self.cargar_datos_existentes()
        self.llenar_desplegables()
        print(self.numero_serie)

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
        btn_generar.setFont(QFont("Arial", 12, QFont.Weight. Bold))
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

        self.tabla_canales. setStyleSheet("""
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
        self.llenar_combo("plantillas.php", self.combo_plantilla, "nombre_plantilla", incluir_escriba=False)
        
    def subir_programacion_api(self, programacion_data=None):
            """Envía la programación de canales a la API"""
            try:
                self.api.post("programacion_canales.php", self.programacion_data)
                #self.api.post("programacion_canales.php", {"numero_serie": self.,self.programacion_data})
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
# PESTAÑA PRINCIPAL:  INGRESO DE EQUIPOS
#
# ═══════════════════════════════════════════════════════════

class IngresoEquiposTab(ApiTab):
    """Pestaña de ingreso de equipos"""

    def __init__(self, api, programacion_dat=None):
        super().__init__(api)
        self.api = api
        self.programacion_data = {
            'cantidad_canales': 16,
            'canales': []
        }
        self.API_BASE_URL = direcciones.URL.API_BASE_URL  # URL base de la API
        self.crear_interfaz()
        self.llenar_desplegables()
        self.programacion = programacion_dat
        

    def crear_interfaz(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(15)

        header = QLabel("📥 INGRESO DE EQUIPOS")
        header.setFont(QFont("Arial", 20, QFont.Weight.Bold))
        header.setAlignment(Qt.AlignmentFlag.AlignCenter)
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

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        #scroll.viewport().setStyleSheet("background-color: #f0f0f0;")

        form_widget = QWidget()
        form_widget.setStyleSheet("background-color: #eceff1;")
        form_main_layout = QHBoxLayout()
        form_main_layout.setSpacing(20)

        left_column = self.crear_formulario()
        form_main_layout.addWidget(left_column, 2)

        right_column = self.crear_columna_imagen()
        form_main_layout.addWidget(right_column, 1)

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

        row = 0

        lbl = QLabel("📻 Tipo de equipo:")
        lbl.setStyleSheet(estilo_label)
        lbl.setAlignment(Qt.AlignmentFlag.AlignRight |
                         Qt.AlignmentFlag.AlignVCenter)
        form_layout.addWidget(lbl, row, 0)

        self.combo_tipo = QComboBox()
        self.combo_tipo.setEditable(True)
        self.combo_tipo.setPlaceholderText("Seleccione o escriba...")
        self.combo_tipo.lineEdit().setPlaceholderText("Seleccione o escriba...")
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
        self.combo_marca.lineEdit().setPlaceholderText("Seleccione o escriba...")
        self.combo_marca.setFixedHeight(45)
        self.combo_marca.setStyleSheet(estilo_input)
        form_layout.addWidget(self. combo_marca, row, 1)
        row += 1

        lbl = QLabel("📱 Modelo:")
        lbl.setStyleSheet(estilo_label)
        lbl.setAlignment(Qt.AlignmentFlag.AlignRight |
                         Qt.AlignmentFlag.AlignVCenter)
        form_layout.addWidget(lbl, row, 0)

        self. combo_modelo = QComboBox()
        self.combo_modelo.setEditable(True)
        self.combo_modelo.setPlaceholderText("Seleccione o escriba...")
        self.combo_modelo.lineEdit().setPlaceholderText("Seleccione o escriba...")
        self.combo_modelo.setFixedHeight(45)
        self.combo_modelo.setStyleSheet(estilo_input)
        self.combo_modelo.currentTextChanged.connect(self.cargar_imagen_modelo)
        form_layout. addWidget(self.combo_modelo, row, 1)
        row += 1

        lbl = QLabel("🔢 N° de Serie:")
        lbl.setStyleSheet(
            "color: #c62828; font-weight: bold; font-size: 11pt;")
        lbl.setAlignment(Qt.AlignmentFlag.AlignRight |
                         Qt.AlignmentFlag.AlignVCenter)
        form_layout.addWidget(lbl, row, 0)

        self.input_serie = QLineEdit()
        self.input_serie.setPlaceholderText("Ej: ABC123XYZ")
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
        self.input_serie.textChanged.connect(self.formatear_numero_serie)
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
        self.combo_escala.lineEdit().setPlaceholderText("Seleccione o escriba...")
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
        self.combo_sector.lineEdit().setPlaceholderText("Seleccione o escriba...")
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
        self.combo_estado.lineEdit().setPlaceholderText("Seleccione o escriba...")
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

        self.label_prog_info = QLabel("(No configurado)")
        self.label_prog_info.setFont(QFont("Arial", 9))
        self.label_prog_info.setStyleSheet(
            "color: #c62828; font-style: italic;")
        prog_layout.addWidget(self.label_prog_info)

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

    def crear_columna_imagen(self):
        """Crea la columna de imagen del equipo"""
        column = QFrame()
        column.setStyleSheet("""
            QFrame {
                background-color: white;
                border-radius: 10px;
                border: 2px solid #cfd8dc;
            }
        """)

        layout = QVBoxLayout()
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(10)

        titulo = QLabel("📷 Imagen del Equipo")
        titulo.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        titulo.setStyleSheet("color: #37474f;")
        titulo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(titulo)

        self.label_imagen = QLabel("📷\n\nSin imagen\ndisponible")
        self.label_imagen.setFixedSize(350, 350)
        self.label_imagen.setStyleSheet("""
            QLabel {
                border: 3px dashed #cfd8dc;
                border-radius: 8px;
                background-color:  #fafafa;
                color: #90a4ae;
                font-size: 14pt;
                font-weight: bold;
            }
        """)
        self.label_imagen.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.label_imagen,
                         alignment=Qt.AlignmentFlag. AlignCenter)

        layout.addStretch()

        column.setLayout(layout)
        return column

    def crear_botones_inferiores(self):
        """Crea los botones de acción inferiores"""
        botones_layout = QHBoxLayout()
        botones_layout. setSpacing(15)

        btn_importar = QPushButton("📊 Importar desde Excel")
        btn_importar. setFont(QFont("Arial", 11, QFont.Weight.Bold))
        btn_importar.setFixedHeight(45)
        btn_importar.setCursor(Qt.CursorShape. PointingHandCursor)
        btn_importar.setStyleSheet("""
            QPushButton {
                background-color: #388e3c;
                color:  white;
                border: none;
                border-radius: 8px;
                padding: 0 25px;
            }
            QPushButton:hover {
                background-color: #2e7d32;
            }
        """)
        btn_importar.clicked.connect(self.importar_excel)
        botones_layout.addWidget(btn_importar)

        botones_layout.addStretch()

        btn_guardar = QPushButton("💾 Guardar Equipo")
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
        btn_guardar.clicked.connect(self.guardar_equipo)
        botones_layout.addWidget(btn_guardar)

        return botones_layout

    def formatear_numero_serie(self, text):
        cursor_pos = self.input_serie. cursorPosition()
        text_formateado = text. upper().replace(" ", "")
        if text != text_formateado:
            self.input_serie.blockSignals(True)
            self.input_serie.setText(text_formateado)
            self.input_serie.setCursorPosition(cursor_pos)
            self.input_serie.blockSignals(False)
            
# ================================
# CARGAR IMAGEN DEL MODELO
# ================================
    
    def capturar_modelo_actual(self):
        modelo = self.combo_modelo.currentText().strip()
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
        # Si no se pasa modelo, obtenerlo del combo
        if modelo is None:
            modelo = self.combo_modelo.currentText().strip()
    
        if not modelo or modelo == "":
            self.mostrar_placeholder()
            return

        nombre_archivo = self.consulta_ruta_imagen(modelo)
    
        if not nombre_archivo:
            self.mostrar_placeholder(modelo)
            return
    
        # 2. Construir la ruta completa local
        ruta_imagenes = direcciones.URL.IMG_BASE_URL  # Carpeta local de imágenes
        ruta_completa = os.path.join(ruta_imagenes, nombre_archivo)
    
        # 3. Verificar si el archivo existe
        if not os.path.exists(ruta_completa):
            self.mostrar_placeholder(modelo)
            return
    
        # 4. Cargar la imagen
        pixmap = QPixmap(ruta_completa)
        if pixmap.isNull():
            self.mostrar_placeholder(modelo)
            return
    
        # 5. Mostrar la imagen escalada
        pixmap_scaled = pixmap.scaled(
            350, 350,
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
                font-size: 14pt;
                font-weight: bold;
            }
        """)
        
# ================================
# CONFIGURAR PROGRAMACIÓN
# ================================

    def abrir_programacion(self):
        numero_serie = self.input_serie.text().strip()
        dialogo = DialogoProgramacion(self.api, self, self.programacion_data, numero_serie)
        dialogo.showMaximized()
        if dialogo.exec() == QDialog.DialogCode.Accepted:
            self.programacion_data = dialogo.get_programacion()
            cantidad = self.programacion_data['cantidad_canales']
            self.label_prog_info.setText(f"✅ Configurado ({cantidad} canales)")
            self.label_prog_info.setStyleSheet(
                "color: #1e8449; font-style: normal; font-weight: bold;")
            
    def get_nombre_plantilla(self):
        try:
            return self.programacion_data['canales'][0]['nombre_config']
        except (KeyError, IndexError, TypeError):
            return ''
# ================================
# IMPORTAR DESDE EXCEL
# ================================

    def importar_excel(self):
        archivo, _ = QFileDialog.getOpenFileName(
            self, "Importar Excel", "", "Archivos Excel (*.xlsx *.xls)"
        )

        if archivo:
            try:
                df = pd.read_excel(archivo, dtype=str)
                columnas_texto = ['Tipo', 'Marca', 'Sector', 'Estado']
                df[columnas_texto] = df[columnas_texto].apply(lambda x: x.str.strip().str.title())
                modelos_clean = ['Modelo']
                df[modelos_clean] = df[modelos_clean].apply(lambda x: x.str.strip())
                errores_texto = {
                    'Base Vhf Fm': 'Base VHF FM',
                    'Vhf Aeronautico': 'VHF Aeronautico',
                    'Lineal Hf':'Lineal HF',
                    'Receptor Hf':'Receptor HF',
                    'Excitador Hf': 'Excitador HF',
                    'Exitador Hf': 'Excitador HF',   # error de tipeo frecuente en las planillas
                    'Icom':'ICOM',
                    'Cubic':'CUBIC',
                    'Glidepath':'GLIDEPATH',

                }
                columnas_corregir = ['Tipo', 'Marca', 'Sector']
                df[columnas_corregir] = df[columnas_corregir].replace(errores_texto)

                # Creamos la instancia de la nueva ventana y le pasamos los datos
                # Usamos 'self.nueva_ventana' para que la variable persista en memoria
                self.nueva_ventana = ModalImportarAlta(self.api, df)
                self.nueva_ventana.show()
                
            except Exception as e:
                QMessageBox.critical(self, "Error", f"No se pudo abrir la ventana: {e}")
                
# ================================
# ALTA DE EQUIPO EN LA BASE DE DATOS
# ================================

    def guardar_equipo(self):
        serie = self.input_serie.text().strip()
        if not serie:
            QMessageBox.warning(
                self,
                "⚠️ Campo Requerido",
                "El N° de Serie es obligatorio."
            )
            self.input_serie.setFocus()
            return
        datos_capturados = self.capturar_datos_equipo()

        if self.alta_equipo_api(datos_capturados):
            #self.subir_programacion_api(self.programacion_data)
            #print(self.programacion_data)
            self.limpiar_campos()

    def limpiar_campos(self):
        self.combo_tipo.setCurrentText("")
        self.combo_marca.setCurrentText("")
        self.combo_modelo.setCurrentText("")
        self.input_serie.clear()
        self.combo_escala.setCurrentText("")
        self.combo_sector.setCurrentText("")
        self.combo_estado.setCurrentText("")
        self.combo_potencia.setCurrentText("")
        self.text_observaciones. clear()
        self.label_imagen.clear()
        self.mostrar_placeholder()
        self.programacion_data = None
        self.label_prog_info.setText("(No configurado)")
        self.label_prog_info.setStyleSheet(
            "color: #c62828; font-style: italic;")
        
    def capturar_datos_equipo(self):
        datos_equipo = {
            "tipo": self.combo_tipo.currentText().strip(),
            "marca": self.combo_marca.currentText().strip(),
            "modelo": self.combo_modelo.currentText().strip(),
            "numero_serie": self.input_serie.text().strip(),
            "escala": self.combo_escala.currentText().strip(),
            "sector": self.combo_sector.currentText().strip(),
            "estado": self.combo_estado.currentText().strip(),
            "potencia": self.combo_potencia.currentText().strip(),
            "nombre_plantilla": self.get_nombre_plantilla(),
            "ult_observacion": self.text_observaciones.toPlainText().strip()
        }
        return datos_equipo
        
    def alta_equipo_api(self, datos_equipo):
        # self.programacion_data (CON "_data") es el que abrir_programacion()
        # actualiza de verdad con dialogo.get_programacion(). self.programacion
        progra = self.programacion_data
        
        try:
            payload = {
                "equipo": datos_equipo,
                "frecuencias": progra,
            }
            self.api.post("alta_equipo.php", payload)
            print(payload)

            # Si llegamos acá, el servidor respondió 2xx: se guardó bien.
            QMessageBox.information(
                self, "✅ Equipo Guardado",
                "El equipo ha sido guardado exitosamente en la base de datos."
            )
            return True

        except SesionExpirada:
            QMessageBox.warning(self, "Sesión expirada",
                                "Tu sesión venció. Cerrá y volvé a iniciar sesión.")
            return False
        except ApiError as e:
            QMessageBox.critical(self, "❌ Error al Guardar",
                                 f"No se pudo guardar el equipo:\n{e}")
            return False  
# ================================
# CARGA DE DATOS EN COMBOS
# ================================  
    
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
            
    def subir_programacion_api(self, programacion_data=None):
            """Envía la programación de canales a la API"""
            try:
                self.api.post("programacion_canales.php", self.programacion_data)
    
                # Si llegamos a esta línea, el servidor respondió 2xx: se guardó bien.
                # Cualquier error (validación, base, token) ya habría saltado como excepción.
                QMessageBox.information(self, "Éxito",
                                        "Programación de canales guardada correctamente.")
    
            except SesionExpirada:
                QMessageBox.warning(self, "Sesión expirada",
                                    "Tu sesión venció. Cerrá y volvé a iniciar sesión.")
            except ApiError as e:
                QMessageBox.critical(self, "Error", f"No se pudo guardar la programación:\n{e}")
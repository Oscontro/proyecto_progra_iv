"""
Pestaña:    Últimos Movimientos
Versión:  3.0 - FINAL CORREGIDA
Fecha: 2025-12-15
Autor: lucasarsa2015-cpu
Descripción: Timeline VACÍO con colores suaves en diálogo
"""
import pandas as pd
from openpyxl import load_workbook
from openpyxl.utils import get_column_letter
from base_tab import ApiTab
from api_client import ApiError, SesionExpirada
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QFrame, QComboBox, QScrollArea, QMessageBox,
    QDialog, QTextEdit, QDateEdit, QFileDialog
)
from PyQt6.QtCore import Qt, QDate
from PyQt6.QtGui import QFont, QColor
from datetime import datetime, timedelta


# ═══════════════════════════════════════════════════════════
# DIÁLOGO:   VER DETALLE DEL MOVIMIENTO (COLORES SUAVES)
# ═══════════════════════════════════════════════════════════

class DialogoDetalleMovimiento(QDialog):
    """Ventana modal con detalle completo del movimiento - COLORES SUAVES"""

    def __init__(self, movimiento_data, parent=None):
        super().__init__(parent)
        self.movimiento_data = movimiento_data
        self.setWindowTitle("📋 Detalle del Movimiento")
        self.setModal(True)
        self.setFixedSize(600, 550)
        self.crear_interfaz()

    def crear_interfaz(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(25, 25, 25, 25)
        layout.setSpacing(20)

        # Título
        titulo = QLabel("📋 DETALLE DEL MOVIMIENTO")
        titulo.setFont(QFont("Arial", 18, QFont.Weight.Bold))
        titulo.setStyleSheet("color: #1976d2;")
        titulo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(titulo)

        # Frame principal con COLORES SUAVES
        info_frame = QFrame()
        info_frame.setStyleSheet("""
            QFrame {
                background-color: #f5f5f5;
                border:  2px solid #cfd8dc;
                border-radius: 8px;
                padding: 20px;
            }
        """)

        info_layout = QVBoxLayout()
        info_layout.setSpacing(12)

        # Fecha y hora
        lbl_fecha = QLabel(f"🕐 {self.movimiento_data.get('fecha', 'N/A')}")
        lbl_fecha.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        lbl_fecha.setStyleSheet("color: #37474f;")
        info_layout.addWidget(lbl_fecha)

        # Usuario
        lbl_usuario = QLabel(
            f"👤 Usuario: {self.movimiento_data.get('usuario', 'N/A')}")
        lbl_usuario.setFont(QFont("Arial", 11))
        lbl_usuario. setStyleSheet("color: #546e7a;")
        info_layout.addWidget(lbl_usuario)

        # Separador
        separador = QFrame()
        separador.setFrameShape(QFrame.Shape.HLine)
        separador.setStyleSheet("background-color: #cfd8dc;")
        info_layout.addWidget(separador)

        # Tipo de acción
        icono = self.movimiento_data.get('icono', '📋')
        tipo = self.movimiento_data.get('tipo_accion', 'N/A')
        lbl_tipo = QLabel(f"{icono} {tipo}")
        lbl_tipo.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        lbl_tipo.setStyleSheet(
            f"color: {self.movimiento_data.get('color', '#1976d2')};")
        info_layout. addWidget(lbl_tipo)

        # Datos del equipo
        if self.movimiento_data.get('identificador'):
            equipo_frame = QFrame()
            equipo_frame.setStyleSheet("""
                QFrame {
                    background-color: white;
                    border: 1px solid #e0e0e0;
                    border-radius: 5px;
                    padding: 10px;
                }
            """)

            equipo_layout = QVBoxLayout()

            equipo_html = f"""
            <p style='margin:   3px 0; color: #37474f;'><b>N° de Serie:</b> {self.movimiento_data.get('identificador', 'N/A')}</p>
            <p style='margin:  3px 0; color:  #37474f;'><b>Tipo:</b> {self.movimiento_data.get('tipo', 'N/A')}</p>
            <p style='margin: 3px 0; color: #37474f;'><b>Marca:</b> {self.movimiento_data.get('marca', 'N/A')}</p>
            <p style='margin: 3px 0; color: #37474f;'><b>Modelo:</b> {self.movimiento_data.get('modelo_equipo', 'N/A')}</p>
            """
            lbl_equipo = QLabel(equipo_html)
            lbl_equipo.setFont(QFont("Arial", 10))
            lbl_equipo.setWordWrap(True)
            equipo_layout.addWidget(lbl_equipo)

            equipo_frame.setLayout(equipo_layout)
            info_layout.addWidget(equipo_frame)

        # Detalle
        lbl_detalle_titulo = QLabel("📝 Detalle:")
        lbl_detalle_titulo.setFont(QFont("Arial", 11, QFont.Weight.Bold))
        lbl_detalle_titulo.setStyleSheet("color: #37474f;")
        info_layout.addWidget(lbl_detalle_titulo)

        lbl_detalle = QLabel(
            self.movimiento_data.get('detalle', 'Sin detalles'))
        lbl_detalle.setFont(QFont("Arial", 10))
        lbl_detalle.setStyleSheet(
            "color: #546e7a; padding: 8px; background-color: white; border-radius: 5px;")
        lbl_detalle.setWordWrap(True)
        info_layout.addWidget(lbl_detalle)

        # Cambios de estado (si existen)
        if self.movimiento_data.get('estado_anterior'):
            cambio_frame = QFrame()
            cambio_frame.setStyleSheet("""
                QFrame {
                    background-color: white;
                    border: 1px solid #e0e0e0;
                    border-radius: 5px;
                    padding: 10px;
                }
            """)

            cambio_layout = QVBoxLayout()

            cambio_html = f"""
            <p style='margin:  3px 0;'>
            <span style='color: #f44336;'><b>Estado anterior:</b> {self.movimiento_data.get('estado_anterior')}</span> 
            <span style='color: #78909c;'>→</span>
            <span style='color:  #4caf50;'><b>Estado nuevo:</b> {self.movimiento_data.get('estado_nuevo')}</span>
            </p>
            """
            lbl_cambio = QLabel(cambio_html)
            lbl_cambio.setFont(QFont("Arial", 10))
            lbl_cambio.setWordWrap(True)
            cambio_layout.addWidget(lbl_cambio)

            cambio_frame.setLayout(cambio_layout)
            info_layout.addWidget(cambio_frame)

        # Observaciones
        if self.movimiento_data.get('observaciones'):
            lbl_obs_titulo = QLabel("💬 Observaciones:")
            lbl_obs_titulo.setFont(QFont("Arial", 10, QFont.Weight.Bold))
            lbl_obs_titulo.setStyleSheet("color: #37474f;")
            info_layout.addWidget(lbl_obs_titulo)

            text_obs = QTextEdit()
            text_obs.setPlainText(
                self.movimiento_data.get('observaciones', ''))
            text_obs.setReadOnly(True)
            text_obs.setMaximumHeight(80)
            text_obs.setStyleSheet("""
                QTextEdit {
                    border: 1px solid #e0e0e0;
                    border-radius: 5px;
                    padding: 8px;
                    background-color: white;
                    color:  #37474f;
                }
            """)
            info_layout.addWidget(text_obs)

        info_frame.setLayout(info_layout)
        layout.addWidget(info_frame)

        layout.addStretch()

        # Botón cerrar
        botones_layout = QHBoxLayout()
        botones_layout.addStretch()

        btn_cerrar = QPushButton("Cerrar")
        btn_cerrar.setFont(QFont("Arial", 11, QFont.Weight.Bold))
        btn_cerrar.setFixedHeight(45)
        btn_cerrar. setCursor(Qt.CursorShape.PointingHandCursor)
        btn_cerrar.setStyleSheet("""
            QPushButton {
                background-color:  #1976d2;
                color: white;
                border-radius: 6px;
                padding: 0 30px;
            }
            QPushButton:hover {
                background-color: #1565c0;
            }
        """)
        btn_cerrar.clicked.connect(self.accept)
        botones_layout. addWidget(btn_cerrar)

        botones_layout.addStretch()

        layout.addLayout(botones_layout)
        self.setLayout(layout)


# ═══════════════════════════════════════════════════════════
# PESTAÑA PRINCIPAL: ÚLTIMOS MOVIMIENTOS
# ═══════════════════════════════════════════════════════════

class UltimosMovimientosTab(ApiTab):
    """Pestaña de últimos movimientos - Timeline VACÍO"""

    def __init__(self, api):
        super().__init__(api)
        self.api = api
        self.movimientos_completos = []  # VACÍO
        self.movimientos_mostrados = []
        self.movimientos_por_pagina = 20
        self.pagina_actual = 0
        self.crear_interfaz()
        self.llenar_desplegables()

    def crear_interfaz(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(15)

        # Header
        header = QLabel("📅 ÚLTIMOS MOVIMIENTOS")
        header.setFont(QFont("Arial", 20, QFont.Weight.Bold))
        header.setAlignment(Qt.AlignmentFlag.AlignCenter)
        header.setFixedHeight(60)
        header.setStyleSheet("""
            QLabel {
                background:   qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #1565c0, stop:1 #1976d2);
                color: white;
                padding: 15px;
                border-radius:   10px;
                border: 3px solid #0d47a1;
            }
        """)
        layout.addWidget(header)

        # Info de período
        self.lbl_periodo = QLabel(
            "📅 Seleccione un rango de fechas para cargar movimientos")
        self.lbl_periodo.setFont(QFont("Arial", 11))
        self.lbl_periodo.setStyleSheet("color: #546e7a; padding:   5px;")
        self.lbl_periodo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.lbl_periodo)

        # Búsqueda y filtros
        busqueda_layout = self.crear_busqueda_filtros()
        layout.addLayout(busqueda_layout)

        # Scroll area con timeline
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll. setFrameShape(QFrame.Shape.NoFrame)
        self.scroll.setStyleSheet("""
            QScrollArea {
                background-color: #F3F3F3;
                border: none;
            }
        """)

        self.timeline_widget = QWidget()
        self.timeline_widget.setStyleSheet("background-color: #eceff1;")
        self.timeline_layout = QVBoxLayout()
        self.timeline_layout.setSpacing(12)
        self.timeline_layout.setContentsMargins(10, 10, 10, 10)

        # Mensaje inicial
        self.crear_mensaje_vacio()

        self. timeline_widget.setLayout(self.timeline_layout)
        self.scroll.setWidget(self.timeline_widget)

        layout.addWidget(self. scroll, 1)

        # Botón "Cargar más"
        self.btn_cargar_mas = QPushButton("⬇️ Cargar Más Movimientos")
        self.btn_cargar_mas.setFont(QFont("Arial", 11, QFont.Weight.Bold))
        self.btn_cargar_mas.setFixedHeight(45)
        self.btn_cargar_mas.setCursor(Qt.CursorShape. PointingHandCursor)
        self.btn_cargar_mas.setEnabled(False)
        self.btn_cargar_mas.setStyleSheet("""
            QPushButton {
                background-color: #1976d2;
                color: white;
                border-radius: 6px;
            }
            QPushButton:hover {
                background-color: #1565c0;
            }
            QPushButton:disabled {
                background-color: #cfd8dc;
                color: #90a4ae;
            }
        """)
        self.btn_cargar_mas.clicked. connect(self.cargar_mas_movimientos)
        layout.addWidget(self.btn_cargar_mas)

        # Botones inferiores
        botones_layout = self.crear_botones()
        layout.addLayout(botones_layout)

        self.setLayout(layout)

    def crear_busqueda_filtros(self):
        """Búsqueda y filtros con rango de fechas"""
        container_layout = QVBoxLayout()
        container_layout.setSpacing(10)

        # Búsqueda
        busqueda_layout = QHBoxLayout()
        lbl_buscar = QLabel("🔍 Buscar:")
        lbl_buscar.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        lbl_buscar.setStyleSheet("color: #37474f;")
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
            QLineEdit:focus { border: 2px solid #1976d2; }
        """)
        self.input_buscar.textChanged.connect(self.aplicar_filtros)
        busqueda_layout.addWidget(self.input_buscar)

        btn_limpiar = QPushButton("🗑️ Limpiar Filtros")
        btn_limpiar.setFixedHeight(35)
        btn_limpiar.setStyleSheet("""
            QPushButton {
                background-color:  #757575;
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

        # Filtros (Fila 1: Tipo y Usuario)
        filtros_layout1 = QHBoxLayout()
        lbl_filtros = QLabel("Filtros:")
        lbl_filtros.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        lbl_filtros.setStyleSheet("color: #37474f;")
        filtros_layout1.addWidget(lbl_filtros)

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

        lbl_tipo = QLabel("Tipo:")
        lbl_tipo.setStyleSheet("color: #37474f;")
        filtros_layout1.addWidget(lbl_tipo)
        self.combo_filtro_tipo = QComboBox()
        self.combo_filtro_tipo.addItems([
            "Todos",
            "Ingreso de Equipos",
            "Gestión de Taller",
            "Gestión de Vehículos",
            "Papelera"
        ])
        self.combo_filtro_tipo.setFixedHeight(32)
        self.combo_filtro_tipo.setStyleSheet(estilo_combo)
        self.combo_filtro_tipo.currentTextChanged.connect(
            lambda: self.aplicar_filtros())
        filtros_layout1.addWidget(self.combo_filtro_tipo)

        lbl_usuario = QLabel("Usuario:")
        lbl_usuario.setStyleSheet("color: #37474f;")
        filtros_layout1.addWidget(lbl_usuario)
        self.combo_filtro_usuario = QComboBox()
        self.combo_filtro_usuario.addItem("Todos")
        self.combo_filtro_usuario.setFixedHeight(32)
        self.combo_filtro_usuario.setStyleSheet(estilo_combo)
        self.combo_filtro_usuario.currentTextChanged.connect(
            lambda: self.aplicar_filtros())
        filtros_layout1.addWidget(self.combo_filtro_usuario)

        filtros_layout1.addStretch()
        container_layout.addLayout(filtros_layout1)

        # Filtros (Fila 2: Rango de Fechas)
        filtros_layout2 = QHBoxLayout()

        lbl_fecha = QLabel("📅 Rango de Fechas:")
        lbl_fecha.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        lbl_fecha.setStyleSheet("color: #37474f;")
        filtros_layout2.addWidget(lbl_fecha)

        estilo_date = """
            QDateEdit {
                border: 2px solid #cfd8dc;
                border-radius: 6px;
                padding: 5px;
                background-color: white;
                min-width: 120px;
                color: black;
            }
            QDateEdit:hover {
                border: 2px solid #1976d2;
            }
            QDateEdit::drop-down {
                border: none;
                width: 25px;
            }
        """

        lbl_desde = QLabel("Desde:")
        lbl_desde.setStyleSheet("color: #37474f;")
        filtros_layout2.addWidget(lbl_desde)
        self.date_desde = QDateEdit()
        self.date_desde.setCalendarPopup(True)
        self.date_desde.setDisplayFormat("dd/MM/yyyy")
        self.date_desde. setDate(QDate. currentDate().addDays(-7))
        self.date_desde.setFixedHeight(32)
        self.date_desde.setStyleSheet(estilo_date)
        filtros_layout2.addWidget(self.date_desde)

        lbl_hasta = QLabel("Hasta:")
        lbl_hasta.setStyleSheet("color: #37474f;")
        filtros_layout2.addWidget(lbl_hasta)
        self.date_hasta = QDateEdit()
        self.date_hasta.setCalendarPopup(True)
        self.date_hasta.setDisplayFormat("dd/MM/yyyy")
        self.date_hasta.setDate(QDate.currentDate())
        self.date_hasta.setFixedHeight(32)
        self.date_hasta.setStyleSheet(estilo_date)
        filtros_layout2.addWidget(self.date_hasta)

        btn_buscar = QPushButton("🔍 Buscar")
        btn_buscar.setFixedHeight(32)
        btn_buscar. setCursor(Qt.CursorShape.PointingHandCursor)
        btn_buscar.setStyleSheet("""
            QPushButton {
                background-color:  #1976d2;
                color: white;
                border-radius: 6px;
                padding: 0 20px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #1565c0;
            }
        """)
        btn_buscar.clicked.connect(self.buscar_por_fecha)
        filtros_layout2.addWidget(btn_buscar)

        filtros_layout2.addStretch()
        container_layout.addLayout(filtros_layout2)

        return container_layout

    def crear_botones(self):
        """Botones inferiores"""
        botones_layout = QHBoxLayout()
        botones_layout. setSpacing(12)

        btn_exportar = QPushButton("📄 Exportar a Excel")
        btn_exportar.setFont(QFont("Arial", 11, QFont.Weight.Bold))
        btn_exportar.setFixedHeight(40)
        btn_exportar. setCursor(Qt.CursorShape.PointingHandCursor)
        btn_exportar. setStyleSheet("""
            QPushButton {
                background-color: #388e3c;
                color:  white;
                border-radius:  6px;
                padding:  0 20px;
            }
            QPushButton:hover {
                background-color: #2e7d32;
            }
        """)
        btn_exportar.clicked.connect(self. exportar_excel)
        botones_layout. addWidget(btn_exportar)

        botones_layout.addStretch()

        return botones_layout

    def crear_mensaje_vacio(self):
        """Crea mensaje cuando no hay datos"""
        mensaje_frame = QFrame()
        mensaje_frame.setStyleSheet("""
            QFrame {
                background-color: white;
                border: 2px dashed #cfd8dc;
                border-radius: 10px;
                padding: 40px;
            }
        """)

        mensaje_layout = QVBoxLayout()

        icono = QLabel("📅")
        icono.setFont(QFont("Arial", 48))
        icono.setAlignment(Qt.AlignmentFlag. AlignCenter)
        mensaje_layout.addWidget(icono)

        texto = QLabel("No hay movimientos para mostrar")
        texto.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        texto.setStyleSheet("color: #78909c;")
        texto.setAlignment(Qt.AlignmentFlag.AlignCenter)
        mensaje_layout.addWidget(texto)

        instruccion = QLabel(
            "Seleccione un rango de fechas y haga clic en 'Buscar'")
        instruccion.setFont(QFont("Arial", 11))
        instruccion.setStyleSheet("color: #90a4ae;")
        instruccion.setAlignment(Qt. AlignmentFlag.AlignCenter)
        mensaje_layout.addWidget(instruccion)

        mensaje_frame.setLayout(mensaje_layout)
        self.timeline_layout.addWidget(mensaje_frame)

    def buscar_por_fecha(self):
        """Primera búsqueda: reinicia y trae la primera página."""
        fecha_desde = self.date_desde.date().toPyDate()
        fecha_hasta = self.date_hasta.date().toPyDate()

        if fecha_desde > fecha_hasta:
            QMessageBox.warning(self, "⚠️ Fechas Inválidas",
                "La fecha 'Desde' no puede ser posterior a la fecha 'Hasta'.")
            return

        self.lbl_periodo.setText(
            f"📅 Mostrando movimientos del {fecha_desde.strftime('%d/%m/%Y')} "
            f"al {fecha_hasta.strftime('%d/%m/%Y')}")

        # Guardamos las fechas para reusarlas en "cargar más".
        self._fecha_desde = fecha_desde.isoformat()
        self._fecha_hasta = fecha_hasta.isoformat()

        self.pagina_actual = 0
        self.movimientos_completos = []      # acá acumulamos lo traído
        self.limpiar_timeline()

        self._traer_pagina(primera=True)

    def cargar_mas_movimientos(self):
        """Trae la siguiente página desde el servidor."""
        self.pagina_actual += 1
        self._traer_pagina(primera=False)

    def _traer_pagina(self, primera):
        """Pide una tanda al servidor y la agrega al timeline."""
        offset = self.pagina_actual * self.movimientos_por_pagina

        try:
            tanda = self.api.get("movimientos.php", {
                "fecha_desde": self._fecha_desde,
                "fecha_hasta": self._fecha_hasta,
                "offset": offset,
                "limite": self.movimientos_por_pagina,
            })

            if primera and not tanda:
                self.crear_mensaje_vacio()
                self.btn_cargar_mas.setEnabled(False)
                return

            # Acumulamos y pintamos solo la tanda nueva.
            self.movimientos_completos.extend(tanda)
            self._quitar_stretch_final()
            self.pintar_timeline(tanda)

            # Si la tanda vino con menos de lo pedido, ya no hay más.
            hay_mas = len(tanda) == self.movimientos_por_pagina
            self.btn_cargar_mas.setEnabled(hay_mas)

        except SesionExpirada:
            QMessageBox.warning(self, "Sesión expirada",
                "Tu sesión venció. Cerrá y volvé a iniciar sesión.")
        except ApiError as e:
            QMessageBox.critical(self, "Error", f"Al cargar movimientos:\n{e}")

    def aplicar_filtros(self):
        """Aplica filtros a los movimientos y repinta el timeline."""
        if not self.movimientos_completos:
            return

        # 1. Empezar SIEMPRE desde la lista completa.
        filtrados = self.movimientos_completos.copy()

        # 2. Filtro por texto (número de serie).
        texto = self.input_buscar.text().strip().upper()
        if texto:
            filtrados = [
                m for m in filtrados
                if texto in (m.get('identificador') or '').upper()
            ]

        # 3. Filtro por usuario (si no está en "Todos").
        usuario = self.combo_filtro_usuario.currentText()
        if usuario and usuario != "Todos":
            filtrados = [
                m for m in filtrados
                if str(m.get('usuario', '')) == usuario
            ]

        # 4. (Filtro por tipo: lo dejo comentado hasta definir el mapeo,
        #     ver la nota de abajo.)
        accion = self.combo_filtro_tipo.currentText()
        if accion and accion != "Todos":
            filtrados = [
                m for m in filtrados
                if str(m.get('tipo_accion', '')) == accion
            ]

        # 5. Repintar el timeline con lo filtrado.
        self.limpiar_timeline()
        if not filtrados:
            self.crear_mensaje_vacio()
        else:
            self.pintar_timeline(filtrados)

    def limpiar_filtros(self):
        """Limpia todos los filtros"""
        self. input_buscar.clear()
        self.combo_filtro_tipo.setCurrentIndex(0)
        self.combo_filtro_usuario.setCurrentIndex(0)
        self.date_desde.setDate(QDate.currentDate().addDays(-7))
        self.date_hasta.setDate(QDate.currentDate())

        # Limpiar timeline
        self.limpiar_timeline()
        self.crear_mensaje_vacio()
        self.movimientos_completos = []
        self.lbl_periodo.setText(
            "📅 Seleccione un rango de fechas para cargar movimientos")

    def limpiar_timeline(self):
        """Limpia todos los items del timeline"""
        while self.timeline_layout.count():
            child = self.timeline_layout.takeAt(0)
            if child.widget():
                child. widget().deleteLater()

    def pintar_timeline(self, movimientos):
        """Crea una tarjeta por cada movimiento y la agrega al timeline."""

        # Traducción de los códigos de acción a texto legible + un color.
        estilos_accion = {
            "ENVIADO_A_TALLER":   ("🛠️ Enviado a taller",     "#f57c00"),
            "EGRESO_TALLER":      ("✅ Egresado de taller",    "#388e3c"),
            "ALTA":               ("📥 Alta de equipo",        "#1976d2"),
            "MODIFICACION":       ("✏️ Modificado",            "#7b1fa2"),
            "ENVIADO_A_PAPELERA": ("🗑️ Enviado a papelera",   "#c62828"),
            "RESTAURADO":         ("♻️ Restaurado",            "#00796b"),
        }

        for mov in movimientos:
            accion = mov.get("tipo_accion", "")
            texto_accion, color = estilos_accion.get(
                accion, (accion.replace("_", " ").capitalize(), "#546e7a"))
            print(accion)

            # Tarjeta contenedora
            tarjeta = QFrame()
            tarjeta.setStyleSheet(f"""
                QFrame {{
                    background-color: white;
                    border: 1px solid #cfd8dc;
                    border-left: 5px solid {color};
                    border-radius: 8px;
                }}
            """)
            layout = QVBoxLayout()
            layout.setContentsMargins(15, 10, 15, 10)
            layout.setSpacing(4)

            # Línea 1: acción + fecha
            fila_top = QHBoxLayout()
            lbl_accion = QLabel(texto_accion)
            lbl_accion.setFont(QFont("Arial", 12, QFont.Weight.Bold))
            lbl_accion.setStyleSheet(f"color: {color}; border: none;")
            fila_top.addWidget(lbl_accion)
            fila_top.addStretch()

            lbl_fecha = QLabel(self._formatear_fecha(mov.get("fecha", "")))
            lbl_fecha.setFont(QFont("Arial", 9))
            lbl_fecha.setStyleSheet("color: #90a4ae; border: none;")
            fila_top.addWidget(lbl_fecha)
            layout.addLayout(fila_top)

            # Línea 2: equipo (tipo, marca, modelo, serie)
            

            es_equipo = mov.get('origen', '').lower() == "equipo"
            etiqueta = "Serie" if es_equipo else "Identificación"

            equipo_txt = (
                f"{mov.get('tipo', '')} {mov.get('marca', '')} {mov.get('modelo_equipo', '')} "
                f"— {etiqueta}: {mov.get('identificador', '')}"
                )
            lbl_equipo = QLabel(equipo_txt.strip())
            lbl_equipo.setFont(QFont("Arial", 10, QFont.Weight.Bold))
            lbl_equipo.setStyleSheet("color: #37474f; border: none;")
            layout.addWidget(lbl_equipo)

            # Línea 3: usuario + observaciones
            usuario = mov.get("usuario", "—")
            obs = mov.get("observaciones", "") or "Sin observaciones"
            lbl_detalle = QLabel(f"👤 Usuario {usuario}   ·   {obs}")
            lbl_detalle.setFont(QFont("Arial", 9))
            lbl_detalle.setStyleSheet("color: #78909c; border: none;")
            lbl_detalle.setWordWrap(True)
            layout.addWidget(lbl_detalle)

            tarjeta.setLayout(layout)
            self.timeline_layout.addWidget(tarjeta)

        # Empuja las tarjetas hacia arriba para que no queden centradas.
        self.timeline_layout.addStretch()

    def _formatear_fecha(self, fecha_str):
        """Convierte '2026-07-30 01:20:11' a '30/07/2026 01:20'."""
        try:
            from datetime import datetime
            dt = datetime.strptime(fecha_str, "%Y-%m-%d %H:%M:%S")
            return dt.strftime("%d/%m/%Y %H:%M")
        except (ValueError, TypeError):
            return fecha_str  # si viene en otro formato, lo dejamos como está

    def ver_detalle_movimiento(self, movimiento):
        """Abre el diálogo con detalle completo"""
        DialogoDetalleMovimiento(movimiento, self).exec()

    def exportar_excel(self):
        """Exporta los movimientos a Excel"""
        if not self.movimientos_completos:
            QMessageBox.warning(
                self,
                "⚠️ Sin Datos",
                "No hay movimientos para exportar.\nPrimero realice una búsqueda."
            )
            return

        datos_a_excel = self.movimientos_completos
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
            self.llenar_combo("usuario.php", self.combo_filtro_usuario, "username", incluir_todos=True)

    def _quitar_stretch_final(self):
        count = self.timeline_layout.count()
        if count > 0:
            item = self.timeline_layout.itemAt(count - 1)
            if item is not None and item.widget() is None:
                self.timeline_layout.takeAt(count - 1)

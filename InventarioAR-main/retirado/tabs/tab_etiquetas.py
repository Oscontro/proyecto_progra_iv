import requests
import pandas as pd
import direcciones # type: ignore
from PyQt6.QtWidgets import (
    QMenu, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QFrame, QComboBox, QMessageBox, QCompleter,
    QTextEdit, QScrollArea, QFileDialog
)
from PyQt6.QtCore import Qt, QStringListModel, QUrl
from PyQt6.QtGui import QAction, QFont, QColor, QDesktopServices
from datetime import datetime
from base_tab import ApiTab
from api_client import ApiError, SesionExpirada
import os
import tempfile
from io import BytesIO
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Image, Paragraph, Spacer
from reportlab.graphics.barcode import code128
from reportlab.graphics.shapes import Drawing
from reportlab.graphics import renderPDF


class EtiquetaEquipo:
    
    # Dimensiones de la etiqueta (1/3 de A4)
    ANCHO = 210 * mm
    ALTO = 99 * mm
    MARGEN = 5 * mm
    
    def __init__(self, api, API_BASE_URL: str = None):
        self.api = api
        self.API_BASE_URL = API_BASE_URL
        self.IMG_BASE_URL = direcciones.URL.IMG_BASE_URL
    
    def generar_etiqueta(self, datos: dict, output_path: str, historial: list = None) -> str:
        """
        Genera la etiqueta PDF usando canvas directamente para evitar problemas de anidamiento.
        """
        from reportlab.pdfgen import canvas
        from reportlab.lib.utils import ImageReader
        
        # Guardar datos como atributo para usar en otros métodos
        self.datos = datos
        
        # Calcular altura según historial
        alto_etiqueta = self.ALTO
        if historial:
            alto_etiqueta = self.ALTO + (len(historial[:3]) * 6 * mm) + 15 * mm
        
        # Crear canvas
        c = canvas.Canvas(output_path, pagesize=(self.ANCHO, alto_etiqueta))
        
        # Posición inicial (desde arriba)
        y = alto_etiqueta - self.MARGEN
        
        # ===== TÍTULO =====
        c.setFont('Helvetica-Bold', 14)
        c.setFillColor(colors.HexColor('#1a5276'))
        titulo = f"{datos.get('numero_serie', '')} - {datos.get('modelo_equipo', '')}"
        c.drawString(self.MARGEN + 5, y - 12, titulo)
        y -= 20
        
        # ===== LÍNEA SEPARADORA =====
        c.setStrokeColor(colors.HexColor('#3498db'))
        c.setLineWidth(2)
        c.line(self.MARGEN, y, self.ANCHO - self.MARGEN, y)
        y -= 8
        
        # ===== DATOS DEL EQUIPO (izquierda) =====
        campos = [
            ('N° de Serie:', datos.get('numero_serie', '')),
            ('Tipo:', datos.get('tipo', '')),
            ('Marca:', datos.get('marca', '')),
            ('Modelo:', datos.get('modelo_equipo', '')),
            ('Escala:', datos.get('escala', '')),
            ('Sector:', datos.get('sector', '')),
            ('Estado:', datos.get('estado', '')),
        ]
        
        y_datos = y
        for label, valor in campos:
            c.setFont('Helvetica-Bold', 9)
            c.setFillColor(colors.HexColor('#2c3e50'))
            c.drawString(self.MARGEN + 5, y_datos - 10, label)
            
            c.setFont('Helvetica', 9)
            c.setFillColor(colors.HexColor('#34495e'))
            c.drawString(self.MARGEN + 75, y_datos - 10, str(valor))
            
            y_datos -= 12
        
        # ===== IMAGEN (derecha) =====
        imagen_nombre = self.get_imagen()
        img_x = self.ANCHO - self.MARGEN - 60 * mm
        img_y = y - 55 * mm
        img_width = 55 * mm
        img_height = 55 * mm
        
        imagen_dibujada = False
        if imagen_nombre:
            try:
                ruta_imagenes = self.IMG_BASE_URL  # Carpeta local de imágenes
                ruta_completa = os.path.join(ruta_imagenes, imagen_nombre)
                
                # Verificar si el archivo existe
                if os.path.exists(ruta_completa):
                    c.drawImage(
                        ruta_completa,  # Pasar la ruta directamente, no BytesIO
                        img_x, img_y,
                        width=img_width, height=img_height,
                        preserveAspectRatio=True
                    )
                    imagen_dibujada = True
                else:
                    print(f"Imagen no encontrada: {ruta_completa}")
            except Exception as e:
                print(f"Error al cargar imagen: {e}")
        
        # Placeholder si no hay imagen
        if not imagen_dibujada:
            c.setStrokeColor(colors.HexColor('#bdc3c7'))
            c.setFillColor(colors.HexColor('#ecf0f1'))
            c.rect(img_x, img_y, img_width, img_height, fill=1)
            c.setFillColor(colors.HexColor('#7f8c8d'))
            c.setFont('Helvetica', 10)
            c.drawCentredString(img_x + img_width/2, img_y + img_height/2, "Sin imagen")
        
        # Actualizar Y después de datos e imagen
        y = min(y_datos, img_y) - 5
        
        # ===== HISTORIAL =====
        if historial:
            y -= 5
            c.setFont('Helvetica-Bold', 9)
            c.setFillColor(colors.HexColor('#1a5276'))
            c.drawString(self.MARGEN + 5, y, "Historial:")
            y -= 12
            
            c.setFont('Helvetica', 7)
            c.setFillColor(colors.HexColor('#5d6d7e'))
            
            for entrada in historial[:3]:
                fecha = entrada.get('fecha_evento', '')
                usuario = entrada.get('nombre', '')
                accion = entrada.get('observaciones', '')
                texto = f"• {fecha} - {usuario} - {accion}"
                
                # Truncar si es muy largo
                if len(texto) > 120:
                    texto = texto[:117] + "..."
                
                c.drawString(self.MARGEN + 10, y, texto)
                y -= 10
        
        # ===== CÓDIGO DE BARRAS =====
        y -= 5
        barcode = code128.Code128(
            datos.get('numero_serie', ''),
            barWidth=0.5 * mm,
            barHeight=12 * mm,
            humanReadable=True
        )
        
        # Centrar código de barras
        barcode_width = barcode.width
        barcode_x = (self.ANCHO - barcode_width) / 2
        barcode.drawOn(c, barcode_x, self.MARGEN + 3)
        
        # Guardar
        c.save()
        
        return output_path
    
    def get_imagen(self):
        """Obtiene el nombre de la imagen desde la API basándose en el modelo del equipo."""
        modelo = self.datos.get('modelo_equipo', "")
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
            QMessageBox.critical(self, "Error", f"No se pudo cargar la imagen:\n{e}")
            return None


class DialogoVistaPrevia:
    """
    Clase auxiliar para mostrar vista previa de la etiqueta en PyQt6.
    """
    @staticmethod
    def mostrar_y_abrir_pdf(pdf_path: str, parent=None):
        """
        Muestra un mensaje y abre el PDF generado.
        
        Args:
            pdf_path: Ruta del archivo PDF
            parent: Widget padre para el diálogo
        """
        msg = QMessageBox(parent)
        msg.setIcon(QMessageBox.Icon.Information)
        msg.setWindowTitle("Etiqueta Generada")
        msg.setText(f"La etiqueta se ha generado correctamente.")
        msg.setInformativeText("¿Desea abrir el archivo PDF?")
        msg.setStandardButtons(
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if msg.exec() == QMessageBox.StandardButton.Yes:
            QDesktopServices.openUrl(QUrl.fromLocalFile(pdf_path))


# ═══════════════════════════════════════════════════════════
# PESTAÑA PRINCIPAL: ETIQUETAS (FICHAS PDF) - COMPACTA
# ═══════════════════════════════════════════════════════════

class EtiquetasTab(ApiTab):
    """Pestaña de generación de fichas técnicas PDF con código de barras"""

    def __init__(self, api):
        super().__init__(api)
        self.api = api
        self.equipos_disponibles = []  # Lista de equipos del inventario
        self.equipo_seleccionado = None
        self.historial = {}  # Inicializar historial vacío
        self.API_BASE_URL = direcciones.URL.API_BASE_URL  # URL base de la API
        self.crear_interfaz()
        self.cargar_equipos_inventario()
        
    def crear_interfaz(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(12)

        # Header
        header = QLabel("🎫 ETIQUETAS")
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

        # Búsqueda COMPACTA en una sola fila
        busqueda_layout = self.crear_busqueda_compacta()
        layout.addLayout(busqueda_layout)

        # Datos del equipo seleccionado (MÁS ESPACIO)
        self.crear_datos_equipo()
        layout.addWidget(self.datos_frame, 1)

        # Botón generar
        self.btn_generar = QPushButton("📄 Generar Ficha Técnica (PDF)")
        self.btn_generar.setEnabled(False)
        self.btn_generar.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        self.btn_generar.setFixedHeight(50)
        self.btn_generar.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_generar.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #c62828, stop:1 #e53935);
                color: white;
                border-radius: 8px;
                font-weight: bold;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #b71c1c, stop:1 #c62828);
            }
            QPushButton:disabled {
                background-color: #cfd8dc;
                color: #90a4ae;
            }
        """)
        self.btn_generar.clicked.connect(self.generar_pdf)
        layout.addWidget(self.btn_generar)

        
        
        self.setLayout(layout)

    def crear_busqueda_compacta(self):
        """Crea la sección de búsqueda COMPACTA"""
        busqueda_layout = QVBoxLayout()
        busqueda_layout.setSpacing(8)

        # Título
        lbl_titulo = QLabel("🔍 Buscar Equipo por N° de Serie")
        lbl_titulo.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        lbl_titulo.setStyleSheet("color: #1976d2;")
        lbl_titulo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        busqueda_layout.addWidget(lbl_titulo)

        # Frame compacto
        busqueda_frame = QFrame()
        busqueda_frame.setStyleSheet("""
            QFrame {
                background-color: white;
                border-radius: 8px;
                border: 2px solid #cfd8dc;
                padding: 12px;
            }
        """)

        frame_layout = QHBoxLayout()
        frame_layout.setSpacing(10)

        # Espaciador izquierdo para centrar
        frame_layout.addStretch(1)

        # Input directo
        lbl_input = QLabel("📝 Escribir:")
        lbl_input.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        lbl_input.setStyleSheet("color: #37474f;")
        frame_layout.addWidget(lbl_input)

        self.input_serie = QLineEdit()
        self.input_serie.setPlaceholderText("Ej: ABC123")
        self.input_serie.setFixedHeight(38)
        self.input_serie.setFixedWidth(350)
        self.input_serie.setStyleSheet("""
            QLineEdit {
                border: 2px solid #cfd8dc;
                border-radius: 6px;
                padding: 8px;
                font-size: 11pt;
                background-color: #fafafa;
                color: black;
            }
            QLineEdit:focus {
                border: 2px solid #1976d2;
                background-color: white;
            }
        """)
        self.input_serie.returnPressed.connect(self.buscar_por_serie)
        frame_layout.addWidget(self.input_serie)

        btn_buscar = QPushButton("🔍 Buscar")
        btn_buscar.setFixedSize(100, 38)
        btn_buscar.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_buscar.setStyleSheet("""
            QPushButton {
                background-color: #1976d2;
                color: white;
                border-radius: 6px;
                font-weight: bold;
                font-size: 10pt;
            }
            QPushButton:hover {
                background-color: #1565c0;
            }
        """)
        btn_buscar.clicked.connect(self.buscar_por_serie)
        frame_layout.addWidget(btn_buscar)

        # Espaciador derecho para centrar
        frame_layout.addStretch(1)

        busqueda_frame.setLayout(frame_layout)
        busqueda_layout.addWidget(busqueda_frame)

        # ComboBox oculto (se mantiene para no romper código fuente)
        self.combo_equipos = QComboBox()
        self.combo_equipos.setVisible(False)
        self.completer = QCompleter()
        self.completer.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        self.completer.setFilterMode(Qt.MatchFlag.MatchContains)
        self.combo_equipos.setCompleter(self.completer)
        self.combo_equipos.currentTextChanged.connect(self.seleccionar_equipo)

        return busqueda_layout

    def crear_datos_equipo(self):
        """Crea el recuadro de datos del equipo (MÁS GRANDE)"""
        self.datos_frame = QFrame()
        self.datos_frame.setStyleSheet("""
            QFrame {
                background-color: white;
                border-radius: 10px;
                border: 2px solid #cfd8dc;
            }
        """)

        datos_layout = QVBoxLayout()
        datos_layout.setContentsMargins(20, 15, 20, 15)
        datos_layout.setSpacing(12)

        # Título más compacto
        titulo = QLabel("📋 Datos del Equipo Seleccionado")
        titulo.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        titulo.setStyleSheet("color: #1976d2;")
        titulo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        datos_layout.addWidget(titulo)

        # Scroll area para los datos
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setStyleSheet("""
            QScrollArea {
                background-color: transparent;
                border: none;
            }
        """)

        self.contenido_datos = QWidget()
        self.contenido_datos.setStyleSheet("background-color: white;")
        self.contenido_layout = QVBoxLayout()
        self.contenido_layout.setSpacing(10)

        # Mensaje inicial
        self.crear_mensaje_vacio()

        self.contenido_datos.setLayout(self.contenido_layout)
        scroll.setWidget(self.contenido_datos)

        datos_layout.addWidget(scroll)

        self.datos_frame.setLayout(datos_layout)

    def crear_mensaje_vacio(self):
        """Crea el mensaje cuando no hay equipo seleccionado"""
        mensaje_frame = QFrame()
        mensaje_frame.setStyleSheet("""
            QFrame {
                background-color: #f5f5f5;
                border: 2px dashed #cfd8dc;
                border-radius: 8px;
                padding: 30px;
            }
        """)

        mensaje_layout = QVBoxLayout()

        icono = QLabel("📦")
        icono.setFont(QFont("Arial", 42))
        icono.setAlignment(Qt.AlignmentFlag.AlignCenter)
        mensaje_layout.addWidget(icono)

        texto = QLabel("Ningún equipo seleccionado")
        texto.setFont(QFont("Arial", 13, QFont.Weight.Bold))
        texto.setStyleSheet("color: #78909c;")
        texto.setAlignment(Qt.AlignmentFlag.AlignCenter)
        mensaje_layout.addWidget(texto)

        instruccion = QLabel(
            "Busque un equipo por N° de Serie o selecciónelo del inventario")
        instruccion.setFont(QFont("Arial", 10))
        instruccion.setStyleSheet("color: #90a4ae;")
        instruccion.setAlignment(Qt.AlignmentFlag.AlignCenter)
        instruccion.setWordWrap(True)
        mensaje_layout.addWidget(instruccion)

        mensaje_frame.setLayout(mensaje_layout)
        self.contenido_layout.addWidget(mensaje_frame)

    def cargar_equipos_inventario(self):
        """Carga los equipos del inventario (conectar con BD real)"""
        self.equipos_disponibles = []  # VACÍO por defecto

        # Llenar combo
        items = [""]  # Item vacío inicial
        for equipo in self.equipos_disponibles:
            items.append(
                f"{equipo['numero_serie']} - {equipo['modelo_equipo']} ({equipo['estado']})")

        self.combo_equipos.addItems(items)

        # Configurar autocompletado
        model = QStringListModel(items)
        self.completer.setModel(model)

    def buscar_por_serie(self):
        """Busca un equipo por N° de Serie"""
        serie = self.input_serie.text().strip().upper()

        if not serie:
            QMessageBox.warning(
                self,
                "⚠️ Campo Vacío",
                "Por favor ingrese un N° de Serie para buscar."
            )
            return
            
        # Buscar equipo en DB
        try:
            equipo = self.api.get("equipo_etiqueta.php", {"numero_serie": serie})
            
            if equipo:
                self.equipo_seleccionado = equipo.get("data")
                self.historial_ultimos_tres(serie)  # Cargar historial para el equipo
                self.mostrar_datos_equipo(self.equipo_seleccionado)
                self.btn_generar.setEnabled(True)
            else:
                QMessageBox.information(
                    self,
                    "No Encontrado",
                    f"No se encontró ningún equipo con N° de Serie: {serie}"
                )
                self.limpiar_datos()
        except SesionExpirada:
            QMessageBox.warning(self, "Sesión expirada",
                "Tu sesión venció. Cerrá y volvé a iniciar sesión.")
        except ApiError as e:
            QMessageBox.critical(self, "Error", f"Obtener equipo:\n{e}")
            
    def historial_ultimos_tres(self, serie):
        """Obtiene el historial de los últimos 3 eventos del equipo"""
        try:
            self.historial = self.api.get("historial_ultimos_tres.php", {"numero_serie": serie})
            if self.historial:
                return self.historial.get("data", [])
            else:
                self.historial = {"data": []}
                return []
        except SesionExpirada:
            QMessageBox.warning(self, "Sesión expirada",
                "Tu sesión venció. Cerrá y volvé a iniciar sesión.")
            self.historial = {"data": []}
            return []
        except ApiError as e:
            QMessageBox.critical(self, "Error", f"Obtener historial:\n{e}")
            self.historial = {"data": []}
            return []

    def seleccionar_equipo(self, texto):
        """Maneja la selección del ComboBox"""
        if not texto or texto == "":
            self.limpiar_datos()
            return

        # Extraer N° de Serie del formato "Serie - Modelo"
        if " - " in texto:
            serie = texto.split(" - ")[0].strip()

            # Buscar equipo
            for equipo in self.equipos_disponibles:
                if equipo['numero_serie'] == serie:
                    self.equipo_seleccionado = equipo
                    self.historial_ultimos_tres(serie)
                    self.mostrar_datos_equipo(equipo)
                    self.btn_generar.setEnabled(True)
                    return

    def mostrar_datos_equipo(self, equipo):
        """Muestra los datos del equipo en el recuadro"""
        # Limpiar contenido anterior
        while self.contenido_layout.count():
            child = self.contenido_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

        # Frame con datos principales
        datos_frame = QFrame()
        datos_frame.setStyleSheet("""
            QFrame {
                background-color: #e3f2fd;
                border: 2px solid #1976d2;
                border-radius: 8px;
                padding: 12px;
            }
        """)

        datos_layout = QVBoxLayout()
        datos_layout.setSpacing(6)

        # Título del equipo
        titulo_equipo = QLabel(f"📻 {equipo['numero_serie']} - {equipo['modelo_equipo']}")
        titulo_equipo.setFont(QFont("Arial", 13, QFont.Weight.Bold))
        titulo_equipo.setStyleSheet("color: #0d47a1;")
        datos_layout.addWidget(titulo_equipo)

        # Datos en formato HTML
        datos_html = f"""
        <table style='width: 100%; color: #1976d2; font-size: 10pt;'>
            <tr><td style='padding: 3px;'><b>N° de Serie:</b></td><td style='padding: 3px;'>{equipo['numero_serie']}</td></tr>
            <tr><td style='padding: 3px;'><b>Tipo:</b></td><td style='padding: 3px;'>{equipo['tipo']}</td></tr>
            <tr><td style='padding: 3px;'><b>Marca:</b></td><td style='padding: 3px;'>{equipo['marca']}</td></tr>
            <tr><td style='padding: 3px;'><b>Modelo:</b></td><td style='padding: 3px;'>{equipo['modelo_equipo']}</td></tr>
            <tr><td style='padding: 3px;'><b>Escala:</b></td><td style='padding: 3px;'>{equipo['escala']}</td></tr>
            <tr><td style='padding: 3px;'><b>Sector:</b></td><td style='padding: 3px;'>{equipo['sector']}</td></tr>
            <tr><td style='padding: 3px;'><b>Estado:</b></td><td style='padding: 3px;'><span style='color: #4caf50; font-weight: bold;'>{equipo['estado']}</span></td></tr>
            <tr><td style='padding: 3px;'><b>Usuario:</b></td><td style='padding: 3px;'>{equipo.get('usuario_modificacion', 'N/A')}</td></tr>
        </table>
        """

        lbl_datos = QLabel(datos_html)
        lbl_datos.setWordWrap(True)
        datos_layout.addWidget(lbl_datos)

        datos_frame.setLayout(datos_layout)
        self.contenido_layout.addWidget(datos_frame)

        # Observaciones
        if equipo.get('observaciones'):
            obs_frame = QFrame()
            obs_frame.setStyleSheet("""
                QFrame {
                    background-color: #fff3e0;
                    border: 2px solid #ff9800;
                    border-radius: 8px;
                    padding: 10px;
                }
            """)

            obs_layout = QVBoxLayout()
            obs_layout.setSpacing(4)

            lbl_obs_titulo = QLabel("📝 Observaciones:")
            lbl_obs_titulo.setFont(QFont("Arial", 10, QFont.Weight.Bold))
            lbl_obs_titulo.setStyleSheet("color: #e65100;")
            obs_layout.addWidget(lbl_obs_titulo)

            lbl_obs = QLabel(equipo['observaciones'])
            lbl_obs.setFont(QFont("Arial", 9))
            lbl_obs.setStyleSheet("color: #f57c00;")
            lbl_obs.setWordWrap(True)
            obs_layout.addWidget(lbl_obs)

            obs_frame.setLayout(obs_layout)
            self.contenido_layout.addWidget(obs_frame)

        # Historial
        historial_data = self.historial.get('data', [])
        if historial_data:
            historial_frame = QFrame()
            historial_frame.setStyleSheet("""
                QFrame {
                    background-color: #f5f5f5;
                    border: 2px solid #cfd8dc;
                    border-radius: 8px;
                    padding: 10px;
                }
            """)

            historial_layout = QVBoxLayout()
            historial_layout.setSpacing(4)

            lbl_hist_titulo = QLabel("📜 Historial:")
            lbl_hist_titulo.setFont(QFont("Arial", 10, QFont.Weight.Bold))
            lbl_hist_titulo.setStyleSheet("color: #37474f;")
            historial_layout.addWidget(lbl_hist_titulo)

            for evento in historial_data:
                lbl_evento = QLabel(f"• {evento['fecha_evento']} - {evento['nombre']} - {evento['observaciones']}")
                lbl_evento.setFont(QFont("Arial", 9))
                lbl_evento.setStyleSheet("color: #546e7a;")
                lbl_evento.setWordWrap(True)
                historial_layout.addWidget(lbl_evento)

            historial_frame.setLayout(historial_layout)
            self.contenido_layout.addWidget(historial_frame)

        self.contenido_layout.addStretch()

    def limpiar_datos(self):
        """Limpia los datos mostrados"""
        while self.contenido_layout.count():
            child = self.contenido_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

        self.crear_mensaje_vacio()
        self.equipo_seleccionado = None
        self.historial = {"data": []}
        self.btn_generar.setEnabled(False)
        
    def generar_pdf(self):
        """Genera la etiqueta PDF del equipo seleccionado"""
        if not self.equipo_seleccionado:
            QMessageBox.warning(
                self,
                "⚠️ Sin Equipo",
                "Por favor seleccione un equipo antes de generar la etiqueta."
            )
            return
        
        # Preguntar dónde guardar el archivo
        numero_serie = self.equipo_seleccionado.get('numero_serie', 'equipo')
        nombre_archivo = f"etiqueta_{numero_serie}.pdf"
        
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Guardar Etiqueta PDF",
            nombre_archivo,
            "Archivos PDF (*.pdf)"
        )
        
        if not file_path:
            return  # Usuario canceló
        
        try:
            # Configurar el generador
            generador = EtiquetaEquipo(self.api, self.API_BASE_URL)
        
            # Datos del equipo
            datos = self.equipo_seleccionado
        
            # Historial del equipo
            historial = self.historial.get('data', [])
        
            # Generar etiqueta
            pdf_path = generador.generar_etiqueta(
                datos=datos,
                output_path=file_path,
                historial=historial
            )
        
            # Mostrar diálogo de éxito y preguntar si abrir
            DialogoVistaPrevia.mostrar_y_abrir_pdf(pdf_path, self)
            
        except Exception as e:
            QMessageBox.critical(
                self,
                "❌ Error",
                f"Error al generar la etiqueta:\n{str(e)}"
            )
            
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
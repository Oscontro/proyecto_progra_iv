"""
Generador de Etiquetas de Equipos en PDF
Tamaño: 1/3 de hoja A4 (210mm x 99mm aproximadamente)
Contenido: Tabla de datos (izquierda), Imagen (derecha), Código de barras Code128 (abajo)
"""

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
import requests
from PyQt6.QtWidgets import QMessageBox
from PyQt6.QtCore import QUrl
from PyQt6.QtGui import QDesktopServices


class EtiquetaEquipo:
    """
    Genera etiquetas PDF para equipos del inventario.
    
    Tamaño de etiqueta: 1/3 de A4 (210mm x 99mm)
    Layout:
        - Izquierda: Tabla con datos del equipo
        - Derecha: Imagen del equipo
        - Abajo: Código de barras Code128 con número de serie
    """
    
    # Dimensiones de la etiqueta (1/3 de A4)
    ANCHO = 210 * mm
    ALTO = 99 * mm
    MARGEN = 5 * mm
    
    def __init__(self, api_base_url: str = None):
        """
        Inicializa el generador de etiquetas.
        
        Args:
            api_base_url: URL base de la API para obtener imágenes
        """
        self.api_base_url = api_base_url
        self.styles = getSampleStyleSheet()
        self._configurar_estilos()
    
    def _configurar_estilos(self):
        """Configura los estilos de texto para la etiqueta."""
        self.styles.add(ParagraphStyle(
            name='TituloEtiqueta',
            fontSize=12,
            fontName='Helvetica-Bold',
            spaceAfter=3 * mm,
            textColor=colors.HexColor('#1a5276')
        ))
        self.styles.add(ParagraphStyle(
            name='DatoLabel',
            fontSize=9,
            fontName='Helvetica-Bold',
            textColor=colors.HexColor('#2c3e50')
        ))
        self.styles.add(ParagraphStyle(
            name='DatoValor',
            fontSize=9,
            fontName='Helvetica',
            textColor=colors.HexColor('#34495e')
        ))
        self.styles.add(ParagraphStyle(
            name='HistorialTitulo',
            fontSize=9,
            fontName='Helvetica-Bold',
            textColor=colors.HexColor('#1a5276'),
            spaceBefore=2 * mm,
            spaceAfter=1 * mm
        ))
        self.styles.add(ParagraphStyle(
            name='HistorialItem',
            fontSize=7,
            fontName='Helvetica',
            textColor=colors.HexColor('#5d6d7e'),
            leftIndent=3 * mm,
            spaceBefore=0.5 * mm
        ))
    
    def _obtener_imagen(self, imagen_id: str = None, imagen_path: str = None) -> Image:
        """
        Obtiene la imagen del equipo desde la API o desde una ruta local.
        
        Args:
            imagen_id: ID de la imagen para obtener desde la API
            imagen_path: Ruta local de la imagen (alternativa a la API)
            
        Returns:
            Objeto Image de ReportLab o None si no se encuentra
        """
        img_width = 55 * mm
        img_height = 55 * mm
        
        try:
            if imagen_path and os.path.exists(imagen_path):
                # Cargar desde archivo local
                return Image(imagen_path, width=img_width, height=img_height)
            
            elif imagen_id and self.api_base_url:
                # Obtener desde la API
                url = f"{self.api_base_url}/imagenes/{imagen_id}"
                response = requests.get(url, timeout=10)
                
                if response.status_code == 200:
                    img_data = BytesIO(response.content)
                    return Image(img_data, width=img_width, height=img_height)
            
            # Si no hay imagen, crear un placeholder
            return self._crear_placeholder_imagen(img_width, img_height)
            
        except Exception as e:
            print(f"Error al obtener imagen: {e}")
            return self._crear_placeholder_imagen(img_width, img_height)
    
    def _crear_placeholder_imagen(self, width, height) -> Table:
        """Crea un placeholder cuando no hay imagen disponible."""
        placeholder_data = [['Sin imagen']]
        placeholder = Table(placeholder_data, colWidths=[width], rowHeights=[height])
        placeholder.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('BOX', (0, 0), (-1, -1), 1, colors.HexColor('#bdc3c7')),
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#ecf0f1')),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.HexColor('#7f8c8d')),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
        ]))
        return placeholder
    
    def _crear_historial(self, historial: list) -> Table:
        """
        Crea la sección de historial del equipo.
        
        Args:
            historial: Lista de diccionarios con el historial:
                - fecha: str (fecha y hora del evento)
                - usuario: str (usuario que realizó la acción)
                - accion: str (descripción de la acción)
                
        Returns:
            Table de ReportLab con el historial formateado
        """
        if not historial:
            return None
        
        # Título del historial
        historial_data = []
        
        # Agregar cada entrada del historial
        for entrada in historial[:5]:  # Limitar a 5 entradas para que quepa
            fecha = entrada.get('fecha', '')
            usuario = entrada.get('usuario', '')
            accion = entrada.get('accion', '')
            
            texto = f"• {fecha} - {usuario} - {accion}"
            historial_data.append([Paragraph(texto, self.styles['HistorialItem'])])
        
        if not historial_data:
            return None
        
        # Crear tabla del historial
        tabla = Table(
            historial_data,
            colWidths=[195 * mm],
            rowHeights=[5 * mm] * len(historial_data)
        )
        
        tabla.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('TOPPADDING', (0, 0), (-1, -1), 0),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 0),
            ('LEFTPADDING', (0, 0), (-1, -1), 2),
        ]))
        
        return tabla

    def _crear_codigo_barras(self, numero_serie: str) -> Drawing:
        """
        Crea el código de barras Code128 con el número de serie.
        
        Args:
            numero_serie: Número de serie a codificar
            
        Returns:
            Drawing con el código de barras
        """
        barcode_width = 180 * mm
        barcode_height = 20 * mm
        
        # Crear el código de barras
        barcode = code128.Code128(
            numero_serie,
            barWidth=0.5 * mm,
            barHeight=15 * mm,
            humanReadable=True
        )
        
        # Crear el Drawing que contiene el código de barras
        drawing = Drawing(barcode_width, barcode_height)
        
        # Centrar el código de barras
        barcode_actual_width = barcode.width
        x_pos = (barcode_width - barcode_actual_width) / 2
        
        barcode.x = x_pos
        barcode.y = 2 * mm
        drawing.add(barcode)
        
        return drawing
    
    def _crear_tabla_datos(self, datos: dict) -> Table:
        """
        Crea la tabla con los datos del equipo.
        
        Args:
            datos: Diccionario con los datos del equipo
            
        Returns:
            Table de ReportLab con los datos formateados
        """
        # Definir los campos a mostrar
        campos = [
            ('N° de Serie:', datos.get('numero_serie', '')),
            ('Tipo:', datos.get('tipo', '')),
            ('Marca:', datos.get('marca', '')),
            ('Modelo:', datos.get('modelo', '')),
            ('Escala:', datos.get('escala', '')),
            ('Sector:', datos.get('sector', '')),
            ('Estado:', datos.get('estado', '')),
        ]
        
        # Crear datos de la tabla
        table_data = []
        for label, valor in campos:
            table_data.append([
                Paragraph(label, self.styles['DatoLabel']),
                Paragraph(str(valor), self.styles['DatoValor'])
            ])
        
        # Crear la tabla
        tabla = Table(
            table_data,
            colWidths=[30 * mm, 65 * mm],
            rowHeights=[8 * mm] * len(campos)
        )
        
        # Estilo de la tabla
        tabla.setStyle(TableStyle([
            ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
            ('ALIGN', (1, 0), (1, -1), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('TOPPADDING', (0, 0), (-1, -1), 1),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 1),
            ('LEFTPADDING', (0, 0), (-1, -1), 2),
            ('RIGHTPADDING', (0, 0), (-1, -1), 2),
            ('LINEBELOW', (0, 0), (-1, -2), 0.5, colors.HexColor('#d5dbdb')),
            ('BOX', (0, 0), (-1, -1), 1, colors.HexColor('#3498db')),
            ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#ebf5fb')),
        ]))
        
        return tabla
    
    def generar_etiqueta(
        self,
        datos: dict,
        output_path: str,
        imagen_id: str = None,
        imagen_path: str = None,
        historial: list = None
    ) -> str:
        """
        Genera la etiqueta PDF completa.
        
        Args:
            datos: Diccionario con los datos del equipo:
                - numero_serie: str
                - tipo: str
                - marca: str
                - modelo: str
                - escala: str
                - sector: str
                - estado: str
            output_path: Ruta donde guardar el PDF
            imagen_id: ID de la imagen para obtener desde la API
            imagen_path: Ruta local de la imagen (alternativa)
            historial: Lista de diccionarios con el historial:
                - fecha: str
                - usuario: str
                - accion: str
            
        Returns:
            Ruta del archivo PDF generado
        """
        # Ajustar altura si hay historial
        alto_etiqueta = self.ALTO
        if historial:
            alto_etiqueta = self.ALTO + (len(historial[:5]) * 5 * mm) + 10 * mm
        
        # Crear el documento PDF
        doc = SimpleDocTemplate(
            output_path,
            pagesize=(self.ANCHO, alto_etiqueta),
            leftMargin=self.MARGEN,
            rightMargin=self.MARGEN,
            topMargin=self.MARGEN,
            bottomMargin=self.MARGEN
        )
        
        elements = []
        
        # Título
        titulo = f"{datos.get('numero_serie', '')} - {datos.get('modelo', '')}"
        elements.append(Paragraph(titulo, self.styles['TituloEtiqueta']))
        elements.append(Spacer(1, 2 * mm))
        
        # Crear tabla de datos e imagen
        tabla_datos = self._crear_tabla_datos(datos)
        imagen = self._obtener_imagen(imagen_id, imagen_path)
        
        # Crear tabla contenedora para datos + imagen lado a lado
        contenedor_data = [[tabla_datos, imagen]]
        contenedor = Table(
            contenedor_data,
            colWidths=[100 * mm, 60 * mm]
        )
        contenedor.setStyle(TableStyle([
            ('ALIGN', (0, 0), (0, 0), 'LEFT'),
            ('ALIGN', (1, 0), (1, 0), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ]))
        
        elements.append(contenedor)
        
        # Historial (si existe)
        if historial:
            elements.append(Spacer(1, 2 * mm))
            
            # Título de historial
            titulo_historial = Paragraph("📋 Historial:", self.styles['HistorialTitulo'])
            elements.append(titulo_historial)
            
            # Tabla de historial
            tabla_historial = self._crear_historial(historial)
            if tabla_historial:
                elements.append(tabla_historial)
        
        elements.append(Spacer(1, 3 * mm))
        
        # Código de barras
        codigo_barras = self._crear_codigo_barras(datos.get('numero_serie', ''))
        elements.append(codigo_barras)
        
        # Generar el PDF
        doc.build(elements)
        
        return output_path
    
    def generar_multiples_etiquetas(
        self,
        lista_equipos: list,
        output_path: str,
        obtener_imagen_func=None
    ) -> str:
        """
        Genera un PDF con múltiples etiquetas (3 por página A4).
        
        Args:
            lista_equipos: Lista de diccionarios con datos de equipos
            output_path: Ruta donde guardar el PDF
            obtener_imagen_func: Función que recibe datos del equipo y retorna la ruta de imagen
            
        Returns:
            Ruta del archivo PDF generado
        """
        from reportlab.lib.pagesizes import A4
        
        # Para múltiples etiquetas, crear PDFs individuales y combinarlos
        # o usar un enfoque diferente con canvas directo
        
        from reportlab.pdfgen import canvas
        
        c = canvas.Canvas(output_path, pagesize=A4)
        page_width, page_height = A4
        
        etiquetas_por_pagina = 3
        etiqueta_height = page_height / etiquetas_por_pagina
        
        for i, equipo in enumerate(lista_equipos):
            # Calcular posición en la página
            pos_en_pagina = i % etiquetas_por_pagina
            
            if i > 0 and pos_en_pagina == 0:
                c.showPage()
            
            # Posición Y (de arriba hacia abajo)
            y_base = page_height - (pos_en_pagina + 1) * etiqueta_height
            
            # Dibujar la etiqueta en esta posición
            self._dibujar_etiqueta_en_canvas(
                c, equipo, 
                x=0, y=y_base,
                width=page_width, height=etiqueta_height,
                obtener_imagen_func=obtener_imagen_func
            )
            
            # Línea separadora
            if pos_en_pagina < etiquetas_por_pagina - 1:
                c.setStrokeColor(colors.HexColor('#bdc3c7'))
                c.setDash(3, 3)
                c.line(10, y_base, page_width - 10, y_base)
                c.setDash()
        
        c.save()
        return output_path
    
    def _dibujar_etiqueta_en_canvas(
        self, 
        canvas_obj, 
        datos: dict,
        x: float, 
        y: float, 
        width: float, 
        height: float,
        obtener_imagen_func=None
    ):
        """
        Dibuja una etiqueta individual en el canvas.
        """
        margen = 10
        
        # Título
        canvas_obj.setFont('Helvetica-Bold', 12)
        canvas_obj.setFillColor(colors.HexColor('#1a5276'))
        titulo = f"{datos.get('numero_serie', '')} - {datos.get('modelo', '')}"
        canvas_obj.drawString(x + margen, y + height - 20, titulo)
        
        # Datos del equipo
        campos = [
            ('N° de Serie:', datos.get('numero_serie', '')),
            ('Tipo:', datos.get('tipo', '')),
            ('Marca:', datos.get('marca', '')),
            ('Modelo:', datos.get('modelo', '')),
            ('Escala:', datos.get('escala', '')),
            ('Sector:', datos.get('sector', '')),
            ('Estado:', datos.get('estado', '')),
        ]
        
        y_texto = y + height - 40
        for label, valor in campos:
            canvas_obj.setFont('Helvetica-Bold', 8)
            canvas_obj.setFillColor(colors.HexColor('#2c3e50'))
            canvas_obj.drawString(x + margen, y_texto, label)
            
            canvas_obj.setFont('Helvetica', 8)
            canvas_obj.setFillColor(colors.HexColor('#34495e'))
            canvas_obj.drawString(x + margen + 60, y_texto, str(valor))
            
            y_texto -= 12
        
        # Imagen (si está disponible)
        if obtener_imagen_func:
            imagen_path = obtener_imagen_func(datos)
            if imagen_path and os.path.exists(imagen_path):
                try:
                    canvas_obj.drawImage(
                        imagen_path,
                        x + width - 70 - margen,
                        y + height - 90,
                        width=60,
                        height=60,
                        preserveAspectRatio=True
                    )
                except Exception as e:
                    print(f"Error al dibujar imagen: {e}")
        
        # Código de barras
        barcode = code128.Code128(
            datos.get('numero_serie', ''),
            barWidth=0.4 * mm,
            barHeight=12 * mm,
            humanReadable=True
        )
        barcode.drawOn(canvas_obj, x + margen + 30, y + 10)


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


# Ejemplo de uso
if __name__ == "__main__":
    # Datos de ejemplo (como los de tu captura)
    datos_equipo = {
        'numero_serie': '987654321',
        'tipo': 'Base HF',
        'marca': 'EIFFEL',
        'modelo': 'COLINEAL DE TUBO',
        'escala': 'BRC',
        'sector': 'OPERACIONES',
        'estado': 'EN STOCK',
    }
    
    # Historial de ejemplo (como en tu captura)
    historial_equipo = [
        {
            'fecha': '2026-02-14 21:19:38',
            'usuario': 'Administrador',
            'accion': 'Sector cambiado de "CARGAS" a "OPERACIONES"'
        },
        {
            'fecha': '2026-02-14 21:19:29',
            'usuario': 'Administrador',
            'accion': 'Equipo restaurado desde la papelera'
        },
        {
            'fecha': '2026-02-14 04:00:17',
            'usuario': 'Administrador',
            'accion': 'Equipo enviado a la papelera'
        },
    ]
    
    # Crear generador
    generador = EtiquetaEquipo(api_base_url="http://tu-api.com/api")
    
    # Generar etiqueta individual con historial
    output = generador.generar_etiqueta(
        datos=datos_equipo,
        output_path="etiqueta_equipo.pdf",
        imagen_path="ruta/a/imagen.jpg",  # O usar imagen_id para la API
        historial=historial_equipo
    )
    
    print(f"Etiqueta generada: {output}")
    
    # Ejemplo de múltiples etiquetas
    lista_equipos = [datos_equipo, datos_equipo, datos_equipo]  # 3 equipos de ejemplo
    
    output_multiple = generador.generar_multiples_etiquetas(
        lista_equipos=lista_equipos,
        output_path="etiquetas_multiple.pdf"
    )
    
    print(f"Etiquetas múltiples generadas: {output_multiple}")

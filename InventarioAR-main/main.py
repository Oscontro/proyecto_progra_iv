"""
Sistema de Inventario de Equipos de Radio
Versión: 1.0.1
Fecha: 2025-12-15
Desarrollador: Lucas E Goitea Juarez
"""

import sys
import os
from pathlib import Path
import requests
import pandas as pd
import keyring
from requests import api
import direcciones
from api_client import ApiClient, ApiError
from keyring.errors import PasswordDeleteError
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QLineEdit, QDialog, QTabWidget, QMessageBox,
    QFrame, QCheckBox
)
from PyQt6.QtCore import Qt, QSettings
from PyQt6.QtGui import QFont, QIcon, QPixmap

from tabs.tab_ingreso_equipos import IngresoEquiposTab
from tabs.tab_inventario import InventarioTab
from tabs.tab_taller import TallerTab
from tabs.tab_repuestos import StockRepuestosTab
from tabs.tab_papelera import PapeleraTab
from tabs.tab_estadisticas import EstadisticasTab
from tabs.tab_administracion import AdministracionTab

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
LOGO_ICONO = os.path.join(BASE_DIR, "resources",
                          "images", "logos", "aerolineas_icono.png")
LOGO_COMPLETO = os.path.join(
    BASE_DIR, "resources", "images", "logos", "aerolineas_logo.png")

#API_BASE_URL = direcciones.API_BASE_URL  # URL de la API definida en direcciones.py
"""
CAMBIO DE CLAVE EN EL CLIENTE
=============================
Dos piezas:
  1) Un diálogo DialogoCambiarClave para que el usuario ingrese la nueva.
  2) La detección de debe_cambiar_clave después del login, que obliga
     al cambio antes de dejar entrar a la app.
"""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QLabel, QLineEdit, QPushButton, QMessageBox
)
from api_client import ApiError, SesionExpirada


# ─────────────────────────────────────────────────────────────
# 1) DIÁLOGO DE CAMBIO DE CLAVE
# ─────────────────────────────────────────────────────────────
class DialogoCambiarClave(QDialog):
    """Pide la clave actual y la nueva. Llama a cambiar_clave.php."""

    def __init__(self, api, obligatorio=False, parent=None):
        super().__init__(parent)
        self.api = api
        self.obligatorio = obligatorio   # True = primer login / reset, no puede cancelar
        self.setWindowTitle("Cambiar contraseña")
        self.setModal(True)
        self.setMinimumSize(820, 520)
        if os.path.exists(LOGO_ICONO):
            self.setWindowIcon(QIcon(LOGO_ICONO))
        self.setStyleSheet("QDialog { background-color: #eceff1; }")
        self._construir()

    def _construir(self):
        layout_principal = QHBoxLayout()
        layout_principal.setContentsMargins(0, 0, 0, 0)
        layout_principal.setSpacing(0)

        # ── Panel izquierdo (azul, como el login) ──
        panel_izquierdo = QFrame()
        panel_izquierdo.setFixedWidth(320)
        panel_izquierdo.setStyleSheet("QFrame { background-color: #1565c0; }")

        layout_izq = QVBoxLayout()
        layout_izq.setContentsMargins(30, 40, 30, 40)
        layout_izq.setSpacing(20)
        layout_izq.addStretch()

        icono = QLabel("🔒")
        icono.setFont(QFont("Arial", 72))
        icono.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout_izq.addWidget(icono)

        titulo = QLabel("SEGURIDAD\nDE LA CUENTA")
        titulo.setFont(QFont("Arial", 24, QFont.Weight.Bold))
        titulo.setStyleSheet("color: white;")
        titulo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout_izq.addWidget(titulo)

        subtitulo = QLabel("Definí una contraseña personal")
        subtitulo.setFont(QFont("Arial", 13))
        subtitulo.setStyleSheet("color: #e3f2fd;")
        subtitulo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout_izq.addWidget(subtitulo)

        layout_izq.addStretch()
        panel_izquierdo.setLayout(layout_izq)
        layout_principal.addWidget(panel_izquierdo)

        # ── Panel derecho (blanco, con el formulario) ──
        panel_derecho = QFrame()
        panel_derecho.setStyleSheet("QFrame { background-color: white; }")

        layout_der = QVBoxLayout()
        layout_der.setContentsMargins(50, 45, 50, 45)
        layout_der.setSpacing(14)

        titulo_form = QLabel("Cambiar contraseña")
        titulo_form.setFont(QFont("Arial", 24, QFont.Weight.Bold))
        titulo_form.setStyleSheet("color: #1565c0;")
        layout_der.addWidget(titulo_form)

        if self.obligatorio:
            aviso = QLabel("Debés cambiar tu contraseña antes de continuar.")
            aviso.setFont(QFont("Arial", 10, QFont.Weight.Bold))
            aviso.setStyleSheet("color: #c62828;")
            aviso.setWordWrap(True)
            layout_der.addWidget(aviso)

        layout_der.addSpacing(10)

        # Estilo reutilizable para los tres inputs (igual que el login).
        estilo_input = """
            QLineEdit {
                border: 2px solid #cfd8dc;
                border-radius: 8px;
                padding: 0 15px;
                background-color: #fafafa;
                color: black;
            }
            QLineEdit:focus {
                border: 2px solid #1565c0;
                background-color: white;
            }
        """
        estilo_label = "color: #37474f;"

        lbl_actual = QLabel("Contraseña actual")
        lbl_actual.setFont(QFont("Arial", 11, QFont.Weight.Bold))
        lbl_actual.setStyleSheet(estilo_label)
        layout_der.addWidget(lbl_actual)

        self.input_actual = QLineEdit()
        self.input_actual.setEchoMode(QLineEdit.EchoMode.Password)
        self.input_actual.setFont(QFont("Arial", 12))
        self.input_actual.setFixedHeight(42)
        self.input_actual.setStyleSheet(estilo_input)
        layout_der.addWidget(self.input_actual)

        lbl_nueva = QLabel("Nueva contraseña (mínimo 8 caracteres)")
        lbl_nueva.setFont(QFont("Arial", 11, QFont.Weight.Bold))
        lbl_nueva.setStyleSheet(estilo_label)
        layout_der.addWidget(lbl_nueva)

        self.input_nueva = QLineEdit()
        self.input_nueva.setEchoMode(QLineEdit.EchoMode.Password)
        self.input_nueva.setFont(QFont("Arial", 12))
        self.input_nueva.setFixedHeight(42)
        self.input_nueva.setStyleSheet(estilo_input)
        layout_der.addWidget(self.input_nueva)

        lbl_repetir = QLabel("Repetir nueva contraseña")
        lbl_repetir.setFont(QFont("Arial", 11, QFont.Weight.Bold))
        lbl_repetir.setStyleSheet(estilo_label)
        layout_der.addWidget(lbl_repetir)

        self.input_repetir = QLineEdit()
        self.input_repetir.setEchoMode(QLineEdit.EchoMode.Password)
        self.input_repetir.setFont(QFont("Arial", 12))
        self.input_repetir.setFixedHeight(42)
        self.input_repetir.setStyleSheet(estilo_input)
        self.input_repetir.returnPressed.connect(self.guardar)
        layout_der.addWidget(self.input_repetir)

        layout_der.addSpacing(15)

        btn_guardar = QPushButton("GUARDAR")
        btn_guardar.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        btn_guardar.setFixedHeight(48)
        btn_guardar.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_guardar.setStyleSheet("""
            QPushButton {
                background-color: #1565c0;
                color: white;
                border: none;
                border-radius: 10px;
            }
            QPushButton:hover { background-color: #0d47a1; }
            QPushButton:pressed { background-color: #0a3d91; }
        """)
        btn_guardar.clicked.connect(self.guardar)
        layout_der.addWidget(btn_guardar)

        # Si es obligatorio, no ofrecemos cancelar.
        if not self.obligatorio:
            btn_cancelar = QPushButton("Cancelar")
            btn_cancelar.setFont(QFont("Arial", 11))
            btn_cancelar.setFixedHeight(40)
            btn_cancelar.setCursor(Qt.CursorShape.PointingHandCursor)
            btn_cancelar.setStyleSheet("""
                QPushButton {
                    background-color: #eceff1;
                    color: #546e7a;
                    border: 2px solid #cfd8dc;
                    border-radius: 8px;
                }
                QPushButton:hover { background-color: #cfd8dc; }
            """)
            btn_cancelar.clicked.connect(self.reject)
            layout_der.addWidget(btn_cancelar)

        layout_der.addStretch()
        panel_derecho.setLayout(layout_der)
        layout_principal.addWidget(panel_derecho)

        self.setLayout(layout_principal)
        self.input_actual.setFocus()

    def guardar(self):
        actual  = self.input_actual.text()
        nueva   = self.input_nueva.text()
        repetir = self.input_repetir.text()

        # Validaciones del lado del cliente (buena experiencia; el servidor las repite).
        if not actual or not nueva:
            QMessageBox.warning(self, "Atención", "Completá todos los campos.")
            return
        if len(nueva) < 8:
            QMessageBox.warning(self, "Atención",
                                "La nueva contraseña debe tener al menos 8 caracteres.")
            return
        if nueva != repetir:
            QMessageBox.warning(self, "Atención", "Las contraseñas nuevas no coinciden.")
            return

        try:
            self.api.post("cambiar_clave.php", {
                "clave_actual": actual,
                "nueva_clave": nueva,
            })
            QMessageBox.information(self, "Listo", "Contraseña actualizada correctamente.")
            self.accept()

        except SesionExpirada:
            QMessageBox.warning(self, "Sesión expirada",
                                "Tu sesión venció. Volvé a iniciar sesión.")
            self.reject()
        except ApiError as e:
            # Acá cae "clave actual incorrecta", "debe ser distinta", etc.
            QMessageBox.warning(self, "Error", str(e))

    # Si es obligatorio, bloqueamos el cierre con la X o Escape.
    def reject(self):
        if self.obligatorio:
            QMessageBox.warning(self, "Atención",
                                "Debés cambiar la contraseña para continuar.")
            return   # ignora el intento de cerrar
        super().reject()

class DialogoLogin(QDialog):
    def __init__(self, api):
        super().__init__()
        self.api = api
        self.setAttribute(Qt.WidgetAttribute.WA_NativeWindow, True)
        self.usuario_autenticado = None
        self.es_administrador = False
        self.configurar_ventana()
        self.crear_interfaz()
        self.cargar_usuario_recordado() 
        ruta_script = Path(__file__).resolve().parent
        
        
    def configurar_ventana(self):
        self.setWindowTitle("Sistema de Inventario - Acceso")
        self.showMaximized()
        self.setWindowFlags(Qt.WindowType.Dialog |
                            Qt.WindowType.WindowCloseButtonHint)

        if os.path.exists(LOGO_ICONO):
            self.setWindowIcon(QIcon(LOGO_ICONO))

        self.setStyleSheet("QDialog { background-color: #eceff1; }")

    def crear_interfaz(self):
        layout_principal = QHBoxLayout()
        layout_principal.setContentsMargins(0, 0, 0, 0)
        layout_principal.setSpacing(0)

        panel_izquierdo = QFrame()
        panel_izquierdo.setFixedWidth(400)
        panel_izquierdo.setStyleSheet("QFrame { background-color: #1565c0; }")

        layout_izq = QVBoxLayout()
        layout_izq.setContentsMargins(30, 40, 30, 40)
        layout_izq.setSpacing(20)

        # ✅ RECUADRO MÁS GRANDE (180px en lugar de 150px)
        logo_frame = QFrame()
        logo_frame.setFixedHeight(120)
        logo_frame.setStyleSheet("""
            QFrame {
                background-color: rgba(255, 255, 255, 0.15);
                border: 3px solid rgba(255, 255, 255, 0.4);
                border-radius: 12px;
            }
        """)

        logo_layout = QVBoxLayout()
        logo_layout.setContentsMargins(3, 3, 3, 3)  # ✅ Margen MÍNIMO

        logo_label = QLabel()

        if os.path.exists(LOGO_COMPLETO):
            pixmap_logo = QPixmap(LOGO_COMPLETO)
            if not pixmap_logo.isNull():
                # ✅ ESCALAR AL MÁXIMO:  334x170 (casi todo el recuadro)
                pixmap_scaled = pixmap_logo.scaled(
                    334, 110,
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation
                )
                logo_label.setPixmap(pixmap_scaled)
                logo_label.setStyleSheet("background-color: transparent;")
            else:
                logo_label.setText("AEROLÍNEAS\nARGENTINAS")
                logo_label.setFont(QFont("Arial", 14, QFont.Weight.Bold))
                logo_label.setStyleSheet("color: white;")
        else:
            logo_label.setText("AEROLÍNEAS\nARGENTINAS")
            logo_label.setFont(QFont("Arial", 14, QFont.Weight.Bold))
            logo_label.setStyleSheet("color: white;")

        logo_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        logo_layout.addWidget(logo_label)
        logo_frame.setLayout(logo_layout)

        layout_izq.addWidget(logo_frame)

        icono_radio = QLabel("📻")
        icono_radio.setFont(QFont("Arial", 80))
        icono_radio.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout_izq.addWidget(icono_radio)

        titulo_sistema = QLabel("SISTEMA DE\nINVENTARIO")
        titulo_sistema.setFont(QFont("Arial", 28, QFont.Weight.Bold))
        titulo_sistema.setStyleSheet("color: white;")
        titulo_sistema.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout_izq.addWidget(titulo_sistema)

        subtitulo = QLabel("Comunicaciones de Radio")
        subtitulo.setFont(QFont("Arial", 16))
        subtitulo.setStyleSheet("color: white;")
        subtitulo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout_izq.addWidget(subtitulo)

        layout_izq.addStretch()

        version_label = QLabel(
            "Versión 1.0.1\nDesarrollado por:\nLucas E Goitea Juarez")
        version_label.setFont(QFont("Arial", 9))
        version_label.setStyleSheet("color: rgba(255, 255, 255, 0.85);")
        version_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout_izq.addWidget(version_label)

        panel_izquierdo.setLayout(layout_izq)
        layout_principal.addWidget(panel_izquierdo)

        # Panel derecho
        panel_derecho = QFrame()
        panel_derecho.setStyleSheet("QFrame { background-color: white; }")

        layout_der = QVBoxLayout()
        layout_der.setContentsMargins(50, 60, 50, 60)
        layout_der.setSpacing(25)

        titulo_form = QLabel("Iniciar Sesión")
        titulo_form.setFont(QFont("Arial", 28, QFont.Weight.Bold))
        titulo_form.setStyleSheet("color: #1565c0;")
        layout_der.addWidget(titulo_form)

        subtitulo_form = QLabel("Ingrese sus credenciales de acceso")
        subtitulo_form.setFont(QFont("Arial", 11))
        subtitulo_form.setStyleSheet("color: #546e7a;")
        layout_der.addWidget(subtitulo_form)

        layout_der.addSpacing(20)

        lbl_usuario = QLabel("Usuario / Legajo")
        lbl_usuario.setFont(QFont("Arial", 11, QFont.Weight.Bold))
        lbl_usuario.setStyleSheet("color: #37474f;")
        layout_der.addWidget(lbl_usuario)

        self.input_usuario = QLineEdit()
        self.input_usuario.setPlaceholderText("Ingrese su usuario")
        self.input_usuario.setFont(QFont("Arial", 12))
        self.input_usuario.setFixedHeight(45)
        self.input_usuario.setStyleSheet("""
            QLineEdit {
                border: 2px solid #cfd8dc;
                border-radius: 8px;
                padding: 0 15px;
                background-color: #fafafa;
                color: black;
            }
            QLineEdit:focus {
                border: 2px solid #1565c0;
                background-color: white;
            }
        """)
        layout_der.addWidget(self.input_usuario)

        lbl_password = QLabel("Contraseña")
        lbl_password.setFont(QFont("Arial", 11, QFont.Weight.Bold))
        lbl_password.setStyleSheet("color: #37474f;")
        layout_der.addWidget(lbl_password)

        password_layout = QHBoxLayout()
        password_layout.setSpacing(0)

        self.input_password = QLineEdit()
        self.input_password.setPlaceholderText("Ingrese su contraseña")
        self.input_password.setFont(QFont("Arial", 12))
        self.input_password.setFixedHeight(45)
        self.input_password.setEchoMode(QLineEdit.EchoMode.Password)
        self.input_password.setStyleSheet("""
            QLineEdit {
                border: 2px solid #cfd8dc;
                border-top-left-radius: 8px;
                border-bottom-left-radius: 8px;
                border-top-right-radius: 0px;
                border-bottom-right-radius: 0px;
                padding: 0 15px;
                background-color: #fafafa;
                color: black;
            }
            QLineEdit:focus {
                border: 2px solid #1565c0;
                background-color: white;
            }
        """)
        self.input_password.returnPressed.connect(self.iniciar_sesion)
        password_layout.addWidget(self.input_password)

        self.btn_ver_password = QPushButton("👁️")
        self.btn_ver_password.setFixedSize(45, 45)
        self.btn_ver_password.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_ver_password.setCheckable(True)
        self.btn_ver_password.setStyleSheet("""
            QPushButton {
                border: 2px solid #cfd8dc;
                border-left: none;
                border-top-right-radius: 8px;
                border-bottom-right-radius: 8px;
                background-color: #fafafa;
                font-size: 16pt;
            }
            QPushButton: hover { background-color: #e0e0e0; }
            QPushButton:checked {
                background-color: #1565c0;
                border-color: #1565c0;
            }
        """)
        self.btn_ver_password.clicked.connect(self.toggle_ver_password)
        password_layout.addWidget(self.btn_ver_password)

        layout_der.addLayout(password_layout)

        self.check_recordar = QCheckBox("Recordar mi usuario")
        self.check_recordar.setFont(QFont("Arial", 10))
        self.check_recordar.setStyleSheet("color: #546e7a;")
        layout_der.addWidget(self.check_recordar)

        layout_der.addSpacing(10)

        btn_ingresar = QPushButton("INGRESAR")
        btn_ingresar.setFont(QFont("Arial", 13, QFont.Weight.Bold))
        btn_ingresar.setFixedHeight(50)
        btn_ingresar.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_ingresar.setStyleSheet("""
            QPushButton {
                background-color: #1565c0;
                color: white;
                border: none;
                border-radius: 10px;
            }
            QPushButton:hover { background-color: #0d47a1; }
            QPushButton:pressed { background-color: #0a3d91; }
        """)
        btn_ingresar.clicked.connect(self.iniciar_sesion)
        layout_der.addWidget(btn_ingresar)

        layout_der.addSpacing(20)

        info_contacto = QLabel(
            "¿Problemas para acceder?    Contacte al administrador\nlucas.goitea@aerolineas.com.ar")
        info_contacto.setFont(QFont("Arial", 9))
        info_contacto.setStyleSheet("color: #90a4ae;")
        info_contacto.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout_der.addWidget(info_contacto)

        layout_der.addStretch()

        panel_derecho.setLayout(layout_der)
        layout_principal.addWidget(panel_derecho)

        self.setLayout(layout_principal)
        self.input_usuario.setFocus()

    def toggle_ver_password(self, checked):
        if checked:
            self.input_password.setEchoMode(QLineEdit.EchoMode.Normal)
            self.btn_ver_password.setText("🙈")
        else:
            self.input_password.setEchoMode(QLineEdit.EchoMode.Password)
            self.btn_ver_password.setText("👁️")

    def iniciar_sesion(self):
        usuario = self.input_usuario.text().strip()
        password = self.input_password.text()
 
        if not usuario or not password:
            QMessageBox.critical(self, "⚠️ Campos Vacíos",
                                "Por favor complete usuario y contraseña.")
            return
 
        # Feedback visual: la petición puede tardar un segundo.
        self.setCursor(Qt.CursorShape.WaitCursor)
        self.setEnabled(False)
        QApplication.processEvents()
 
        try:
            self.api.login(usuario, password)
 
            # El rol viene DEL SERVIDOR, no se decide acá.
            self.usuario_autenticado = self.api.usuario
            self.es_administrador = self.api.es_admin

            self.guardar_usuario_recordado()
            self.accept()
 
        except ApiError as e:
            QMessageBox.critical(self, "❌ Error de Autenticación", str(e))
            self.input_password.clear()
            self.input_password.setFocus()
 
        finally:
            self.setEnabled(True)
            self.unsetCursor()

    def cargar_usuario_recordado(self):
        settings = QSettings("Aerolineas", "InventarioRadios")
        usuario = settings.value("ultimo_usuario", "")
        if usuario:
            self.input_usuario.setText(usuario)
            self.check_recordar.setChecked(True)
            self.input_password.setFocus()   # el usuario ya está, va directo a la clave
 
    def guardar_usuario_recordado(self):
        settings = QSettings("Aerolineas", "InventarioRadios")
        if self.check_recordar.isChecked():
            settings.setValue("ultimo_usuario", self.input_usuario.text().strip())
        else:
            settings.remove("ultimo_usuario")


class VentanaPrincipal(QMainWindow):
    def __init__(self, api, usuario, es_administrador):
        super().__init__()
        self.api = api
        self.usuario = usuario
        self.es_administrador = es_administrador
        self.configurar_ventana()
        self.crear_interfaz()

    def configurar_ventana(self):
        self.setWindowTitle("Sistema de Inventario de Equipos de Radio")
        if os.path.exists(LOGO_ICONO):
            self.setWindowIcon(QIcon(LOGO_ICONO))
        self.setMinimumSize(1366, 768)
        self.showMaximized()

    def crear_interfaz(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        layout_principal = QVBoxLayout()
        layout_principal.setContentsMargins(0, 0, 0, 0)
        layout_principal.setSpacing(0)

        barra_superior = self.crear_barra_superior()
        layout_principal.addWidget(barra_superior)

        self.tabs = QTabWidget()
        self.tabs.setFont(QFont("Arial", 11, QFont.Weight.Bold))
        self.tabs.setStyleSheet("""
            QTabWidget::pane {
                border: none;
                background-color: #eceff1;
            }
            QTabBar::tab {
                background-color: #90a4ae;
                color:  white;
                padding: 15px 25px;
                margin-right: 2px;
                border-top-left-radius: 8px;
                border-top-right-radius: 8px;
                font-size: 12pt;
                font-weight: bold;
                min-width: 140px;
            }
            QTabBar::tab:selected {
                background:  qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #37474f, stop:1 #263238);
            }
            QTabBar::tab:hover: ! selected {
                background-color: #78909c;
            }
        """)
        
        self.ingreso_tab     = IngresoEquiposTab(self.api)
        self.inventario_tab  = InventarioTab(self.api)
        self.taller_tab      = TallerTab(self.api)
        self.repuestos_tab   = StockRepuestosTab(self.api)
        self.papelera_tab    = PapeleraTab(self.api, self.es_administrador)
        self.estadisticas_tab = EstadisticasTab(self.api)

        # Pasar la referencia de papelera a inventario
        self.inventario_tab.set_papelera_tab(self.papelera_tab)

        self.tabs.addTab(self.ingreso_tab,     "📥 Ingreso de Equipos")
        self.tabs.addTab(self.inventario_tab,  "📦 Inventario")
        self.tabs.addTab(self.taller_tab,      "🛠️ Taller")
        self.tabs.addTab(self.repuestos_tab,   "🔩 Repuestos" )
        self.tabs.addTab(self.papelera_tab,    "🗑️ Papelera")
        self.tabs.addTab(self.estadisticas_tab, "📊 Estadísticas")

        if self.es_administrador:
            self.tabs.addTab(AdministracionTab(self.api), "👤 Administración")
            
        self.tabs.currentChanged.connect(self.on_tab_changed)
        layout_principal.addWidget(self.tabs)
        central_widget.setLayout(layout_principal)

    def crear_barra_superior(self):
        barra = QFrame()
        barra.setFixedHeight(70)
        barra.setStyleSheet(
            "QFrame { background-color: #1565c0; border: none; }")

        layout = QHBoxLayout()
        layout.setContentsMargins(20, 10, 20, 10)
        layout.setSpacing(20)

        logo_label = QLabel()
        if os.path.exists(LOGO_ICONO):
            pixmap_logo = QPixmap(LOGO_ICONO)
            if not pixmap_logo.isNull():
                pixmap_scaled = pixmap_logo.scaled(
                    50, 50, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
                logo_label.setPixmap(pixmap_scaled)
            else:
                logo_label.setText("📻")
                logo_label.setFont(QFont("Arial", 32))
                logo_label.setStyleSheet("color: white;")
        else:
            logo_label.setText("📻")
            logo_label.setFont(QFont("Arial", 32))
            logo_label.setStyleSheet("color: white;")

        logo_label.setFixedSize(50, 50)
        logo_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(logo_label)

        titulo = QLabel("Sistema de Inventario de Equipos de Radio")
        titulo.setFont(QFont("Arial", 18, QFont.Weight.Bold))
        titulo.setStyleSheet("color: white;")
        layout.addWidget(titulo)

        layout.addStretch()

        perfil_layout = QHBoxLayout()
        perfil_layout.setSpacing(12)

        icono_usuario = QLabel("👨‍💼" if self.es_administrador else "👤")
        icono_usuario.setFont(QFont("Arial", 28))
        perfil_layout.addWidget(icono_usuario)

        info_layout = QVBoxLayout()
        info_layout.setSpacing(2)

        lbl_nombre = QLabel(f"Usuario: {self.usuario}")
        lbl_nombre.setFont(QFont("Arial", 11, QFont.Weight.Bold))
        lbl_nombre.setStyleSheet("color: white;")
        info_layout.addWidget(lbl_nombre)

        lbl_rol = QLabel(
            "👨‍💻 Administrador" if self.es_administrador else "👁️ Usuario")
        lbl_rol.setFont(QFont("Arial", 9))
        lbl_rol.setStyleSheet("color: #e3f2fd;")
        info_layout.addWidget(lbl_rol)

        perfil_layout.addLayout(info_layout)
        layout.addLayout(perfil_layout)

        btn_salir = QPushButton("🚪 Salir")
        btn_salir.setFont(QFont("Arial", 11, QFont.Weight.Bold))
        btn_salir.setFixedHeight(50)
        btn_salir.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_salir.setStyleSheet("""
            QPushButton {
                background-color: #c62828;
                color: white;
                border: none;
                border-radius: 8px;
                padding: 0 20px;
            }
            QPushButton:hover { background-color: #b71c1c; }
            QPushButton:pressed { background-color: #8e0000; }
        """)
        btn_salir.clicked.connect(self.cerrar_sesion)
        layout.addWidget(btn_salir)

        barra.setLayout(layout)
        return barra

    

    def cerrar_sesion(self):
        respuesta = QMessageBox.question(
            self, "🚪 Cerrar Sesión", "¿Está seguro que desea cerrar la sesión?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)

        if respuesta == QMessageBox.StandardButton.Yes:
            self.api.logout()
            self.close()
            dialogo = DialogoLogin(self.api)
            if dialogo.exec() == QDialog.DialogCode.Accepted:
                nueva = abrir_sesion(self.api, dialogo)
                if nueva is not None:
                    self.ventana = nueva
                    self.ventana.show()
    
    def on_tab_changed(self, index):
            """Refresca los datos cuando cambia de pestaña"""
            widget_actual = self.tabs.widget(index)
    
            for metodo in ('obtener_datos_iniciales', 
                           'obtener_datos',
                           'cargar_datos',
                           'obtener_usuarios',
                           'cargar_resumen'):
                if hasattr(widget_actual, metodo):
                    getattr(widget_actual, metodo)()
                    break

def abrir_sesion(api, dialogo_login):
    """Lógica común después de un login exitoso.
    Devuelve la VentanaPrincipal, o None si no se debe entrar."""
    # Si la cuenta requiere cambio de clave, lo forzamos ANTES de entrar.
    if api.debe_cambiar_clave:
        cambio = DialogoCambiarClave(api, obligatorio=True)
        if cambio.exec() != QDialog.DialogCode.Accepted:
            return None   # no cambió la clave, no entra

    return VentanaPrincipal(api,
                            dialogo_login.usuario_autenticado,
                            dialogo_login.es_administrador)

def main():
    app = QApplication(sys.argv)
    if os.path.exists(LOGO_ICONO):
        app.setWindowIcon(QIcon(LOGO_ICONO))
    app.setFont(QFont("Arial", 10))

    api = ApiClient()
    app.setStyleSheet("""
        QMessageBox { background-color: #F3F3F3; }
        QMessageBox QLabel { color: #000000; background-color: transparent; font-size: 14px; }
        QMessageBox QPushButton {
            background-color: #007acc; color: white; border-radius: 4px;
            padding: 6px 14px; font-weight: bold;
        }
        QMessageBox QPushButton:hover { background-color: #005999; }
    """)

    # Si quedó un token válido de la vez anterior, entramos directo
    # (salvo que la cuenta tenga pendiente el cambio de clave).
    if api.verificar_sesion():
        if api.debe_cambiar_clave:
            cambio = DialogoCambiarClave(api, obligatorio=True)
            if cambio.exec() != QDialog.DialogCode.Accepted:
                sys.exit(0)
        ventana = VentanaPrincipal(api, api.usuario, api.es_admin)
        ventana.show()
        sys.exit(app.exec())

    dialogo_login = DialogoLogin(api)
    if dialogo_login.exec() == QDialog.DialogCode.Accepted:
        # Si no completó el cambio de clave obligatorio, no entra.
        ventana = abrir_sesion(api, dialogo_login)
        if ventana is not None:
            ventana.show()
            sys.exit(app.exec())
        
    

if __name__ == "__main__":
    main()

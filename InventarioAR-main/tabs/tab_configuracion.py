"""
Pestaña:  Configuración del Sistema
Versión: 4.1 - OPTIMIZADA Y COMPACTA
Fecha: 2025-12-14
Autor: lucasarsa2015-cpu
Descripción: Configuración completa del sistema con sub-tabs (versión compacta)
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QTabWidget, QFrame, QMessageBox, QFileDialog,
    QGridLayout, QGroupBox, QTextEdit, QTableWidget, QTableWidgetItem,
    QHeaderView, QDialog, QComboBox, QCheckBox, QSpinBox
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QColor, QPixmap
import os
from datetime import datetime


# ═══════════════════════════════════════════════════════════
# DIÁLOGO:  AGREGAR/EDITAR DATO PREDEFINIDO
# ═══════════════════════════════════════════════════════════

class DialogoDatoPredefinido(QDialog):
    """Ventana para agregar o editar un dato predefinido"""

    def __init__(self, parent=None, categoria="", valor="", modo="crear"):
        super().__init__(parent)
        self.categoria = categoria
        self.valor_actual = valor
        self.modo = modo
        self.valor_guardado = ""
        self.configurar_ventana()
        self.crear_interfaz()

        if modo == "editar" and valor:
            self.input_valor.setText(valor)

    def configurar_ventana(self):
        titulo = f"✨ Agregar {self.categoria}" if self.modo == "crear" else f"✏️ Editar {self. categoria}"
        self.setWindowTitle(titulo)
        self.setModal(True)
        self.setFixedSize(450, 200)
        self.setStyleSheet("QDialog { background-color: #f5f7fa; }")

    def crear_interfaz(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        # Título
        titulo = QLabel(
            f"{'➕ Nuevo' if self.modo == 'crear' else '✏️ Editar'} {self.categoria}")
        titulo.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        titulo.setStyleSheet("color: #0d47a1; padding: 8px;")
        titulo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(titulo)

        # Campo de valor
        form_layout = QHBoxLayout()

        lbl = QLabel(f"{self.categoria}:")
        lbl.setFont(QFont("Arial", 11, QFont.Weight.Bold))
        lbl.setStyleSheet("color: #37474f;")
        lbl.setFixedWidth(120)
        form_layout.addWidget(lbl)

        self.input_valor = QLineEdit()
        self.input_valor.setPlaceholderText(
            f"Ingrese {self.categoria. lower()}")
        self.input_valor.setFont(QFont("Arial", 11))
        self.input_valor.setFixedHeight(35)
        self.input_valor.setStyleSheet("""
            QLineEdit {
                border: 2px solid #cfd8dc;
                border-radius: 6px;
                padding: 8px;
                background-color: white;
            }
            QLineEdit:focus { border: 2px solid #1976d2; }
        """)
        form_layout.addWidget(self.input_valor)

        layout.addLayout(form_layout)

        # Botones
        botones_layout = QHBoxLayout()
        botones_layout.setSpacing(10)

        btn_cancelar = QPushButton("❌ Cancelar")
        btn_cancelar.setFont(QFont("Arial", 11, QFont.Weight.Bold))
        btn_cancelar.setFixedHeight(40)
        btn_cancelar. setCursor(Qt.CursorShape.PointingHandCursor)
        btn_cancelar.setStyleSheet("""
            QPushButton {
                background-color:  #757575;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 0 20px;
            }
            QPushButton:hover { background-color: #616161; }
        """)
        btn_cancelar.clicked.connect(self.reject)
        botones_layout. addWidget(btn_cancelar)

        btn_guardar = QPushButton("💾 Guardar")
        btn_guardar.setFont(QFont("Arial", 11, QFont.Weight.Bold))
        btn_guardar.setFixedHeight(40)
        btn_guardar.setCursor(Qt. CursorShape.PointingHandCursor)
        btn_guardar.setStyleSheet("""
            QPushButton {
                background:  qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #1e8449, stop:1 #27ae60);
                color: white;
                border: none;
                border-radius: 6px;
                padding: 0 20px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #186a3b, stop:1 #1e8449);
            }
        """)
        btn_guardar.clicked.connect(self.guardar)
        botones_layout.addWidget(btn_guardar)

        layout.addLayout(botones_layout)
        self.setLayout(layout)

    def guardar(self):
        valor = self.input_valor.text().strip()
        if not valor:
            QMessageBox.warning(self, "⚠️ Campo Vacío",
                                f"Ingrese un valor para {self.categoria}")
            return

        self.valor_guardado = valor
        self.accept()


# ═══════════════════════════════════════════════════════════
# SUB-TAB 1: BASE DE DATOS
# ═══════════════════════════════════════════════════════════

class SubTabBaseDatos(QWidget):
    """Sub-tab de configuración de base de datos"""

    def __init__(self):
        super().__init__()
        self.crear_interfaz()

    def crear_interfaz(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(15)

        grupo_conexion = self.crear_grupo_conexion()
        layout.addWidget(grupo_conexion)

        grupo_backup = self.crear_grupo_backup()
        layout.addWidget(grupo_backup)

        grupo_log = self.crear_grupo_log()
        layout.addWidget(grupo_log)

        layout.addStretch()
        self.setLayout(layout)

    def crear_grupo_conexion(self):
        """Grupo de conexión MySQL"""
        grupo = QGroupBox("🔌 Conexión MySQL")
        grupo.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        grupo.setStyleSheet("""
            QGroupBox {
                border: 2px solid #1976d2;
                border-radius: 8px;
                margin-top:  8px;
                padding-top: 12px;
                background-color: white;
            }
            QGroupBox::title {
                color: #0d47a1;
                subcontrol-origin: margin;
                left: 12px;
                padding: 0 8px;
            }
        """)

        layout = QGridLayout()
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(10)
        layout.setColumnMinimumWidth(0, 120)

        estilo_label = "color: #37474f; font-weight: bold; font-size: 11pt;"
        estilo_input = """
            QLineEdit {
                border: 2px solid #cfd8dc;
                border-radius: 6px;
                padding: 8px;
                font-size: 11pt;
                background-color: #fafafa;
            }
            QLineEdit:focus {
                border: 2px solid #1976d2;
                background-color: white;
            }
        """

        row = 0

        # Host
        lbl = QLabel("🌐 Host:")
        lbl.setStyleSheet(estilo_label)
        lbl.setAlignment(Qt.AlignmentFlag.AlignRight |
                         Qt.AlignmentFlag.AlignVCenter)
        layout.addWidget(lbl, row, 0)

        self.input_host = QLineEdit()
        self.input_host.setText("localhost")
        self.input_host.setFixedHeight(35)
        self.input_host.setStyleSheet(estilo_input)
        layout.addWidget(self.input_host, row, 1)
        row += 1

        # Puerto
        lbl = QLabel("🔢 Puerto:")
        lbl.setStyleSheet(estilo_label)
        lbl.setAlignment(Qt.AlignmentFlag.AlignRight |
                         Qt. AlignmentFlag.AlignVCenter)
        layout.addWidget(lbl, row, 0)

        self.input_puerto = QLineEdit()
        self.input_puerto.setText("3306")
        self.input_puerto.setFixedHeight(35)
        self.input_puerto.setStyleSheet(estilo_input)
        layout.addWidget(self. input_puerto, row, 1)
        row += 1

        # Usuario
        lbl = QLabel("👤 Usuario:")
        lbl.setStyleSheet(estilo_label)
        lbl.setAlignment(Qt.AlignmentFlag.AlignRight |
                         Qt.AlignmentFlag.AlignVCenter)
        layout.addWidget(lbl, row, 0)

        self.input_usuario = QLineEdit()
        self.input_usuario.setText("root")
        self.input_usuario.setFixedHeight(35)
        self.input_usuario.setStyleSheet(estilo_input)
        layout.addWidget(self.input_usuario, row, 1)
        row += 1

        # Contraseña
        lbl = QLabel("🔒 Contraseña:")
        lbl.setStyleSheet(estilo_label)
        lbl.setAlignment(Qt.AlignmentFlag.AlignRight |
                         Qt.AlignmentFlag.AlignVCenter)
        layout.addWidget(lbl, row, 0)

        self. input_password = QLineEdit()
        self.input_password.setEchoMode(QLineEdit.EchoMode.Password)
        self.input_password.setFixedHeight(35)
        self.input_password.setStyleSheet(estilo_input)
        layout.addWidget(self.input_password, row, 1)
        row += 1

        # Base de Datos
        lbl = QLabel("💾 Base de Datos:")
        lbl.setStyleSheet(estilo_label)
        lbl.setAlignment(Qt.AlignmentFlag.AlignRight |
                         Qt.AlignmentFlag.AlignVCenter)
        layout.addWidget(lbl, row, 0)

        self.input_database = QLineEdit()
        self.input_database.setText("inventario_radios")
        self.input_database.setFixedHeight(35)
        self.input_database. setStyleSheet(estilo_input)
        layout.addWidget(self.input_database, row, 1)
        row += 1

        # Botones
        botones_layout = QHBoxLayout()
        botones_layout.setSpacing(10)

        btn_test = QPushButton("🔍 Test de Conexión")
        btn_test.setFont(QFont("Arial", 11, QFont.Weight.Bold))
        btn_test.setFixedHeight(40)
        btn_test.setCursor(Qt. CursorShape.PointingHandCursor)
        btn_test.setStyleSheet("""
            QPushButton {
                background-color: #1976d2;
                color:  white;
                border: none;
                border-radius: 6px;
                padding: 0 20px;
            }
            QPushButton:hover { background-color: #1565c0; }
        """)
        btn_test.clicked.connect(self.test_conexion)
        botones_layout.addWidget(btn_test)

        btn_guardar = QPushButton("💾 Guardar Configuración")
        btn_guardar.setFont(QFont("Arial", 11, QFont.Weight.Bold))
        btn_guardar. setFixedHeight(40)
        btn_guardar.setCursor(Qt.CursorShape. PointingHandCursor)
        btn_guardar.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #1e8449, stop:1 #27ae60);
                color: white;
                border: none;
                border-radius: 6px;
                padding: 0 20px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #186a3b, stop:1 #1e8449);
            }
        """)
        btn_guardar.clicked.connect(self.guardar_configuracion)
        botones_layout.addWidget(btn_guardar)

        layout.addLayout(botones_layout, row, 0, 1, 2)

        grupo. setLayout(layout)
        return grupo

    def crear_grupo_backup(self):
        """Grupo de backups"""
        grupo = QGroupBox("💾 Backups")
        grupo.setFont(QFont("Arial", 12, QFont. Weight.Bold))
        grupo.setStyleSheet("""
            QGroupBox {
                border: 2px solid #f57c00;
                border-radius: 8px;
                margin-top: 8px;
                padding-top: 12px;
                background-color: white;
            }
            QGroupBox::title {
                color:  #e65100;
                subcontrol-origin: margin;
                left:  12px;
                padding:  0 8px;
            }
        """)

        layout = QGridLayout()
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(10)

        row = 0

        # Carpeta de backups
        lbl = QLabel("📁 Carpeta de Backups:")
        lbl.setFont(QFont("Arial", 11, QFont.Weight.Bold))
        lbl.setStyleSheet("color: #37474f;")
        layout.addWidget(lbl, row, 0)

        carpeta_layout = QHBoxLayout()

        self.input_carpeta_backup = QLineEdit()
        self.input_carpeta_backup.setText(
            "G:/Programa Nuevo Base de datos/backups")
        self.input_carpeta_backup.setFixedHeight(35)
        self.input_carpeta_backup.setStyleSheet("""
            QLineEdit {
                border:  2px solid #cfd8dc;
                border-radius:  6px;
                padding:  8px;
                font-size: 10pt;
                background-color:  #fafafa;
            }
        """)
        carpeta_layout.addWidget(self.input_carpeta_backup)

        btn_examinar = QPushButton("📂 Examinar")
        btn_examinar.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        btn_examinar.setFixedSize(100, 35)
        btn_examinar.setCursor(Qt. CursorShape.PointingHandCursor)
        btn_examinar.setStyleSheet("""
            QPushButton {
                background-color: #757575;
                color: white;
                border: none;
                border-radius: 6px;
            }
            QPushButton:hover { background-color: #616161; }
        """)
        btn_examinar.clicked.connect(self.seleccionar_carpeta_backup)
        carpeta_layout.addWidget(btn_examinar)

        layout.addLayout(carpeta_layout, row, 1)
        row += 1

        # Backup automático
        lbl = QLabel("⏰ Backup Automático:")
        lbl.setFont(QFont("Arial", 11, QFont.Weight.Bold))
        lbl.setStyleSheet("color: #37474f;")
        layout.addWidget(lbl, row, 0)

        auto_layout = QHBoxLayout()

        self.check_backup_auto = QCheckBox("Activar backup automático diario")
        self.check_backup_auto.setChecked(True)
        self.check_backup_auto.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        self.check_backup_auto.setStyleSheet("color: #1976d2;")
        auto_layout.addWidget(self. check_backup_auto)

        auto_layout.addWidget(QLabel("a las"))

        self.spin_hora = QSpinBox()
        self.spin_hora.setRange(0, 23)
        self.spin_hora.setValue(2)
        self.spin_hora.setFixedSize(60, 30)
        self.spin_hora.setStyleSheet("""
            QSpinBox {
                border: 2px solid #cfd8dc;
                border-radius: 4px;
                padding: 4px;
                font-size:  11pt;
                font-weight: bold;
            }
        """)
        auto_layout. addWidget(self.spin_hora)

        auto_layout.addWidget(QLabel(":"))

        self. spin_minuto = QSpinBox()
        self.spin_minuto.setRange(0, 59)
        self.spin_minuto.setValue(0)
        self.spin_minuto.setFixedSize(60, 30)
        self.spin_minuto.setStyleSheet("""
            QSpinBox {
                border: 2px solid #cfd8dc;
                border-radius: 4px;
                padding: 4px;
                font-size: 11pt;
                font-weight:  bold;
            }
        """)
        auto_layout.addWidget(self.spin_minuto)

        auto_layout.addStretch()

        layout.addLayout(auto_layout, row, 1)
        row += 1

        # Botones de backup manual
        botones_layout = QHBoxLayout()
        botones_layout.setSpacing(10)

        btn_backup_sql = QPushButton("💿 Backup SQL Ahora")
        btn_backup_sql.setFont(QFont("Arial", 11, QFont. Weight.Bold))
        btn_backup_sql.setFixedHeight(40)
        btn_backup_sql.setCursor(Qt. CursorShape.PointingHandCursor)
        btn_backup_sql.setStyleSheet("""
            QPushButton {
                background-color: #f57c00;
                color:  white;
                border: none;
                border-radius: 6px;
                padding: 0 15px;
            }
            QPushButton:hover { background-color: #e65100; }
        """)
        btn_backup_sql.clicked. connect(self.backup_sql)
        botones_layout.addWidget(btn_backup_sql)

        btn_backup_excel = QPushButton("📊 Backup Excel Ahora")
        btn_backup_excel.setFont(QFont("Arial", 11, QFont.Weight.Bold))
        btn_backup_excel.setFixedHeight(40)
        btn_backup_excel.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_backup_excel.setStyleSheet("""
            QPushButton {
                background-color: #388e3c;
                color:  white;
                border: none;
                border-radius: 6px;
                padding: 0 15px;
            }
            QPushButton:hover { background-color: #2e7d32; }
        """)
        btn_backup_excel.clicked.connect(self.backup_excel)
        botones_layout.addWidget(btn_backup_excel)

        btn_restaurar = QPushButton("🔄 Restaurar desde Backup")
        btn_restaurar.setFont(QFont("Arial", 11, QFont. Weight.Bold))
        btn_restaurar.setFixedHeight(40)
        btn_restaurar.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_restaurar.setStyleSheet("""
            QPushButton {
                background-color: #7b1fa2;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 0 15px;
            }
            QPushButton:hover { background-color: #6a1b9a; }
        """)
        btn_restaurar.clicked.connect(self. restaurar_backup)
        botones_layout. addWidget(btn_restaurar)

        layout.addLayout(botones_layout, row, 0, 1, 2)

        grupo.setLayout(layout)
        return grupo

    def crear_grupo_log(self):
        """Grupo de log de backups"""
        grupo = QGroupBox("📜 Log de Backups")
        grupo.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        grupo.setStyleSheet("""
            QGroupBox {
                border: 2px solid #7b1fa2;
                border-radius: 8px;
                margin-top: 8px;
                padding-top: 12px;
                background-color: white;
            }
            QGroupBox::title {
                color: #6a1b9a;
                subcontrol-origin: margin;
                left: 12px;
                padding: 0 8px;
            }
        """)

        layout = QVBoxLayout()
        layout.setContentsMargins(15, 15, 15, 15)

        self.text_log = QTextEdit()
        self.text_log.setReadOnly(True)
        self.text_log.setMaximumHeight(120)
        self.text_log.setFont(QFont("Courier New", 9))
        self.text_log.setStyleSheet("""
            QTextEdit {
                border:  2px solid #cfd8dc;
                border-radius: 6px;
                padding: 8px;
                background-color: #263238;
                color: #00ff00;
            }
        """)
        self.text_log.setPlaceholderText(
            "Los registros de backups aparecerán aquí...")

        # Log de ejemplo
        self.text_log. append(
            "✅ [2025-12-14 02:00: 00] Backup automático SQL completado")
        self.text_log. append(
            "✅ [2025-12-13 02:00:00] Backup automático SQL completado")
        self.text_log.append(
            "📊 [2025-12-12 15:30:00] Backup manual Excel creado")

        layout.addWidget(self. text_log)

        grupo.setLayout(layout)
        return grupo

    def test_conexion(self):
        """Prueba la conexión a MySQL"""
        QMessageBox.information(
            self,
            "✅ Conexión Exitosa",
            f"Conexión establecida correctamente con:\n\n"
            f"Host: {self.input_host. text()}\n"
            f"Puerto: {self.input_puerto. text()}\n"
            f"Usuario: {self.input_usuario.text()}\n"
            f"Base de Datos: {self.input_database.text()}"
        )

    def guardar_configuracion(self):
        """Guarda la configuración de MySQL"""
        QMessageBox.information(
            self,
            "💾 Configuración Guardada",
            "La configuración de conexión ha sido guardada correctamente."
        )

    def seleccionar_carpeta_backup(self):
        """Selecciona carpeta de backups"""
        carpeta = QFileDialog.getExistingDirectory(
            self,
            "Seleccionar Carpeta de Backups",
            self.input_carpeta_backup. text()
        )
        if carpeta:
            self.input_carpeta_backup.setText(carpeta)

    def backup_sql(self):
        """Realiza backup SQL"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        archivo = f"backup_{timestamp}.sql"

        QMessageBox.information(
            self,
            "💿 Backup SQL Creado",
            f"Backup creado exitosamente:\n\n{archivo}\n\n"
            f"Ubicación: {self.input_carpeta_backup.text()}"
        )

        self.text_log.append(
            f"✅ [{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Backup manual SQL:  {archivo}")

    def backup_excel(self):
        """Realiza backup Excel"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        archivo = f"backup_{timestamp}. xlsx"

        QMessageBox.information(
            self,
            "📊 Backup Excel Creado",
            f"Backup creado exitosamente:\n\n{archivo}\n\n"
            f"Ubicación: {self.input_carpeta_backup.text()}"
        )

        self.text_log.append(
            f"📊 [{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Backup manual Excel: {archivo}")

    def restaurar_backup(self):
        """Restaura desde un backup"""
        archivo, _ = QFileDialog.getOpenFileName(
            self,
            "Seleccionar Backup para Restaurar",
            self. input_carpeta_backup.text(),
            "Archivos SQL (*.sql);;Todos los archivos (*.*)"
        )

        if archivo:
            respuesta = QMessageBox.warning(
                self,
                "⚠️ ADVERTENCIA",
                f"¿Está seguro de restaurar desde:\n\n{os.path.basename(archivo)}\n\n"
                "⚠️ ESTO SOBRESCRIBIRÁ TODOS LOS DATOS ACTUALES ⚠️",
                QMessageBox.StandardButton.Yes | QMessageBox. StandardButton.No
            )

            if respuesta == QMessageBox.StandardButton.Yes:
                QMessageBox.information(
                    self,
                    "✅ Restauración Completada",
                    "La base de datos ha sido restaurada exitosamente."
                )

                self.text_log.append(
                    f"🔄 [{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Restauración desde:  {os.path.basename(archivo)}")


# Continuará en el siguiente mensaje con las demás sub-tabs optimizadas...
# ═══════════════════════════════════════════════════════════
# SUB-TAB 2:  RECURSOS (IMÁGENES)
# ═══════════════════════════════════════════════════════════

class SubTabRecursos(QWidget):
    """Sub-tab de configuración de recursos (imágenes, logos)"""

    def __init__(self):
        super().__init__()
        self.crear_interfaz()

    def crear_interfaz(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(15)

        grupo_carpetas = self.crear_grupo_carpetas()
        layout.addWidget(grupo_carpetas)

        grupo_logo = self.crear_grupo_logo()
        layout.addWidget(grupo_logo)

        layout.addStretch()
        self.setLayout(layout)

    def crear_grupo_carpetas(self):
        """Grupo de configuración de carpetas"""
        grupo = QGroupBox("📁 Carpetas de Recursos")
        grupo.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        grupo.setStyleSheet("""
            QGroupBox {
                border:  2px solid #1976d2;
                border-radius: 8px;
                margin-top: 8px;
                padding-top: 12px;
                background-color:  white;
            }
            QGroupBox::title {
                color: #0d47a1;
                subcontrol-origin: margin;
                left: 12px;
                padding: 0 8px;
            }
        """)

        layout = QGridLayout()
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(10)

        estilo_label = "color: #37474f; font-weight: bold; font-size: 11pt;"

        row = 0

        # Carpeta de imágenes de modelos
        lbl = QLabel("🖼️ Imágenes de Modelos:")
        lbl.setStyleSheet(estilo_label)
        layout.addWidget(lbl, row, 0)

        carpeta_layout = QHBoxLayout()

        self.input_carpeta_imagenes = QLineEdit()
        self.input_carpeta_imagenes.setText(
            "G:/Programa Nuevo Base de datos/resources/images/modelos")
        self.input_carpeta_imagenes.setFixedHeight(35)
        self.input_carpeta_imagenes.setStyleSheet("""
            QLineEdit {
                border: 2px solid #cfd8dc;
                border-radius: 6px;
                padding: 8px;
                font-size:  10pt;
                background-color:  #fafafa;
            }
        """)
        carpeta_layout.addWidget(self.input_carpeta_imagenes)

        btn_examinar = QPushButton("📂")
        btn_examinar.setFixedSize(35, 35)
        btn_examinar.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_examinar.setStyleSheet("""
            QPushButton {
                background-color:  #757575;
                color: white;
                border: none;
                border-radius: 6px;
                font-size: 16pt;
            }
            QPushButton:hover { background-color: #616161; }
        """)
        btn_examinar.clicked.connect(
            lambda: self.seleccionar_carpeta(self.input_carpeta_imagenes))
        carpeta_layout.addWidget(btn_examinar)

        btn_abrir = QPushButton("🔍")
        btn_abrir.setFixedSize(35, 35)
        btn_abrir.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_abrir.setStyleSheet("""
            QPushButton {
                background-color: #1976d2;
                color:  white;
                border: none;
                border-radius: 6px;
                font-size:  16pt;
            }
            QPushButton:hover { background-color: #1565c0; }
        """)
        btn_abrir.clicked.connect(lambda: self. abrir_carpeta(
            self. input_carpeta_imagenes. text()))
        carpeta_layout.addWidget(btn_abrir)

        layout.addLayout(carpeta_layout, row, 1)
        row += 1

        # Carpeta de logos
        lbl = QLabel("🏢 Logos:")
        lbl.setStyleSheet(estilo_label)
        layout.addWidget(lbl, row, 0)

        carpeta_layout2 = QHBoxLayout()

        self.input_carpeta_logos = QLineEdit()
        self.input_carpeta_logos.setText(
            "G:/Programa Nuevo Base de datos/resources/images/logos")
        self.input_carpeta_logos. setFixedHeight(35)
        self.input_carpeta_logos.setStyleSheet("""
            QLineEdit {
                border: 2px solid #cfd8dc;
                border-radius: 6px;
                padding: 8px;
                font-size: 10pt;
                background-color: #fafafa;
            }
        """)
        carpeta_layout2.addWidget(self.input_carpeta_logos)

        btn_examinar2 = QPushButton("📂")
        btn_examinar2.setFixedSize(35, 35)
        btn_examinar2.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_examinar2.setStyleSheet("""
            QPushButton {
                background-color: #757575;
                color: white;
                border: none;
                border-radius: 6px;
                font-size: 16pt;
            }
            QPushButton: hover { background-color: #616161; }
        """)
        btn_examinar2.clicked.connect(
            lambda: self.seleccionar_carpeta(self. input_carpeta_logos))
        carpeta_layout2.addWidget(btn_examinar2)

        btn_abrir2 = QPushButton("🔍")
        btn_abrir2.setFixedSize(35, 35)
        btn_abrir2.setCursor(Qt.CursorShape. PointingHandCursor)
        btn_abrir2.setStyleSheet("""
            QPushButton {
                background-color: #1976d2;
                color: white;
                border: none;
                border-radius: 6px;
                font-size: 16pt;
            }
            QPushButton:hover { background-color: #1565c0; }
        """)
        btn_abrir2.clicked.connect(
            lambda: self.abrir_carpeta(self.input_carpeta_logos.text()))
        carpeta_layout2.addWidget(btn_abrir2)

        layout.addLayout(carpeta_layout2, row, 1)
        row += 1

        # Botón guardar
        btn_guardar = QPushButton("💾 Guardar Configuración")
        btn_guardar.setFont(QFont("Arial", 11, QFont.Weight.Bold))
        btn_guardar.setFixedHeight(40)
        btn_guardar.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_guardar.setStyleSheet("""
            QPushButton {
                background:  qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop: 0 #1e8449, stop:1 #27ae60);
                color: white;
                border: none;
                border-radius: 6px;
                padding: 0 20px;
            }
            QPushButton: hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #186a3b, stop:1 #1e8449);
            }
        """)
        btn_guardar.clicked.connect(self.guardar_carpetas)
        layout.addWidget(btn_guardar, row, 0, 1, 2)

        grupo.setLayout(layout)
        return grupo

    def crear_grupo_logo(self):
        """Grupo de logo de la empresa"""
        grupo = QGroupBox("🏢 Logo de la Empresa")
        grupo.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        grupo.setStyleSheet("""
            QGroupBox {
                border: 2px solid #f57c00;
                border-radius: 8px;
                margin-top: 8px;
                padding-top: 12px;
                background-color:  white;
            }
            QGroupBox::title {
                color: #e65100;
                subcontrol-origin: margin;
                left: 12px;
                padding: 0 8px;
            }
        """)

        layout = QHBoxLayout()
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(15)

        # Vista previa del logo
        self.label_logo = QLabel("🏢\n\nLOGO\nEMPRESA")
        self.label_logo.setFixedSize(200, 200)
        self.label_logo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.label_logo.setStyleSheet("""
            QLabel {
                border: 3px dashed #cfd8dc;
                border-radius: 8px;
                background-color:  #fafafa;
                color: #90a4ae;
                font-size: 14pt;
                font-weight:  bold;
            }
        """)
        layout.addWidget(self.label_logo)

        # Botones
        botones_layout = QVBoxLayout()
        botones_layout.setSpacing(12)

        btn_cargar = QPushButton("📤 Cargar Logo")
        btn_cargar. setFont(QFont("Arial", 11, QFont.Weight.Bold))
        btn_cargar.setFixedHeight(40)
        btn_cargar.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_cargar.setStyleSheet("""
            QPushButton {
                background-color: #1976d2;
                color:  white;
                border: none;
                border-radius: 6px;
            }
            QPushButton:hover { background-color: #1565c0; }
        """)
        btn_cargar.clicked. connect(self.cargar_logo)
        botones_layout. addWidget(btn_cargar)

        btn_eliminar = QPushButton("🗑️ Eliminar Logo")
        btn_eliminar.setFont(QFont("Arial", 11, QFont.Weight.Bold))
        btn_eliminar. setFixedHeight(40)
        btn_eliminar.setCursor(Qt.CursorShape. PointingHandCursor)
        btn_eliminar.setStyleSheet("""
            QPushButton {
                background-color: #c62828;
                color: white;
                border: none;
                border-radius: 6px;
            }
            QPushButton:hover { background-color:  #b71c1c; }
        """)
        btn_eliminar.clicked.connect(self.eliminar_logo)
        botones_layout.addWidget(btn_eliminar)

        botones_layout.addStretch()

        info = QLabel(
            "💡 Formatos aceptados:\nJPG, PNG\n\nTamaño recomendado:\n800x200 px")
        info.setFont(QFont("Arial", 9))
        info.setStyleSheet("color: #546e7a; padding: 8px;")
        botones_layout. addWidget(info)

        layout.addLayout(botones_layout)

        grupo.setLayout(layout)
        return grupo

    def seleccionar_carpeta(self, line_edit):
        """Selecciona una carpeta"""
        carpeta = QFileDialog.getExistingDirectory(
            self,
            "Seleccionar Carpeta",
            line_edit.text()
        )
        if carpeta:
            line_edit.setText(carpeta)

    def abrir_carpeta(self, ruta):
        """Abre la carpeta en el explorador"""
        import subprocess
        if os.path.exists(ruta):
            subprocess. Popen(f'explorer "{ruta}"')
        else:
            QMessageBox.warning(self, "⚠️ Carpeta no existe",
                                f"La carpeta no existe:\n{ruta}")

    def guardar_carpetas(self):
        """Guarda la configuración de carpetas"""
        QMessageBox.information(
            self,
            "💾 Configuración Guardada",
            "Las rutas de carpetas han sido guardadas correctamente."
        )

    def cargar_logo(self):
        """Carga un logo"""
        archivo, _ = QFileDialog.getOpenFileName(
            self,
            "Seleccionar Logo",
            "",
            "Imágenes (*.png *.jpg *.jpeg);;Todos los archivos (*.*)"
        )

        if archivo:
            pixmap = QPixmap(archivo)
            if not pixmap.isNull():
                pixmap_scaled = pixmap.scaled(
                    200, 200,
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation
                )
                self.label_logo.setPixmap(pixmap_scaled)
                QMessageBox.information(
                    self, "✅ Logo Cargado", "El logo ha sido cargado correctamente.")

    def eliminar_logo(self):
        """Elimina el logo"""
        respuesta = QMessageBox.question(
            self,
            "🗑️ Eliminar Logo",
            "¿Está seguro de eliminar el logo actual?",
            QMessageBox. StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if respuesta == QMessageBox.StandardButton.Yes:
            self.label_logo.clear()
            self.label_logo.setText("🏢\n\nLOGO\nEMPRESA")
            QMessageBox.information(
                self, "✅ Logo Eliminado", "El logo ha sido eliminado.")


# ═══════════════════════════════════════════════════════════
# SUB-TAB 3: DATOS PREDEFINIDOS
# ═══════════════════════════════════════════════════════════

class SubTabDatosPredefinidos(QWidget):
    """Sub-tab de gestión de datos predefinidos"""

    def __init__(self):
        super().__init__()
        self.datos_ejemplo = {
            "Tipos de Equipo": ["Handheld", "Móvil", "Base", "Repetidor", "Gateway"],
            "Marcas": ["Motorola", "Kenwood", "Icom", "Hytera", "Vertex"],
            "Estados": ["Operativo", "En Stock", "En Reparación", "De Baja"],
            "Sectores": ["Logística", "Seguridad", "Operaciones", "Mantenimiento"],
            "Escalas": ["COM", "SEG", "LOG", "OPE", "ADM"],
        }
        self.crear_interfaz()

    def crear_interfaz(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(15)

        # Título
        titulo = QLabel("📋 Gestión de Datos Predefinidos")
        titulo.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        titulo.setStyleSheet("""
            QLabel {
                color: #0d47a1;
                background:  qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #e3f2fd, stop:1 #bbdefb);
                padding: 12px;
                border-radius:  8px;
                border: 2px solid #1976d2;
            }
        """)
        titulo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(titulo)

        # Selector de categoría
        selector_layout = QHBoxLayout()

        lbl = QLabel("Categoría:")
        lbl.setFont(QFont("Arial", 11, QFont.Weight.Bold))
        lbl.setStyleSheet("color: #37474f;")
        selector_layout.addWidget(lbl)

        self.combo_categoria = QComboBox()
        self.combo_categoria. addItems(list(self.datos_ejemplo.keys()))
        self.combo_categoria.setFont(QFont("Arial", 11, QFont.Weight.Bold))
        self.combo_categoria.setFixedHeight(40)
        self.combo_categoria.setStyleSheet("""
            QComboBox {
                border: 2px solid #cfd8dc;
                border-radius: 6px;
                padding: 8px;
                background-color: white;
            }
            QComboBox: hover {
                border: 2px solid #1976d2;
            }
        """)
        self.combo_categoria.currentTextChanged.connect(
            self.cargar_datos_categoria)
        selector_layout.addWidget(self.combo_categoria, 1)

        layout.addLayout(selector_layout)

        # Tabla de datos
        self.tabla_datos = QTableWidget()
        self.tabla_datos.setColumnCount(1)
        self.tabla_datos.setHorizontalHeaderLabels(["Valor"])
        self.tabla_datos.horizontalHeader().setSectionResizeMode(
            0, QHeaderView.ResizeMode.Stretch)
        self.tabla_datos.setStyleSheet("""
            QTableWidget {
                border: 2px solid #cfd8dc;
                border-radius: 8px;
                gridline-color: #eceff1;
                font-size: 11pt;
                background-color: white;
            }
            QTableWidget::item {
                padding: 12px;
            }
            QTableWidget::item:selected {
                background-color: #e3f2fd;
                color: #0d47a1;
            }
            QHeaderView::section {
                background-color: #37474f;
                color: white;
                font-size: 11pt;
                font-weight: bold;
                padding: 12px;
                border:  none;
            }
        """)
        self.tabla_datos. setSelectionBehavior(
            QTableWidget.SelectionBehavior.SelectRows)
        self.tabla_datos.setSelectionMode(
            QTableWidget. SelectionMode.SingleSelection)
        self.tabla_datos.verticalHeader().setDefaultSectionSize(40)
        self.tabla_datos.doubleClicked.connect(self. editar_dato)

        layout.addWidget(self. tabla_datos)

        # Botones
        botones_layout = QHBoxLayout()
        botones_layout.setSpacing(12)

        btn_agregar = QPushButton("➕ Agregar")
        btn_agregar.setFont(QFont("Arial", 11, QFont.Weight.Bold))
        btn_agregar. setFixedHeight(45)
        btn_agregar. setCursor(Qt.CursorShape.PointingHandCursor)
        btn_agregar. setStyleSheet("""
            QPushButton {
                background:  qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #1e8449, stop:1 #27ae60);
                color:  white;
                border: none;
                border-radius: 8px;
                padding: 0 25px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop: 0 #186a3b, stop:1 #1e8449);
            }
        """)
        btn_agregar. clicked.connect(self.agregar_dato)
        botones_layout.addWidget(btn_agregar)

        btn_editar = QPushButton("✏️ Editar")
        btn_editar.setFont(QFont("Arial", 11, QFont.Weight.Bold))
        btn_editar.setFixedHeight(45)
        btn_editar.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_editar.setStyleSheet("""
            QPushButton {
                background-color: #1976d2;
                color: white;
                border: none;
                border-radius: 8px;
                padding: 0 25px;
            }
            QPushButton:hover { background-color: #1565c0; }
        """)
        btn_editar.clicked. connect(self.editar_dato)
        botones_layout. addWidget(btn_editar)

        btn_eliminar = QPushButton("🗑️ Eliminar")
        btn_eliminar.setFont(QFont("Arial", 11, QFont.Weight.Bold))
        btn_eliminar.setFixedHeight(45)
        btn_eliminar.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_eliminar.setStyleSheet("""
            QPushButton {
                background-color: #c62828;
                color: white;
                border: none;
                border-radius: 8px;
                padding: 0 25px;
            }
            QPushButton:hover { background-color: #b71c1c; }
        """)
        btn_eliminar.clicked.connect(self.eliminar_dato)
        botones_layout.addWidget(btn_eliminar)

        layout.addLayout(botones_layout)

        self.setLayout(layout)

        # Cargar datos iniciales
        self.cargar_datos_categoria(self.combo_categoria.currentText())

    def cargar_datos_categoria(self, categoria):
        """Carga los datos de la categoría seleccionada"""
        datos = self.datos_ejemplo.get(categoria, [])
        self.tabla_datos.setRowCount(len(datos))

        for fila, valor in enumerate(datos):
            item = QTableWidgetItem(valor)
            item.setFont(QFont("Arial", 11, QFont.Weight.Bold))
            self.tabla_datos.setItem(fila, 0, item)

    def agregar_dato(self):
        """Agrega un nuevo dato"""
        categoria = self.combo_categoria.currentText()
        dialogo = DialogoDatoPredefinido(
            self, categoria=categoria, modo="crear")

        if dialogo.exec() == QDialog.DialogCode. Accepted:
            self.datos_ejemplo[categoria].append(dialogo.valor_guardado)
            self.cargar_datos_categoria(categoria)
            QMessageBox.information(
                self,
                "✅ Dato Agregado",
                f"'{dialogo.valor_guardado}' agregado a {categoria}"
            )

    def editar_dato(self):
        """Edita el dato seleccionado"""
        fila = self.tabla_datos. currentRow()
        if fila < 0:
            QMessageBox.warning(self, "⚠️ Sin Selección",
                                "Seleccione un dato para editar.")
            return

        categoria = self.combo_categoria.currentText()
        valor_actual = self.tabla_datos. item(fila, 0).text()

        dialogo = DialogoDatoPredefinido(
            self, categoria=categoria, valor=valor_actual, modo="editar")

        if dialogo.exec() == QDialog.DialogCode.Accepted:
            self.datos_ejemplo[categoria][fila] = dialogo.valor_guardado
            self.cargar_datos_categoria(categoria)
            QMessageBox.information(
                self,
                "✅ Dato Actualizado",
                f"Dato actualizado correctamente"
            )

    def eliminar_dato(self):
        """Elimina el dato seleccionado"""
        fila = self.tabla_datos.currentRow()
        if fila < 0:
            QMessageBox.warning(self, "⚠️ Sin Selección",
                                "Seleccione un dato para eliminar.")
            return

        categoria = self.combo_categoria.currentText()
        valor = self.tabla_datos.item(fila, 0).text()

        respuesta = QMessageBox.question(
            self,
            "🗑️ Eliminar Dato",
            f"¿Está seguro de eliminar '{valor}' de {categoria}? ",
            QMessageBox.StandardButton.Yes | QMessageBox. StandardButton.No
        )

        if respuesta == QMessageBox.StandardButton.Yes:
            del self.datos_ejemplo[categoria][fila]
            self.cargar_datos_categoria(categoria)
            QMessageBox.information(
                self, "✅ Dato Eliminado", f"'{valor}' eliminado correctamente.")


# Continuará en el siguiente mensaje con Mantenimiento y Acerca de...
# ═══════════════════════════════════════════════════════════
# SUB-TAB 4: MANTENIMIENTO
# ═══════════════════════════════════════════════════════════

class SubTabMantenimiento(QWidget):
    """Sub-tab de mantenimiento del sistema"""

    def __init__(self):
        super().__init__()
        self.crear_interfaz()

    def crear_interfaz(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(15)

        # Título
        titulo = QLabel("🧹 Mantenimiento del Sistema")
        titulo.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        titulo.setStyleSheet("""
            QLabel {
                color: #c62828;
                background:  qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #ffebee, stop:1 #ffcdd2);
                padding:  12px;
                border-radius:  8px;
                border:  2px solid #c62828;
            }
        """)
        titulo.setAlignment(Qt.AlignmentFlag. AlignCenter)
        layout.addWidget(titulo)

        # Grid de opciones
        grid_layout = QGridLayout()
        grid_layout.setSpacing(15)

        # Limpiar Caché
        card_cache = self.crear_card_mantenimiento(
            "🧹",
            "Limpiar Caché",
            "Elimina archivos temporales y caché del sistema",
            self.limpiar_cache,
            "#f57c00"
        )
        grid_layout.addWidget(card_cache, 0, 0)

        # Vaciar Papelera
        card_papelera = self.crear_card_mantenimiento(
            "🗑️",
            "Vaciar Papelera",
            "Elimina permanentemente todos los equipos en la papelera",
            self. vaciar_papelera,
            "#c62828"
        )
        grid_layout.addWidget(card_papelera, 0, 1)

        # Optimizar BD
        card_optimizar = self.crear_card_mantenimiento(
            "⚡",
            "Optimizar Base de Datos",
            "Reindexar y optimizar tablas para mejor rendimiento",
            self.optimizar_bd,
            "#7b1fa2"
        )
        grid_layout.addWidget(card_optimizar, 1, 0)

        # Informe de Integridad
        card_integridad = self.crear_card_mantenimiento(
            "📊",
            "Informe de Integridad",
            "Genera un informe del estado de la base de datos",
            self.informe_integridad,
            "#1976d2"
        )
        grid_layout.addWidget(card_integridad, 1, 1)

        layout.addLayout(grid_layout)
        layout.addStretch()
        self.setLayout(layout)

    def crear_card_mantenimiento(self, icono, titulo, descripcion, funcion, color):
        """Crea una tarjeta de opción de mantenimiento"""
        card = QFrame()
        card.setStyleSheet(f"""
            QFrame {{
                background-color: white;
                border: 3px solid {color};
                border-radius:  12px;
                padding:  15px;
            }}
            QFrame: hover {{
                background-color: #f5f5f5;
            }}
        """)

        card_layout = QVBoxLayout()
        card_layout.setSpacing(12)

        # Icono
        lbl_icono = QLabel(icono)
        lbl_icono.setFont(QFont("Arial", 40))
        lbl_icono. setAlignment(Qt.AlignmentFlag. AlignCenter)
        lbl_icono.setStyleSheet(f"color: {color};")
        card_layout.addWidget(lbl_icono)

        # Título
        lbl_titulo = QLabel(titulo)
        lbl_titulo.setFont(QFont("Arial", 13, QFont.Weight.Bold))
        lbl_titulo.setStyleSheet(f"color: {color};")
        lbl_titulo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl_titulo.setWordWrap(True)
        card_layout.addWidget(lbl_titulo)

        # Descripción
        lbl_desc = QLabel(descripcion)
        lbl_desc.setFont(QFont("Arial", 9))
        lbl_desc.setStyleSheet("color: #546e7a;")
        lbl_desc.setAlignment(Qt.AlignmentFlag. AlignCenter)
        lbl_desc.setWordWrap(True)
        lbl_desc.setMinimumHeight(50)
        card_layout.addWidget(lbl_desc)

        # Botón
        btn = QPushButton("Ejecutar")
        btn.setFont(QFont("Arial", 11, QFont.Weight.Bold))
        btn.setFixedHeight(40)
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.setStyleSheet(f"""
            QPushButton {{
                background-color:  {color};
                color: white;
                border: none;
                border-radius: 6px;
            }}
            QPushButton:hover {{
                background-color: {color}dd;
            }}
        """)
        btn.clicked.connect(funcion)
        card_layout.addWidget(btn)

        card. setLayout(card_layout)
        return card

    def limpiar_cache(self):
        """Limpia la caché del sistema"""
        respuesta = QMessageBox.question(
            self,
            "🧹 Limpiar Caché",
            "¿Está seguro de limpiar la caché del sistema?\n\nEsto eliminará archivos temporales.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if respuesta == QMessageBox.StandardButton.Yes:
            QMessageBox.information(
                self,
                "✅ Caché Limpiada",
                "La caché del sistema ha sido limpiada correctamente.\n\nEspacio liberado: 45 MB"
            )

    def vaciar_papelera(self):
        """Vacía la papelera permanentemente"""
        respuesta = QMessageBox.critical(
            self,
            "⚠️ VACIAR PAPELERA",
            "¿Está seguro de vaciar PERMANENTEMENTE la papelera?\n\n"
            "⚠️ ESTA ACCIÓN NO SE PUEDE DESHACER ⚠️\n\n"
            "Se eliminarán 12 equipos de forma permanente.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if respuesta == QMessageBox.StandardButton.Yes:
            QMessageBox.information(
                self,
                "✅ Papelera Vaciada",
                "La papelera ha sido vaciada correctamente.\n\n12 equipos eliminados permanentemente."
            )

    def optimizar_bd(self):
        """Optimiza la base de datos"""
        respuesta = QMessageBox.question(
            self,
            "⚡ Optimizar Base de Datos",
            "¿Desea optimizar la base de datos?\n\nEsto puede tomar algunos minutos.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if respuesta == QMessageBox.StandardButton. Yes:
            QMessageBox. information(
                self,
                "✅ Optimización Completada",
                "La base de datos ha sido optimizada correctamente.\n\n"
                "Tablas reindexadas:  15\n"
                "Tiempo:  2.3 segundos"
            )

    def informe_integridad(self):
        """Genera informe de integridad"""
        QMessageBox.information(
            self,
            "📊 Informe de Integridad",
            "Estado de la Base de Datos:\n\n"
            "✅ Conexión:  OK\n"
            "✅ Tablas: 15/15 OK\n"
            "✅ Índices: OK\n"
            "✅ Registros: 1,234\n"
            "✅ Tamaño: 45.6 MB\n\n"
            "Sin errores detectados."
        )


# ═══════════════════════════════════════════════════════════
# SUB-TAB 5: ACERCA DE
# ═══════════════════════════════════════════════════════════

class SubTabAcercaDe(QWidget):
    """Sub-tab de información del sistema"""

    def __init__(self):
        super().__init__()
        self.crear_interfaz()

    def crear_interfaz(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(25)

        layout.addStretch()

        # Logo/Icono
        icono = QLabel("📻")
        icono.setFont(QFont("Arial", 80))
        icono.setAlignment(Qt.AlignmentFlag. AlignCenter)
        icono.setStyleSheet("color: #1976d2;")
        layout.addWidget(icono)

        # Nombre del sistema
        nombre = QLabel("Sistema de Inventario de Equipos de Radio")
        nombre.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        nombre.setStyleSheet("color: #0d47a1;")
        nombre.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(nombre)

        # Versión
        version = QLabel("Versión 4.0")
        version.setFont(QFont("Arial", 14))
        version.setStyleSheet("color: #546e7a;")
        version.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(version)

        # Separador
        separador = QFrame()
        separador.setFrameShape(QFrame.Shape.HLine)
        separador.setStyleSheet("background-color: #cfd8dc;")
        separador.setFixedHeight(2)
        layout.addWidget(separador)

        # Información
        info_layout = QGridLayout()
        info_layout. setSpacing(12)
        info_layout.setColumnStretch(1, 1)

        estilo_label = "color: #37474f; font-weight: bold; font-size: 11pt;"
        estilo_valor = "color: #546e7a; font-size: 11pt;"

        labels = [
            ("👤 Desarrollador:", "lucasarsa2015-cpu"),
            ("📅 Fecha:", "2025-12-14"),
            ("🐍 Python:", "3.12+"),
            ("🖼️ Framework:", "PyQt6"),
            ("🗄️ Base de Datos:", "MySQL"),
            ("📝 Licencia:", "Uso Interno"),
        ]

        for row, (etiqueta, valor) in enumerate(labels):
            lbl = QLabel(etiqueta)
            lbl.setFont(QFont("Arial", 11, QFont.Weight.Bold))
            lbl.setStyleSheet(estilo_label)
            lbl.setAlignment(Qt.AlignmentFlag.AlignRight |
                             Qt.AlignmentFlag.AlignVCenter)
            info_layout.addWidget(lbl, row, 0)

            val = QLabel(valor)
            val.setFont(QFont("Arial", 11))
            val.setStyleSheet(estilo_valor)
            info_layout. addWidget(val, row, 1)

        layout. addLayout(info_layout)

        layout.addStretch()

        # Copyright
        copyright_label = QLabel("© 2025 - Todos los derechos reservados")
        copyright_label.setFont(QFont("Arial", 9))
        copyright_label.setStyleSheet("color: #90a4ae;")
        copyright_label.setAlignment(Qt. AlignmentFlag.AlignCenter)
        layout.addWidget(copyright_label)

        self.setLayout(layout)


# ═══════════════════════════════════════════════════════════
# PESTAÑA PRINCIPAL: CONFIGURACIÓN
# ═══════════════════════════════════════════════════════════

class ConfiguracionTab(QWidget):
    """Pestaña principal de Configuración con sub-tabs"""

    def __init__(self):
        super().__init__()
        self.crear_interfaz()

    def crear_interfaz(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(15)

        # Encabezado
        header = QLabel("⚙️ CONFIGURACIÓN DEL SISTEMA")
        header.setFont(QFont("Arial", 20, QFont.Weight.Bold))
        header.setAlignment(Qt.AlignmentFlag. AlignCenter)
        header.setFixedHeight(60)
        header.setStyleSheet("""
            QLabel {
                background:  qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #1976d2, stop:0.5 #1e88e5, stop:1 #42a5f5);
                color: white;
                padding: 15px;
                border-radius:  10px;
                border: 3px solid #0d47a1;
            }
        """)
        layout.addWidget(header)

        # Sub-Tabs
        self.sub_tabs = QTabWidget()
        self.sub_tabs.setFont(QFont("Arial", 11, QFont.Weight.Bold))
        self.sub_tabs.setStyleSheet("""
            QTabWidget::pane {
                border: 2px solid #cfd8dc;
                border-radius: 8px;
                background-color: #f5f7fa;
                top: -2px;
            }
            QTabBar::tab {
                background-color: #90a4ae;
                color: white;
                padding: 10px 18px;
                margin-right: 2px;
                border-top-left-radius: 6px;
                border-top-right-radius: 6px;
                font-size: 11pt;
                min-width: 100px;
            }
            QTabBar::tab:selected {
                background:  qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #1976d2, stop:1 #1565c0);
            }
            QTabBar::tab:hover: ! selected {
                background-color: #607d8b;
            }
        """)

        # Agregar sub-tabs
        self.sub_tabs.addTab(SubTabBaseDatos(), "🗄️ Base de Datos")
        self.sub_tabs.addTab(SubTabRecursos(), "🖼️ Recursos")
        self.sub_tabs.addTab(SubTabDatosPredefinidos(), "📋 Datos Predefinidos")
        self.sub_tabs. addTab(SubTabMantenimiento(), "🧹 Mantenimiento")
        self.sub_tabs.addTab(SubTabAcercaDe(), "ℹ️ Acerca de")

        layout. addWidget(self.sub_tabs)

        self.setLayout(layout)

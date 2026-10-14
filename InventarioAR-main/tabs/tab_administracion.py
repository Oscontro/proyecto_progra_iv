"""
Pestaña:     Administración de Usuarios
Versión:  5.0 - SIN DATOS PRECARGADOS
Fecha:  2025-12-15
Autor:  lucasarsa2015-cpu
Descripción:  Gestión completa de usuarios del sistema (VACÍO)
"""
from base_tab import ApiTab
from api_client import ApiError, SesionExpirada
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QTableWidget, QTableWidgetItem, QComboBox,
    QCheckBox, QFrame, QHeaderView, QMessageBox, QDialog,
    QGridLayout
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QBrush, QFont, QColor


# ═══════════════════════════════════════════════════════════
# DIÁLOGO:     CREAR/EDITAR USUARIO
# ═══════════════════════════════════════════════════════════

class DialogoUsuario(QDialog):
    """Ventana modal para crear o editar usuarios"""

    def __init__(self, api, parent=None, datos_usuario=None, modo="crear"):
        super().__init__(parent)
        self.api = api
        self.datos_usuario = datos_usuario
        self.modo = modo  # "crear" o "editar"
        self.configurar_ventana()
        self.crear_interfaz()

        # Si es edición, cargar datos existentes
        if modo == "editar" and datos_usuario:
            self.cargar_datos_existentes()

    def configurar_ventana(self):
        """Configuración inicial de la ventana"""
        titulo = "✨ Crear Nuevo Usuario" if self.modo == "crear" else "✏️ Editar Usuario"
        self.setWindowTitle(titulo)
        self.setModal(True)
        self.setFixedSize(700, 780)
        self.setStyleSheet("""
            QDialog {
                background-color: #f5f7fa;
            }
        """)

    def crear_interfaz(self):
        """Crea toda la interfaz del diálogo"""
        layout_principal = QVBoxLayout()
        layout_principal.setContentsMargins(30, 30, 30, 30)
        layout_principal.setSpacing(25)

        # ═══ ENCABEZADO ═══
        self.agregar_encabezado(layout_principal)

        # ═══ FORMULARIO ═══
        self.agregar_formulario(layout_principal)

        # ═══ BOTONES ═══
        self.agregar_botones(layout_principal)

        self.setLayout(layout_principal)

    def agregar_encabezado(self, layout):
        """Agrega el título del diálogo"""
        icono = "✨" if self.modo == "crear" else "✏️"
        texto = f"{icono} {'Crear Nuevo Usuario' if self.modo == 'crear' else 'Editar Usuario'}"

        titulo = QLabel(texto)
        titulo.setFont(QFont("Arial", 22, QFont.Weight.Bold))
        titulo.setStyleSheet("""
            QLabel {
                color: #0d47a1;
                background:     qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #e3f2fd, stop:1 #bbdefb);
                padding:  15px;
                border-radius:    10px;
                border: 2px solid #1976d2;
            }
        """)
        titulo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(titulo)

    def agregar_formulario(self, layout):
        """Agrega el formulario con todos los campos"""
        # Frame contenedor
        frame_formulario = QFrame()
        frame_formulario.setStyleSheet("""
            QFrame {
                background-color: white;
                border-radius: 12px;
                border: 2px solid #e0e0e0;
            }
        """)

        form_layout = QGridLayout()
        form_layout. setContentsMargins(30, 30, 30, 30)
        form_layout. setSpacing(17)
        form_layout.setColumnMinimumWidth(0, 200)
        form_layout.setColumnStretch(1, 1)

        # Estilos
        estilo_label = """
            QLabel {
                color:   #37474f;
                font-weight: bold;
                font-size: 14pt;
                font-family:   Arial;
            }
        """

        estilo_input = """
            QLineEdit, QComboBox {
                border: 2px solid #cfd8dc;
                border-radius: 8px;
                padding: 12px;
                font-size:    14pt;
                font-family: Arial;
                background-color: #fafafa;
                color: black;
            }
            QLineEdit:focus, QComboBox:focus {
                border:    2px solid #1976d2;
                background-color: white;
            }
            QLineEdit:disabled {
                background-color: #eceff1;
                color: #78909c;
            }
            QComboBox QAbstractItemView {
                color: black;               /* Color de letra del menú desplegable */
                selection-background-color: #1976d2; /* Fondo de la opción seleccionada/hover */

            }
        """

        fila = 0

        # ─── LEGAJO ───
        lbl_legajo = QLabel("👤 Legajo:")
        lbl_legajo.setStyleSheet(estilo_label)
        lbl_legajo.setAlignment(
            Qt.AlignmentFlag. AlignRight | Qt.AlignmentFlag.AlignVCenter)
        form_layout. addWidget(lbl_legajo, fila, 0)

        self.input_legajo = QLineEdit()
        self.input_legajo.setPlaceholderText("Ej: 12345")
        self.input_legajo.setFixedHeight(50)
        self.input_legajo.setStyleSheet(estilo_input)
        form_layout.addWidget(self.input_legajo, fila, 1)
        fila += 1

        # ─── USERNAME ───
        lbl_username = QLabel("👤 Usuario:")
        lbl_username.setStyleSheet(estilo_label)
        lbl_username.setAlignment(
            Qt.AlignmentFlag. AlignRight | Qt.AlignmentFlag.AlignVCenter)
        form_layout. addWidget(lbl_username, fila, 0)
        
        self.input_username = QLineEdit()
        self.input_username.setPlaceholderText("Ej: admin, user001")
        self.input_username.setFixedHeight(50)
        self.input_username.setStyleSheet(estilo_input)
        form_layout.addWidget(self.input_username, fila, 1)
        fila += 1

        # ─── NOMBRE ───
        lbl_nombre = QLabel("📝 Nombre:")
        lbl_nombre.setStyleSheet(estilo_label)
        lbl_nombre.setAlignment(
            Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        form_layout.addWidget(lbl_nombre, fila, 0)

        self.input_nombre = QLineEdit()
        self.input_nombre.setPlaceholderText("Nombre del usuario")
        self.input_nombre.setFixedHeight(50)
        self.input_nombre.setStyleSheet(estilo_input)
        form_layout.addWidget(self.input_nombre, fila, 1)
        fila += 1

        # ─── APELLIDO ───
        lbl_apellido = QLabel("📝 Apellido:")
        lbl_apellido.setStyleSheet(estilo_label)
        lbl_apellido.setAlignment(
            Qt.AlignmentFlag.AlignRight | Qt. AlignmentFlag.AlignVCenter)
        form_layout. addWidget(lbl_apellido, fila, 0)

        self.input_apellido = QLineEdit()
        self.input_apellido.setPlaceholderText("Apellido del usuario")
        self.input_apellido.setFixedHeight(50)
        self.input_apellido.setStyleSheet(estilo_input)
        form_layout.addWidget(self.input_apellido, fila, 1)
        fila += 1

        # ─── EMAIL ───
        lbl_email = QLabel("📧 Email:")
        lbl_email.setStyleSheet(estilo_label)
        lbl_email.setAlignment(Qt.AlignmentFlag.AlignRight |
                               Qt.AlignmentFlag.AlignVCenter)
        form_layout.addWidget(lbl_email, fila, 0)

        self.input_email = QLineEdit()
        self.input_email.setPlaceholderText("usuario@empresa.com")
        self.input_email.setFixedHeight(50)
        self.input_email.setStyleSheet(estilo_input)
        form_layout.addWidget(self.input_email, fila, 1)
        fila += 1

        # ─── PERFIL ───
        lbl_perfil = QLabel("🎭 Perfil / Rol:")
        lbl_perfil.setStyleSheet(estilo_label)
        lbl_perfil.setAlignment(
            Qt.AlignmentFlag. AlignRight | Qt.AlignmentFlag.AlignVCenter)
        form_layout.addWidget(lbl_perfil, fila, 0)

        self.combo_perfil = QComboBox()
        self.combo_perfil.addItems([
            "Técnico",
            "Administrador"
        ])
        self.combo_perfil.setFixedHeight(50)
        self.combo_perfil.setStyleSheet(estilo_input)
        form_layout.addWidget(self.combo_perfil, fila, 1)
        fila += 1

        # ─── ESTADO ───
        lbl_estado = QLabel("💡 Estado:")
        lbl_estado.setStyleSheet(estilo_label)
        lbl_estado.setAlignment(
            Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        form_layout.addWidget(lbl_estado, fila, 0)

        self.check_activo = QCheckBox("✅ Usuario Activo")
        self.check_activo.setChecked(True)
        self.check_activo.setFont(QFont("Arial", 13, QFont.Weight.Bold))
        self.check_activo.setStyleSheet("""
            QCheckBox {
                color: #1976d2;
                spacing: 10px;
            }
            QCheckBox::indicator {
                width: 25px;
                height: 25px;
            }
        """)
        form_layout.addWidget(self.check_activo, fila, 1)
        fila += 1

        # ─── INFORMACIÓN CONTRASEÑA ───
        if self.modo == "crear":
            info_password = QLabel("⚠️ La contraseña inicial será:     1234")
            info_password. setFont(QFont("Arial", 12, QFont.Weight.Bold))
            info_password.setStyleSheet("""
                QLabel {
                    color: #0d47a1;
                    background-color: #e3f2fd;
                    padding: 15px;
                    border-radius: 8px;
                    border: 2px solid #1976d2;
                }
            """)
            info_password.setAlignment(Qt.AlignmentFlag.AlignCenter)
            form_layout.addWidget(info_password, fila, 0, 1, 2)

        frame_formulario.setLayout(form_layout)
        layout.addWidget(frame_formulario)

    def agregar_botones(self, layout):
        """Agrega los botones de acción"""
        botones_layout = QHBoxLayout()
        botones_layout.setSpacing(15)

        # Botón Cancelar
        btn_cancelar = QPushButton("❌ Cancelar")
        btn_cancelar.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        btn_cancelar.setFixedHeight(55)
        btn_cancelar. setCursor(Qt.CursorShape.PointingHandCursor)
        btn_cancelar.setStyleSheet("""
            QPushButton {
                background-color:    #757575;
                color:  white;
                border: none;
                border-radius: 10px;
                padding: 0 35px;
            }
            QPushButton:hover {
                background-color: #616161;
            }
            QPushButton:pressed {
                background-color: #424242;
            }
        """)
        btn_cancelar.clicked. connect(self.reject)
        botones_layout. addWidget(btn_cancelar)

        # Botón Guardar
        icono_guardar = "💾"
        texto_guardar = f"{icono_guardar} Guardar Usuario" if self.modo == "crear" else f"{icono_guardar} Actualizar Usuario"

        btn_guardar = QPushButton(texto_guardar)
        btn_guardar.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        btn_guardar.setFixedHeight(55)
        btn_guardar.setCursor(Qt.CursorShape. PointingHandCursor)
        btn_guardar.setStyleSheet("""
            QPushButton {
                background:     qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #1e8449, stop:1 #27ae60);
                color: white;
                border: none;
                border-radius: 10px;
                padding: 0 35px;
            }
            QPushButton:hover {
                background:    qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #186a3b, stop:1 #1e8449);
            }
            QPushButton:pressed {
                background:  #145a32;
            }
        """)
        btn_guardar.clicked.connect(self.validar_y_guardar)
        botones_layout.addWidget(btn_guardar)

        layout.addLayout(botones_layout)

    def cargar_datos_existentes(self):
        """Carga los datos del usuario en modo edición"""
        if not self.datos_usuario:
            return

        self.input_legajo.setText(self.datos_usuario.get("legajo", ""))
        self.input_legajo.setEnabled(False)  # No se puede cambiar el legajo
        self.input_username.setText(self.datos_usuario.get("username", ""))
        self.input_nombre.setText(self.datos_usuario.get("nombre", ""))
        self.input_apellido.setText(self.datos_usuario.get("apellido", ""))
        self.input_email.setText(self.datos_usuario.get("email", ""))

        # Buscar y seleccionar el perfil
        perfil = self.datos_usuario.get("perfil", "")
        for i in range(self.combo_perfil.count()):
            if perfil in self.combo_perfil.itemText(i):
                self. combo_perfil.setCurrentIndex(i)
                break

        self.check_activo.setChecked(self.datos_usuario.get("activo", True))

    def validar_y_guardar(self):
        """Valida los datos y guarda el usuario"""
        # Validar legajo
        legajo = self.input_legajo.text().strip()
        if not legajo:
            QMessageBox.warning(
                self,
                "⚠️ Campo Requerido",
                "El legajo es obligatorio."
            )
            self.input_legajo.setFocus()
            return

        # Validar username
        username = self.input_username.text().strip()
        if not username:
            QMessageBox.warning(
                self,
                "⚠️ Campo Requerido",
                "El username es obligatorio."
            )
            self.input_username.setFocus()
            return

        # Validar nombre
        nombre = self.input_nombre.text().strip()
        if not nombre:
            QMessageBox.warning(
                self,
                "⚠️ Campo Requerido",
                "El nombre es obligatorio."
            )
            self.input_nombre.setFocus()
            return

        # Validar apellido
        apellido = self.input_apellido.text().strip()
        if not apellido:
            QMessageBox.warning(
                self,
                "⚠️ Campo Requerido",
                "El apellido es obligatorio."
            )
            self.input_apellido.setFocus()
            return

        # Validar email (opcional pero si existe debe ser válido)
        email = self.input_email.text().strip()
        if email and "@" not in email:
            QMessageBox.warning(
                self,
                "⚠️ Email Inválido",
                "Por favor ingrese un email válido con formato:\nusuario@dominio.com"
            )
            self.input_email.setFocus()
            return
    
        datos = self.obtener_datos()
        if self.modo == "crear":
            try:
                self.api.post("alta_usuario.php", datos)

                accion = "creado" if self.modo == "crear" else "actualizado"
                QMessageBox.information(
                    self,
                    "✅ Éxito",
                    f"Usuario '{legajo}' {accion} correctamente.\n\n"
                    f"Username: {username}\n"
                    f"Nombre completo: {nombre} {apellido}\n"
                    f"Perfil: {self.combo_perfil.currentText()}\n\n"
                )
                
            except SesionExpirada:
                QMessageBox.warning(self, "Sesión expirada",
                    "Tu sesión venció. Cerrá y volvé a iniciar sesión.")
                return
            except ApiError as e:
                QMessageBox.critical(self, "Error", f"Creacion de usuario fallida:\n{e}")
                return
        else:
            try:
                self.api.post("modi_usuarios.php", datos)

                accion = "creado" if self.modo == "crear" else "actualizado"
                QMessageBox.information(
                    self,
                    "✅ Éxito",
                    f"Usuario '{legajo}' {accion} correctamente.\n\n"
                    f"Username: {username}\n"
                    f"Nombre completo: {nombre} {apellido}\n"
                    f"Perfil: {self.combo_perfil.currentText()}\n\n"
                )
                
            except SesionExpirada:
                QMessageBox.warning(self, "Sesión expirada",
                    "Tu sesión venció. Cerrá y volvé a iniciar sesión.")
                return
            except ApiError as e:
                QMessageBox.critical(self, "Error", f"Modificación de usuario fallida:\n{e}")
                return
        self.parent().obtener_usuarios()  # Actualizar la lista de usuarios en la pestaña principal
        self.accept()

    def obtener_datos(self):
        """Retorna los datos del formulario"""
        return {
            "legajo": self.input_legajo.text().strip(),
            "username": self.input_username.text().strip(),
            "nombre": self.input_nombre.text().strip(),
            "apellido": self.input_apellido.text().strip(),
            "email": self.input_email.text().strip(),
            "perfil": self.combo_perfil.currentText(),
            "activo": self.check_activo.isChecked()
        }


# ═══════════════════════════════════════════════════════════
# PESTAÑA PRINCIPAL:     ADMINISTRACIÓN
# ═══════════════════════════════════════════════════════════

class AdministracionTab(ApiTab):
    """Pestaña principal de administración de usuarios"""

    def __init__(self, api):
        super().__init__(api)
        self.api = api
        self.usuarios = []  # Lista VACÍA de usuarios
        self.crear_interfaz()
        self._actualizando = False
        self.obtener_usuarios()

    def crear_interfaz(self):
        """Crea toda la interfaz de la pestaña"""
        layout_principal = QVBoxLayout()
        layout_principal.setContentsMargins(20, 20, 20, 20)
        layout_principal.setSpacing(20)

        # ═══ ENCABEZADO ═══
        self.agregar_encabezado(layout_principal)

        # ═══ BARRA DE BÚSQUEDA ═══
        self.agregar_barra_busqueda(layout_principal)

        # ═══ TABLA DE USUARIOS ═══
        self.agregar_tabla(layout_principal)

        # ═══ BOTONES DE ACCIÓN ═══
        self.agregar_botones_accion(layout_principal)

        self.setLayout(layout_principal)

        self.renderizar_tabla()

    def agregar_encabezado(self, layout):
        """Agrega el encabezado de la pestaña"""
        header = QLabel("👤 ADMINISTRACIÓN DE USUARIOS")
        header.setFont(QFont("Arial", 26, QFont.Weight.Bold))
        header.setAlignment(Qt.AlignmentFlag.AlignCenter)
        header.setFixedHeight(80)
        header.setStyleSheet("""
            QLabel {
                background:     qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop: 0 #c62828, stop:0.5 #d32f2f, stop:1 #e53935);
                color: white;
                padding: 20px;
                border-radius: 12px;
                border: 3px solid #b71c1c;
            }
        """)
        layout.addWidget(header)

    def agregar_barra_busqueda(self, layout):
        """Agrega la barra de búsqueda y filtros"""
        search_layout = QHBoxLayout()
        search_layout.setSpacing(15)

        # Campo de búsqueda
        self.input_buscar = QLineEdit()
        self.input_buscar.setPlaceholderText(
            "🔍 Buscar por legajo, nombre o apellido...")
        self.input_buscar.setFixedHeight(50)
        self.input_buscar.setFont(QFont("Arial", 14))
        self.input_buscar.setStyleSheet("""
            QLineEdit {
                border: 2px solid #cfd8dc;
                border-radius: 10px;
                padding: 0 15px;
                background-color: white;
                color: #263238;
            }
            QLineEdit:focus {
                border:  2px solid #1976d2;
            }
        """)
        self.input_buscar.textChanged.connect(self.filtrar_usuarios)
        search_layout.addWidget(self.input_buscar, 1)

        # Filtro por perfil
        self.combo_filtro_perfil = QComboBox()
        self.combo_filtro_perfil.addItems([
            "Todos los Perfiles",
            "Técnico",
            "Administrador"
        ])
        self.combo_filtro_perfil.setFixedHeight(50)
        self.combo_filtro_perfil.setFixedWidth(250)
        self.combo_filtro_perfil.setFont(QFont("Arial", 13, QFont.Weight.Bold))
        self.combo_filtro_perfil.setStyleSheet("""
            QComboBox {
                border: 2px solid #cfd8dc;
                border-radius: 10px;
                padding: 10px;
                background-color:    white;
                color: #263238;
            }
            QComboBox:hover {
                border: 2px solid #1976d2;
            }
            QComboBox::drop-down {
                padding-right: 10px;
                color: #1976d2;
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
        """)
        self.combo_filtro_perfil.currentTextChanged.connect(
            self.filtrar_usuarios)
        search_layout.addWidget(self.combo_filtro_perfil)

        # Botón Crear Usuario
        btn_crear = QPushButton("➕ Crear Usuario")
        btn_crear.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        btn_crear.setFixedSize(200, 50)
        btn_crear.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_crear.setStyleSheet("""
            QPushButton {
                background:    qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #1e8449, stop:1 #27ae60);
                color: white;
                border: none;
                border-radius: 10px;
            }
            QPushButton:hover {
                background:  qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #186a3b, stop:1 #1e8449);
            }
            QPushButton:pressed {
                background:  #145a32;
            }
        """)
        btn_crear.clicked.connect(self. crear_usuario)
        search_layout.addWidget(btn_crear)

        layout.addLayout(search_layout)

    def agregar_tabla(self, layout):
        """Agrega la tabla de usuarios"""
        self.tabla_usuarios = QTableWidget()
        self.tabla_usuarios.setColumnCount(9)
        self.tabla_usuarios.setHorizontalHeaderLabels([
            "Legajo",
            "Username",
            "Nombre",
            "Apellido",
            "Email",
            "Perfil",
            "Activo",
            "Debe Cambiar Clave",
            "Última Conexión"
        ])

        # Estilo de la tabla
        self.tabla_usuarios.setStyleSheet("""
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
        header = self.tabla_usuarios.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode. Stretch)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(6, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(7, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(8, QHeaderView.ResizeMode.ResizeToContents)

        self.tabla_usuarios.verticalHeader().setDefaultSectionSize(60)
        self.tabla_usuarios.setSelectionBehavior(
            QTableWidget.SelectionBehavior.SelectRows)
        self.tabla_usuarios.setSelectionMode(
            QTableWidget.SelectionMode.SingleSelection)
        self.tabla_usuarios.setAlternatingRowColors(True)

        # Doble clic para editar
        self.tabla_usuarios.doubleClicked.connect(self.editar_usuario)

        # Tabla VACÍA
        self.tabla_usuarios.setRowCount(0)

        layout.addWidget(self.tabla_usuarios)

    def agregar_botones_accion(self, layout):
        """Agrega los botones de acción inferiores"""
        botones_layout = QHBoxLayout()
        botones_layout. setSpacing(15)

        # Botón Editar
        btn_editar = QPushButton("✏️ Editar")
        btn_editar.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        btn_editar.setFixedHeight(55)
        btn_editar. setCursor(Qt.CursorShape.PointingHandCursor)
        btn_editar. setStyleSheet("""
            QPushButton {
                background-color: #1976d2;
                color: white;
                border: none;
                border-radius: 10px;
                padding: 0 30px;
            }
            QPushButton:hover {
                background-color: #1565c0;
            }
            QPushButton:pressed {
                background-color: #0d47a1;
            }
        """)
        btn_editar.clicked.connect(self.editar_usuario)
        botones_layout.addWidget(btn_editar)

        # Botón Resetear Clave
        btn_reset = QPushButton("🔑 Resetear Clave")
        btn_reset.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        btn_reset.setFixedHeight(55)
        btn_reset.setCursor(Qt. CursorShape.PointingHandCursor)
        btn_reset.setStyleSheet("""
            QPushButton {
                background-color: #f57c00;
                color: white;
                border: none;
                border-radius: 10px;
                padding: 0 30px;
            }
            QPushButton:hover {
                background-color: #e65100;
            }
            QPushButton:pressed {
                background-color: #bf360c;
            }
        """)
        btn_reset.clicked.connect(self.resetear_clave)
        botones_layout.addWidget(btn_reset)

        # Botón Activar/Desactivar
        btn_toggle = QPushButton("⚡ Activar/Desactivar")
        btn_toggle.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        btn_toggle.setFixedHeight(55)
        btn_toggle. setCursor(Qt.CursorShape.PointingHandCursor)
        btn_toggle.setStyleSheet("""
            QPushButton {
                background-color:    #7b1fa2;
                color:    white;
                border: none;
                border-radius: 10px;
                padding: 0 30px;
            }
            QPushButton:hover {
                background-color:  #6a1b9a;
            }
            QPushButton:pressed {
                background-color: #4a148c;
            }
        """)
        btn_toggle.clicked.connect(self.toggle_activo)
        botones_layout.addWidget(btn_toggle)

        # Espaciador
        botones_layout.addStretch()

        # Botón Eliminar
        btn_eliminar = QPushButton("🗑️ Eliminar")
        btn_eliminar.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        btn_eliminar.setFixedHeight(55)
        btn_eliminar. setCursor(Qt.CursorShape.PointingHandCursor)
        btn_eliminar. setStyleSheet("""
            QPushButton {
                background-color: #c62828;
                color: white;
                border: none;
                border-radius: 10px;
                padding: 0 30px;
            }
            QPushButton:hover {
                background-color: #b71c1c;
            }
            QPushButton:pressed {
                background-color: #8e0000;
            }
        """)
        btn_eliminar.clicked.connect(self.eliminar_usuario)
        botones_layout.addWidget(btn_eliminar)

        layout.addLayout(botones_layout)

    def obtener_usuarios(self):
        """Obtiene la lista de usuarios desde la base de datos"""
        self._actualizando =  True # <- Bandera para bloquear la actualización de la tabla mientras se cargan los datos
        self.usuarios = []  # Reiniciar la lista de usuarios
        try:
            self.usuarios = self.api.get("usuarios.php")

        except SesionExpirada:
            QMessageBox.warning(self, "Sesión expirada",
                "Tu sesión venció. Cerrá y volvé a iniciar sesión.")
            self.usuarios = []

        except ApiError as e:
            QMessageBox.warning(self, "Error",
                f"No se pudieron cargar los datos del inventario:\n{e}")
            self.usuarios = []

        finally:
            # En un finally: si algo inesperado falla, el flag no queda
            # trabado en True y la pestaña sigue usable.
            self.renderizar_tabla()
            self._actualizando = False  # ← Desbloquear
        

    def renderizar_tabla(self):
        """Renderiza la tabla de usuarios con los datos obtenidos"""
        self.tabla_usuarios.setRowCount(0)  # Limpiar tabla

        for usuario in self.usuarios:
            fila = self.tabla_usuarios.rowCount()
            self.tabla_usuarios.insertRow(fila)

            # Legajo
            item_legajo = QTableWidgetItem(usuario.get("legajo", ""))
            item_legajo.setFlags(Qt.ItemFlag.ItemIsSelectable | Qt.ItemFlag.ItemIsEnabled)
            item_legajo.setForeground(QBrush(QColor("black")))
            self.tabla_usuarios.setItem(fila, 0, item_legajo)

            # Username
            item_username = QTableWidgetItem(usuario.get("username", ""))
            item_username.setFlags(Qt.ItemFlag.ItemIsSelectable | Qt.ItemFlag.ItemIsEnabled)
            item_username.setForeground(QBrush(QColor("black")))
            self.tabla_usuarios.setItem(fila, 1, item_username)

            # Nombre
            item_nombre = QTableWidgetItem(usuario.get("nombre", ""))
            item_nombre.setFlags(Qt.ItemFlag.ItemIsSelectable | Qt.ItemFlag.ItemIsEnabled)
            item_nombre.setForeground(QBrush(QColor("black")))
            self.tabla_usuarios.setItem(fila, 2, item_nombre)

            # Apellido
            item_apellido = QTableWidgetItem(usuario.get("apellido", ""))
            item_apellido.setFlags(Qt.ItemFlag.ItemIsSelectable | Qt.ItemFlag.ItemIsEnabled)
            item_apellido.setForeground(QBrush(QColor("black")))
            self.tabla_usuarios.setItem(fila, 3, item_apellido)

            # Email
            item_email = QTableWidgetItem(usuario.get("email", ""))
            item_email.setFlags(Qt.ItemFlag.ItemIsSelectable | Qt.ItemFlag.ItemIsEnabled)
            item_email.setForeground(QBrush(QColor("black")))
            self.tabla_usuarios.setItem(fila, 4, item_email)

            # Perfil
            item_perfil = QTableWidgetItem(usuario.get("perfil", ""))
            item_perfil.setFlags(Qt.ItemFlag.ItemIsSelectable | Qt.ItemFlag.ItemIsEnabled)
            item_perfil.setForeground(QBrush(QColor("black")))
            self.tabla_usuarios.setItem(fila, 5, item_perfil)

            # Activo
            activo_texto = "✅" if usuario.get("activo", True) else "❌"
            item_activo = QTableWidgetItem(activo_texto)
            item_activo.setFlags(Qt.ItemFlag.ItemIsSelectable | Qt.ItemFlag.ItemIsEnabled)
            item_activo.setForeground(QBrush(QColor("black")))
            item_activo.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.tabla_usuarios.setItem(fila, 6, item_activo)

            # Debe Cambiar Clave
            debe_cambiar_clave = "No" if usuario.get("debe_cambiar_clave", False) else "Sí"
            item_cambiar_clave = QTableWidgetItem(debe_cambiar_clave)
            item_cambiar_clave.setFlags(Qt.ItemFlag.ItemIsSelectable | Qt.ItemFlag.ItemIsEnabled)
            item_cambiar_clave.setForeground(QBrush(QColor("black")))
            self.tabla_usuarios.setItem(fila, 7, item_cambiar_clave)

            # Última Conexión
            ultima_conexion = usuario.get("ultima_conexion", "N/A")
            item_ultima_conexion = QTableWidgetItem(ultima_conexion)
            item_ultima_conexion.setFlags(Qt.ItemFlag.ItemIsSelectable | Qt.ItemFlag.ItemIsEnabled)
            item_ultima_conexion.setForeground(QBrush(QColor("black")))
            self.tabla_usuarios.setItem(fila, 8, item_ultima_conexion)


    def filtrar_usuarios(self):
        """Filtra la tabla según criterios de búsqueda"""
        texto_busqueda = self.input_buscar.text().lower()
        perfil_filtro = self.combo_filtro_perfil.currentText()

        for fila in range(self.tabla_usuarios.rowCount()):
            mostrar = True

            # Filtro de búsqueda por texto
            if texto_busqueda:
                legajo = self.tabla_usuarios.item(fila, 0).text().lower()
                username = self.tabla_usuarios.item(fila, 1).text().lower()
                nombre = self.tabla_usuarios.item(fila, 2).text().lower()
                apellido = self.tabla_usuarios.item(fila, 3).text().lower()

                if (texto_busqueda not in legajo and
                    texto_busqueda not in username and
                    texto_busqueda not in nombre and
                        texto_busqueda not in apellido):
                    mostrar = False

            # Filtro por perfil
            if perfil_filtro != "Todos los Perfiles" and mostrar:
                perfil_usuario = self.tabla_usuarios.item(fila, 5).text()
                nombre_filtro = perfil_filtro.split(
                    " ", 1)[1] if " " in perfil_filtro else perfil_filtro
                if nombre_filtro not in perfil_usuario:
                    mostrar = False

            self.tabla_usuarios.setRowHidden(fila, not mostrar)

    def crear_usuario(self):
        """Abre el diálogo para crear un nuevo usuario"""
        dialogo = DialogoUsuario(self.api, self, modo="crear")
        dialogo.exec()


    def editar_usuario(self):
        """Edita el usuario seleccionado"""
        fila_seleccionada = self.tabla_usuarios.currentRow()

        if fila_seleccionada < 0:
            QMessageBox.warning(
                self,
                "⚠️ Sin Selección",
                "Por favor, seleccione un usuario de la tabla para editar."
            )
            return

        # Obtener datos del usuario seleccionado
        datos_usuario = {
            "legajo": self.tabla_usuarios.item(fila_seleccionada, 0).text(),
            "username" : self.tabla_usuarios.item(fila_seleccionada, 1).text(),
            "nombre":  self.tabla_usuarios.item(fila_seleccionada, 2).text(),
            "apellido": self.tabla_usuarios.item(fila_seleccionada, 3).text(),
            "email": self.tabla_usuarios.item(fila_seleccionada, 4).text(),
            "perfil":  self.tabla_usuarios.item(fila_seleccionada, 5).text(),
            "activo": "✅" in self.tabla_usuarios.item(fila_seleccionada, 6).text()
        }

        # Abrir diálogo de edición
        dialogo = DialogoUsuario(
            self.api, self, datos_usuario=datos_usuario, modo="editar")
        dialogo.exec()

    def resetear_clave(self):
        """Resetea la contraseña del usuario a 1234"""
        fila_seleccionada = self.tabla_usuarios.currentRow()

        if fila_seleccionada < 0:
            QMessageBox.warning(
                self,
                "⚠️ Sin Selección",
                "Por favor, seleccione un usuario de la tabla."
            )
            return

        legajo = self.tabla_usuarios.item(fila_seleccionada, 0).text()

        respuesta = QMessageBox.question(
            self,
            "🔑 Resetear Contraseña",
            f"¿Confirma resetear la contraseña del usuario '{legajo}' a 1234?\n\n"
            "El usuario deberá cambiarla en su próximo ingreso.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if respuesta == QMessageBox.StandardButton.Yes:
            try:
                self.api.post("resetear_clave.php", {"legajo": legajo})
                QMessageBox.information(
                    self,
                    "✅ Contraseña Reseteada",
                    f"La contraseña del usuario '{legajo}' ha sido reseteada a 1234."
                )
            except SesionExpirada:
                QMessageBox.warning(self, "Sesión expirada",
                    "Tu sesión venció. Cerrá y volvé a iniciar sesión.")
                return
            except ApiError as e:
                QMessageBox.critical(self, "Error", f"Error al resetear la contraseña:\n{e}")
                return
            
        self.obtener_usuarios()  # Actualizar la lista de usuarios en la pestaña principal

    def toggle_activo(self):
        """Activa o desactiva un usuario"""
        fila_seleccionada = self.tabla_usuarios.currentRow()

        if fila_seleccionada < 0:
            QMessageBox.warning(
                self,
                "⚠️ Sin Selección",
                "Por favor, seleccione un usuario de la tabla."
            )
            return

        legajo = self.tabla_usuarios.item(fila_seleccionada, 0).text()
        estado_actual = self.tabla_usuarios.item(fila_seleccionada, 6).text()

        esta_activo = "✅" in estado_actual
        accion = "desactivar" if esta_activo else "activar"

        respuesta = QMessageBox.question(
            self,
            f"⚡ {accion. capitalize()} Usuario",
            f"¿Confirma {accion} al usuario '{legajo}'? ",
            QMessageBox.StandardButton.Yes | QMessageBox. StandardButton.No
        )

        if respuesta == QMessageBox.StandardButton.Yes:
            try:
                self.api.post("toggle_activo.php", {"legajo": legajo, "activo": not esta_activo})
                if (accion == "activar"):
                    QMessageBox.information(
                        self,
                        "✅ Estado Actualizado",
                    f"Usuario '{legajo}' activado.\n\n"
                    )
                else:
                    QMessageBox.information(
                        self,
                        "✅ Estado Actualizado",
                        f"Usuario '{legajo}' desactivado.\n\n"
                    )
            except SesionExpirada:
                QMessageBox.warning(self, "Sesión expirada",
                    "Tu sesión venció. Cerrá y volvé a iniciar sesión.")
                return
            except ApiError as e:
                QMessageBox.critical(self, "Error", f"Error al cambiar estado del usuario:\n{e}")
                return
        self.obtener_usuarios()  # Actualizar la lista de usuarios en la pestaña principal

    def eliminar_usuario(self):
        """Elimina permanentemente un usuario"""
        fila_seleccionada = self. tabla_usuarios.currentRow()

        if fila_seleccionada < 0:
            QMessageBox.warning(
                self,
                "⚠️ Sin Selección",
                "Por favor, seleccione un usuario de la tabla para eliminar."
            )
            return

        legajo = self.tabla_usuarios.item(fila_seleccionada, 0).text()
        username = self.tabla_usuarios.item(fila_seleccionada, 1).text()
        nombre_completo = f"{self.tabla_usuarios.item(fila_seleccionada, 2).text()} {self.tabla_usuarios.item(fila_seleccionada, 3).text()}"

        respuesta = QMessageBox.critical(
            self,
            "⚠️ ELIMINAR USUARIO",
            f"¿CONFIRMA ELIMINAR PERMANENTEMENTE al usuario?\n\n"
            f"Username: {username}\n"
            f"Nombre:   {nombre_completo}\n\n"
            f"⚠️ ESTA ACCIÓN NO SE PUEDE DESHACER ⚠️",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if respuesta == QMessageBox.StandardButton. Yes:
            try:
                self.api.post("eliminar_usuario.php", {"legajo": legajo})
                QMessageBox. information(
                                self,
                                "✅ Usuario Eliminado",
                                f"El usuario '{username}' ha sido eliminado."
                            )
            except SesionExpirada:
                QMessageBox.warning(self, "Sesión expirada",
                    "Tu sesión venció. Cerrá y volvé a iniciar sesión.")
                return
            except ApiError as e:
                QMessageBox.critical(self, "Error", f"Error al eliminar usuario:\n{e}")
                return
        self.obtener_usuarios()  # Actualizar la lista de usuarios en la pestaña principal

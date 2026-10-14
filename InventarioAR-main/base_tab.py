"""
base_tab.py  —  Lógica común de API para todas las pestañas.
Guardalo en la carpeta tabs/ (o donde tengas los tab_*.py)

En vez de copiar llenar_combo en cada pestaña, todas heredan de acá.
Un solo lugar para arreglar, un solo lugar para mejorar.
"""

from PyQt6.QtWidgets import QWidget, QMessageBox

from api_client import ApiError, SesionExpirada


class ApiTab(QWidget):
    """Pestaña con acceso a la API autenticada."""

    def __init__(self, api):
        super().__init__()
        self.api = api

    # ─────────────────────────────────────────────────────────
    def llenar_combo(self, endpoint, combo, campo_json,
                     incluir_todos=False, incluir_escriba=False, incluir_total=False):
        """
        endpoint: archivo PHP (ej. 'marcas.php')
        combo: el objeto QComboBox
        campo_json: nombre de la clave en el JSON (ej. 'marca')
        """
        data = []
        try:
            # El token se adjunta solo; la URL base la conoce el cliente.
            data = self.api.get(endpoint)

            items = [str(obj[campo_json]) for obj in data]

            combo.clear()
            if incluir_todos:
                combo.addItem("Todos")
            elif incluir_escriba:
                combo.addItem("Escriba o seleccione")
            elif incluir_total:
                combo.addItem("Total")

            combo.addItems(items)

        except SesionExpirada:
            # Se propaga para que el que llame muestre UN solo aviso.
            raise

        except ApiError as e:
            QMessageBox.warning(self, "Error al cargar datos",
                                f"No se pudo cargar '{endpoint}':\n{e}")

        except KeyError:
            QMessageBox.warning(
                self, "Error de datos",
                f"El campo '{campo_json}' no existe en la respuesta de {endpoint}.")

        return data

    # ─────────────────────────────────────────────────────────
    def cargar_combos(self, definiciones):
        """Carga varios combos y avisa UNA sola vez si la sesión venció.

        definiciones: lista de tuplas (endpoint, combo, campo_json)
        o de dicts si necesitás pasar incluir_todos / incluir_escriba.
        """
        try:
            for d in definiciones:
                if isinstance(d, dict):
                    self.llenar_combo(**d)
                else:
                    endpoint, combo, campo = d
                    self.llenar_combo(endpoint, combo, campo, incluir_todos=True)

        except SesionExpirada:
            self.avisar_sesion_expirada()

    # ─────────────────────────────────────────────────────────
    def avisar_sesion_expirada(self):
        """Delega en VentanaPrincipal si existe; si no, avisa y listo."""
        ventana = self.window()
        if hasattr(ventana, "sesion_expirada"):
            ventana.sesion_expirada()
        else:
            QMessageBox.warning(self, "Sesión expirada",
                                "Tu sesión venció. Volvé a iniciar sesión.")


# ═════════════════════════════════════════════════════════════
# CÓMO USARLA EN CADA PESTAÑA
# ═════════════════════════════════════════════════════════════
#
# tab_inventario.py:
#
#     from base_tab import ApiTab
#
#     class InventarioTab(ApiTab):          # ← antes: QWidget
#         def __init__(self, api):
#             super().__init__(api)         # ← esto ya define self.api
#             ...resto de tu __init__...
#
#         def llenar_desplegables(self):
#             self.cargar_combos([
#                 ("tipos.php",              self.combo_filtro_tipo,   "tipo"),
#                 ("marcas.php",             self.combo_filtro_marca,  "marca"),
#                 ("modelos_inventario.php", self.combo_filtro_modelo, "modelo_equipo"),
#                 ("sectores.php",           self.combo_filtro_sector, "sector"),
#                 ("estados.php",            self.combo_filtro_estado, "estado"),
#                 ("escalas.php",            self.combo_filtro_escala, "escala"),
#             ])
#
#     Y borrás el llenar_combo local: lo hereda de ApiTab.
#
# tab_ingreso.py (la que también pide potencias.php):
#
#     class IngresoEquiposTab(ApiTab):
#         def __init__(self, api):
#             super().__init__(api)
#             ...
#
#         def llenar_desplegables(self):
#             self.cargar_combos([
#                 {"endpoint": "tipos.php", "combo": self.combo_tipo,
#                  "campo_json": "tipo", "incluir_escriba": True},
#                 ("potencias.php", self.combo_potencia, "potencia"),
#                 ...
#             ])

"""
Cliente de la API del Sistema de Inventario.
Guardar como api_client.py junto a main.py

Adaptado al formato de respuesta de tu API:
    éxito -> {"success": true, "data": {...}}
    error  -> {"error": "mensaje"}  con código HTTP 4xx/5xx
"""
import requests
import keyring
from keyring.errors import PasswordDeleteError

import direcciones

SERVICE = "inventario_radios"   # identificador para el Credential Manager


class ApiError(Exception):
    """Error controlado de la API (credenciales, bloqueo, etc.)."""
    pass


class SesionExpirada(ApiError):
    """El token ya no sirve: hay que volver a loguearse."""
    pass


class ApiClient:
    def __init__(self, base_url=None):
        self.base_url = (base_url or direcciones.URL.API_BASE_URL).rstrip("/")
        self.session = requests.Session()
        self.usuario = None
        self.es_admin = False
        self._token = None
        self._cargar_token()

    # ---------- manejo del token ----------
    def _cargar_token(self):
        """Recupera el token guardado del Credential Manager de Windows."""
        self._token = keyring.get_password(SERVICE, "auth_token")
        if self._token:
            self.session.headers["Authorization"] = f"Bearer {self._token}"

    def _guardar_token(self, token):
        self._token = token
        keyring.set_password(SERVICE, "auth_token", token)
        self.session.headers["Authorization"] = f"Bearer {token}"

    def borrar_token(self):
        self._token = None
        self.usuario = None
        self.es_admin = False
        try:
            keyring.delete_password(SERVICE, "auth_token")
        except PasswordDeleteError:
            pass   # no había nada guardado
        self.session.headers.pop("Authorization", None)

    @property
    def autenticado(self):
        return self._token is not None

    # ---------- procesamiento de respuestas ----------
    def _procesar(self, response):
        """Desenvuelve {"success":..., "data":...} o lanza la excepción adecuada."""
        try:
            cuerpo = response.json()
        except ValueError:
            raise ApiError(f"El servidor no devolvió JSON (código {response.status_code})")

        if response.status_code == 401:
            self.borrar_token()
            raise SesionExpirada(cuerpo.get("error", "Sesión expirada"))
        if response.status_code >= 400:
            raise ApiError(cuerpo.get("error", f"Error {response.status_code}"))

        return cuerpo.get("data", cuerpo)   # el contenido útil viene en "data"

    # ---------- endpoints ----------
    def login(self, usuario, password):
        try:
            r = self.session.post(
                f"{self.base_url}/login.php",
                json={"username": usuario, "password": password},
                timeout=10,
            )
            print(f"username: {usuario}, password: {password}")
        
        except requests.RequestException as e:
            raise ApiError(f"No se pudo conectar con el servidor:\n{e}")
        print(r.text)
        # En el login, un 401 significa credenciales malas, no sesión expirada.
        if r.status_code == 401:
            raise ApiError(r.json().get("error", "Usuario o contraseña incorrectos"))

        data = self._procesar(r)
        self._guardar_token(data["token"])
        self.usuario = data["user"]["username"]
        self.es_admin = bool(data["user"]["es_admin"])
        return data

    def logout(self):
        try:
            self.session.post(f"{self.base_url}/logout.php", timeout=5)
        except requests.RequestException:
            pass    # aunque falle la red, borramos el token local igual
        self.borrar_token()

    def verificar_sesion(self):
        """¿El token guardado sigue siendo válido? Útil al arrancar la app."""
        if not self._token:
            return False
        try:
            data = self.get("me.php")
            self.usuario = data["username"]
            self.es_admin = bool(data.get("es_admin", False))
            return True
        except (ApiError, SesionExpirada):
            return False

    # ---------- métodos genéricos para el resto de la app ----------
    def get(self, endpoint, params=None):
        """El token se adjunta solo, porque va en los headers de la Session."""
        try:
            r = self.session.get(f"{self.base_url}/{endpoint}",
                                 params=params, timeout=15)
        except requests.RequestException as e:
            raise ApiError(f"Error de conexión:\n{e}")
        return self._procesar(r)

    def post(self, endpoint, datos=None):
        try:
            r = self.session.post(f"{self.base_url}/{endpoint}",
                                  json=datos or {}, timeout=15)
        except requests.RequestException as e:
            raise ApiError(f"Error de conexión:\n{e}")
        return self._procesar(r)

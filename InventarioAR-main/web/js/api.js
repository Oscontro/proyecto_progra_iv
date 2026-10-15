// Cliente de la API del Sistema de Inventario (equivalente web de api_client.py).
//
// La sesión viaja en una cookie HttpOnly que crea login.php: el JavaScript
// nunca ve ni guarda el token. Cada pedido lleva X-Requested-With, que la
// API exige cuando autentica por cookie (protección CSRF).
//
// Formatos de respuesta que conviven en la API:
//   éxito (nuevo)  -> {"success": true, "data": ...}
//   éxito (viejo)  -> [...] o {...} sin envoltorio
//   error          -> {"error": "mensaje"} con código HTTP 4xx/5xx
//   error (viejo)  -> {"success": false, "message": "..."} con código 200

const API_BASE = new URL('../php/', document.baseURI);

export class ApiError extends Error {
    constructor(mensaje, status = 0, code = null) {
        super(mensaje);
        this.name = 'ApiError';
        this.status = status;
        this.code = code;
    }
}

/** El token ya no sirve: hay que volver a iniciar sesión. */
export class SesionExpirada extends ApiError {
    constructor(mensaje) {
        super(mensaje || 'Sesión expirada', 401);
        this.name = 'SesionExpirada';
    }
}

/** La cuenta tiene una clave temporal: hay que cambiarla antes de seguir. */
export class ClavePendiente extends ApiError {
    constructor(mensaje) {
        super(mensaje || 'Debés cambiar tu contraseña antes de continuar', 403, 'DEBE_CAMBIAR_CLAVE');
        this.name = 'ClavePendiente';
    }
}

// La aplicación se suscribe para reaccionar en un solo lugar
// (volver al login, forzar el cambio de clave), sin repetirlo en cada pestaña.
const oyentes = { sesionExpirada: [], clavePendiente: [] };

function avisar(evento, error) {
    for (const fn of oyentes[evento]) {
        fn(error);
    }
}

async function pedir(endpoint, { method = 'GET', params = null, datos = null, esLogin = false } = {}) {
    const url = new URL(endpoint, API_BASE);
    if (params) {
        for (const [clave, valor] of Object.entries(params)) {
            if (valor !== null && valor !== undefined) {
                url.searchParams.set(clave, valor);
            }
        }
    }

    const headers = { 'X-Requested-With': 'XMLHttpRequest', 'Accept': 'application/json' };
    const opciones = { method, headers, credentials: 'same-origin', cache: 'no-store' };
    if (datos !== null) {
        headers['Content-Type'] = 'application/json';
        opciones.body = JSON.stringify(datos);
    }

    let respuesta;
    try {
        respuesta = await fetch(url, opciones);
    } catch {
        throw new ApiError('No se pudo conectar con el servidor. Verificá tu conexión.');
    }

    const texto = await respuesta.text();
    let cuerpo;
    try {
        cuerpo = texto === '' ? null : JSON.parse(texto);
    } catch {
        // Casi siempre es un warning de PHP o HTML impreso antes del JSON.
        console.error('Respuesta no JSON de', endpoint, texto.slice(0, 300));
        throw new ApiError(`El servidor no devolvió JSON (código ${respuesta.status}).`, respuesta.status);
    }

    const esObjeto = cuerpo !== null && typeof cuerpo === 'object' && !Array.isArray(cuerpo);
    const mensaje = esObjeto ? (cuerpo.error || cuerpo.message || null) : null;
    const codigo = esObjeto ? (cuerpo.code || null) : null;

    if (respuesta.status === 401) {
        // En el login, un 401 son credenciales incorrectas, no una sesión vencida.
        if (esLogin) {
            throw new ApiError(mensaje || 'Usuario o contraseña incorrectos', 401);
        }
        const error = new SesionExpirada(mensaje);
        avisar('sesionExpirada', error);
        throw error;
    }
    if (respuesta.status === 403 && codigo === 'DEBE_CAMBIAR_CLAVE') {
        const error = new ClavePendiente(mensaje);
        avisar('clavePendiente', error);
        throw error;
    }
    if (respuesta.status === 403) {
        throw new ApiError(mensaje || 'No tenés permisos para esta acción', 403);
    }
    if (respuesta.status >= 400) {
        throw new ApiError(mensaje || `Error ${respuesta.status}`, respuesta.status, codigo);
    }
    if (esObjeto && cuerpo.success === false) {
        throw new ApiError(mensaje || 'La operación no se pudo completar', respuesta.status);
    }

    return esObjeto && 'data' in cuerpo ? cuerpo.data : cuerpo;
}

export const api = {
    get(endpoint, params = null) {
        return pedir(endpoint, { params });
    },

    post(endpoint, datos = {}) {
        return pedir(endpoint, { method: 'POST', datos });
    },

    /** Devuelve el usuario: {id, username, es_admin, debe_cambiar_clave}. */
    async login(username, password) {
        const data = await pedir('login.php', {
            method: 'POST',
            datos: { username, password },
            esLogin: true,
        });
        // data.token se ignora a propósito: la sesión queda en la cookie HttpOnly.
        return data.user;
    },

    async logout() {
        try {
            await pedir('logout.php', { method: 'POST', datos: {} });
        } catch {
            // Aunque falle la red, del lado del cliente la sesión se da por cerrada.
        }
    },

    /** Usuario de la sesión actual, o SesionExpirada si no hay sesión válida. */
    me() {
        return pedir('me.php');
    },

    cambiarClave(claveActual, nuevaClave) {
        return pedir('cambiar_clave.php', {
            method: 'POST',
            datos: { clave_actual: claveActual, nueva_clave: nuevaClave },
        });
    },

    alExpirarSesion(fn) {
        oyentes.sesionExpirada.push(fn);
    },

    alPedirCambioClave(fn) {
        oyentes.clavePendiente.push(fn);
    },
};

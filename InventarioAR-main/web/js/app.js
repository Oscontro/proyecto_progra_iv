// Punto de entrada de la aplicación web (zona protegida, app.php).
//
// Flujo:
//   1. app.php ya verificó en el servidor que hay una sesión de PHP válida;
//      el login lo hace la página ingresar.php.
//   2. me.php dice quién es el usuario. Con clave temporal -> cambio de clave obligatorio.
//   3. Si no, la ventana principal con las pestañas que corresponden al rol.
//   4. Si la sesión vence o se cierra, se vuelve a las páginas públicas.

import { api, ApiError, SesionExpirada, ClavePendiente } from './api.js';
import { plantilla, aviso, confirmar, ocupado, el } from './ui.js';
import { pestanasPara } from './pestanas.js';

const raiz = document.getElementById('app');

// Usuario de la sesión actual (null mientras no haya sesión).
let usuarioActual = null;

// ─────────────────────────────────────────────────────────
// Utilidades
// ─────────────────────────────────────────────────────────
function refs(nodo) {
    const mapa = {};
    nodo.querySelectorAll('[data-ref]').forEach((n) => { mapa[n.dataset.ref] = n; });
    return mapa;
}

function mostrarVista(nodo) {
    raiz.replaceChildren(nodo);
}

function mostrarError(parrafo, mensaje) {
    parrafo.textContent = mensaje;
    parrafo.hidden = !mensaje;
}

/** Sin sesión válida la aplicación no se muestra: página de error de acceso. */
function irASesionVencida() {
    location.replace('error.php?codigo=sesion_vencida');
}

async function salir() {
    await api.logout();
    location.replace('index.php?salida=1');
}

// ─────────────────────────────────────────────────────────
// Arranque
// ─────────────────────────────────────────────────────────
async function iniciar() {
    mostrarVista(plantilla('tpl-cargando'));
    try {
        entrar(await api.me());
    } catch (error) {
        if (error instanceof SesionExpirada) {
            irASesionVencida();
            return;
        }
        const vista = plantilla('tpl-error-inicio');
        const r = refs(vista);
        r.mensaje.textContent = error.message;
        r.reintentar.addEventListener('click', iniciar);
        mostrarVista(vista);
    }
}

/** Decide a dónde va un usuario recién autenticado. */
function entrar(usuario) {
    usuarioActual = usuario;
    if (usuario.debe_cambiar_clave) {
        vistaCambioClave({ obligatorio: true });
    } else {
        vistaPrincipal();
    }
}

// Reacciones globales a errores de sesión, vengan de la pestaña que vengan.
api.alExpirarSesion(() => {
    usuarioActual = null;
    irASesionVencida();
});

api.alPedirCambioClave(() => {
    if (usuarioActual) {
        usuarioActual.debe_cambiar_clave = true;
        vistaCambioClave({ obligatorio: true });
    }
});

// ─────────────────────────────────────────────────────────
// Cambio de contraseña (obligatorio tras clave temporal, u opcional)
// ─────────────────────────────────────────────────────────
function vistaCambioClave({ obligatorio }) {
    const vista = plantilla('tpl-cambio-clave');
    const r = refs(vista);
    const form = r.form;

    r.aviso.hidden = !obligatorio;
    r.leyenda.textContent = obligatorio
        ? 'Por seguridad, la contraseña temporal debe reemplazarse antes de usar el sistema.'
        : `Usuario: ${usuarioActual.username}`;

    // Si es obligatorio no se puede volver a la aplicación: solo cerrar sesión.
    r.cancelar.textContent = obligatorio ? 'Cerrar sesión' : 'Cancelar';
    r.cancelar.addEventListener('click', async () => {
        if (obligatorio) {
            await salir();
        } else {
            vistaPrincipal();
        }
    });

    form.addEventListener('submit', async (evento) => {
        evento.preventDefault();
        const actual = form.actual.value;
        const nueva = form.nueva.value;
        const repetir = form.repetir.value;

        // Validaciones del lado del cliente (buena experiencia; el servidor las repite).
        if (!actual || !nueva) {
            mostrarError(r.error, 'Completá todos los campos.');
            return;
        }
        if (nueva.length < 8) {
            mostrarError(r.error, 'La nueva contraseña debe tener al menos 8 caracteres.');
            form.nueva.focus();
            return;
        }
        if (nueva !== repetir) {
            mostrarError(r.error, 'Las contraseñas nuevas no coinciden.');
            form.repetir.focus();
            return;
        }

        mostrarError(r.error, '');
        try {
            await ocupado(form, () => api.cambiarClave(actual, nueva));
            usuarioActual.debe_cambiar_clave = false;
            aviso('Contraseña actualizada correctamente.', 'exito');
            vistaPrincipal();
        } catch (error) {
            if (error instanceof SesionExpirada) {
                return; // el oyente global ya llevó a la página de sesión vencida
            }
            // Acá cae "clave actual incorrecta", "debe ser distinta", etc.
            mostrarError(r.error, error.message);
        }
    });

    mostrarVista(vista);
    form.actual.focus();
}

// ─────────────────────────────────────────────────────────
// Ventana principal con pestañas
// ─────────────────────────────────────────────────────────
function vistaPrincipal() {
    const vista = plantilla('tpl-principal');
    const r = refs(vista);
    const usuario = usuarioActual;
    const ctx = { api, usuario };

    r.icono.textContent = usuario.es_admin ? '👨‍💼' : '👤';
    r.nombre.textContent = `Usuario: ${usuario.username}`;
    r.rol.textContent = usuario.es_admin ? 'Administrador' : 'Usuario';

    r.salir.addEventListener('click', async () => {
        const ok = await confirmar('Cerrar sesión', '¿Está seguro que desea cerrar la sesión?',
                                   { aceptar: 'Cerrar sesión', peligro: true });
        if (ok) {
            await salir();
        }
    });
    r['cambiar-clave'].addEventListener('click', () => vistaCambioClave({ obligatorio: false }));

    const pestanas = pestanasPara(usuario);
    const montadas = new Map(); // id -> { panel, instancia }
    const botones = new Map();

    for (const pestana of pestanas) {
        const boton = el('button', {
            type: 'button', role: 'tab', id: `tab-${pestana.id}`,
            'aria-controls': `panel-${pestana.id}`, 'aria-selected': 'false', tabindex: '-1',
            onclick: () => activar(pestana.id),
        }, el('span', { 'aria-hidden': 'true' }, pestana.icono), ` ${pestana.titulo}`);
        botones.set(pestana.id, boton);
        r.pestanas.append(boton);
    }

    // Navegación con flechas entre pestañas (patrón ARIA tablist).
    r.pestanas.addEventListener('keydown', (evento) => {
        const ids = pestanas.map((p) => p.id);
        const actual = ids.indexOf(document.activeElement?.id?.replace('tab-', ''));
        if (actual === -1) {
            return;
        }
        let destino = null;
        if (evento.key === 'ArrowRight') destino = (actual + 1) % ids.length;
        if (evento.key === 'ArrowLeft') destino = (actual - 1 + ids.length) % ids.length;
        if (evento.key === 'Home') destino = 0;
        if (evento.key === 'End') destino = ids.length - 1;
        if (destino !== null) {
            evento.preventDefault();
            activar(ids[destino]);
            botones.get(ids[destino]).focus();
        }
    });

    async function activar(id) {
        const pestana = pestanas.find((p) => p.id === id) || pestanas[0];

        for (const [otroId, boton] of botones) {
            const activa = otroId === pestana.id;
            boton.setAttribute('aria-selected', String(activa));
            boton.tabIndex = activa ? 0 : -1;
        }
        for (const [otroId, { panel }] of montadas) {
            panel.hidden = otroId !== pestana.id;
        }
        if (location.hash !== `#${pestana.id}`) {
            history.replaceState(null, '', `#${pestana.id}`);
        }

        // Cada pestaña se construye la primera vez que se abre;
        // después solo se le pide que refresque sus datos (como on_tab_changed).
        if (montadas.has(pestana.id)) {
            montadas.get(pestana.id).instancia?.mostrar?.();
            return;
        }

        const panel = el('section', {
            class: 'panel', role: 'tabpanel', id: `panel-${pestana.id}`,
            'aria-labelledby': `tab-${pestana.id}`,
        });
        r.paneles.append(panel);
        const registro = { panel, instancia: null };
        montadas.set(pestana.id, registro);

        if (!pestana.cargar) {
            panel.append(el('div', { class: 'pendiente' },
                el('p', { class: 'pendiente-icono', 'aria-hidden': 'true' }, pestana.icono),
                el('h2', {}, pestana.titulo),
                el('p', {}, 'Esta sección todavía no está disponible en la versión web.'),
                el('p', {}, 'Mientras tanto, usá el cliente de escritorio.')));
            return;
        }

        panel.append(el('p', { class: 'cargando' }, 'Cargando…'));
        try {
            const modulo = await pestana.cargar();
            panel.replaceChildren();
            registro.instancia = modulo.montar(panel, ctx);
            registro.instancia?.mostrar?.();
        } catch (error) {
            if (error instanceof SesionExpirada || error instanceof ClavePendiente) {
                return; // los oyentes globales ya cambiaron de vista
            }
            console.error(error);
            panel.replaceChildren(el('div', { class: 'pendiente' },
                el('p', { class: 'mensaje-error' },
                    `No se pudo cargar la sección: ${error instanceof ApiError ? error.message : 'error inesperado'}`),
                el('button', {
                    type: 'button', class: 'btn btn-primario',
                    onclick: () => {
                        montadas.delete(pestana.id);
                        panel.remove();
                        activar(pestana.id);
                    },
                }, 'Reintentar')));
        }
    }

    // Atrás/Adelante o un enlace con #pestaña cambian de pestaña.
    // El oyente se descarta solo cuando esta vista ya no está en pantalla.
    window.addEventListener('hashchange', function alCambiarHash() {
        if (!raiz.contains(r.pestanas)) {
            window.removeEventListener('hashchange', alCambiarHash);
            return;
        }
        activar(location.hash.slice(1));
    });

    mostrarVista(vista);
    activar(location.hash.slice(1));
}

iniciar();

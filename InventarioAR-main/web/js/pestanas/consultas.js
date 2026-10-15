// Pestaña Consultas (solo administradores): mensajes recibidos por el
// formulario de contacto de la portada (tabla contactos).
//
// Búsqueda, filtro por estado, lectura del mensaje completo (lo marca como
// leído), marcar como no leída, responder por email y eliminar.

import { ApiError, SesionExpirada, ClavePendiente } from '../api.js';
import { el, aviso, confirmar, campoSelect, dialogo } from '../ui.js';
import { tablaSeleccionable } from '../tabla_seleccionable.js';

const COLUMNAS = [
    { clave: 'estado_texto', titulo: 'Estado' },
    { clave: 'fecha', titulo: 'Fecha' },
    { clave: 'nombre', titulo: 'Nombre' },
    { clave: 'email', titulo: 'Email' },
    { clave: 'asunto', titulo: 'Asunto' },
    { clave: 'usuario_texto', titulo: 'Usuario' },
];

const FILTROS = [
    { valor: '', texto: 'Todas' },
    { valor: 'no_leidas', texto: 'No leídas' },
    { valor: 'leidas', texto: 'Leídas' },
];

export function montar(contenedor, { api }) {
    let completas = [];

    const buscar = el('input', { type: 'search', id: 'con-buscar', placeholder: 'Nombre, email, asunto o texto del mensaje…', autocomplete: 'off' });
    const estado = el('p', { class: 'estado-carga', role: 'status' });
    const resumen = el('p', { class: 'texto-suave' });
    const fEstado = campoSelect('Estado', FILTROS, { id: 'con-estado', alCambiar: aplicarFiltros });

    const btnLeer = el('button', { type: 'button', class: 'btn btn-primario', disabled: true, onclick: () => leer() }, '📖 Leer');
    const btnNoLeida = el('button', { type: 'button', class: 'btn btn-secundario', disabled: true, onclick: marcarNoLeida }, '✉️ Marcar como no leída');
    const btnEliminar = el('button', { type: 'button', class: 'btn btn-peligro boton-derecha', disabled: true, onclick: eliminar }, '🗑️ Eliminar');

    const tabla = tablaSeleccionable({
        columnas: COLUMNAS,
        etiqueta: 'Consultas recibidas',
        unidad: 'consultas',
        alSeleccionar: (c) => {
            btnLeer.disabled = !c;
            btnEliminar.disabled = !c;
            btnNoLeida.disabled = !c || !c.leido;
        },
        alActivar: leer,
    });

    contenedor.append(
        el('div', { class: 'cabecera-pestana' }, el('h2', {}, 'Consultas de contacto'), estado),
        resumen,
        el('div', { class: 'filtros' },
            el('div', { class: 'campo campo-ancho' }, el('label', { for: buscar.id }, 'Buscar'), buscar),
            fEstado.nodo,
            el('button', { type: 'button', class: 'btn btn-secundario', onclick: () => cargar() }, '🔁 Actualizar')),
        tabla.contador,
        tabla.nodo,
        el('div', { class: 'acciones-pie' }, btnLeer, btnNoLeida, btnEliminar));

    buscar.addEventListener('input', aplicarFiltros);

    async function cargar() {
        estado.textContent = 'Cargando…';
        try {
            completas = (await api.get('contactos.php')).map((c) => ({
                ...c,
                estado_texto: c.leido ? 'Leída' : '● Nueva',
                usuario_texto: c.usuario ?? 'Visitante',
            }));
            const nuevas = completas.filter((c) => !c.leido).length;
            resumen.textContent = `${completas.length} consultas recibidas · ${nuevas} sin leer.`;
            aplicarFiltros();
        } catch (error) {
            manejarError(error, 'No se pudieron cargar las consultas');
        } finally {
            estado.textContent = '';
        }
    }

    function aplicarFiltros() {
        const texto = buscar.value.trim().toLowerCase();
        const filtro = fEstado.select.value;
        tabla.mostrar(completas.filter((c) =>
            (!texto || [c.nombre, c.email, c.asunto, c.mensaje].some((v) => String(v ?? '').toLowerCase().includes(texto)))
            && (filtro === '' || (filtro === 'leidas') === c.leido)), completas.length);
    }

    async function accion(c, nombre) {
        await api.post('contacto_accion.php', { id_contacto: c.id_contacto, accion: nombre });
    }

    async function leer(c = tabla.seleccionada) {
        if (!c) return;
        const asunto = `Re: ${c.asunto}`;
        const responder = el('a', {
            class: 'btn btn-primario',
            href: `mailto:${encodeURIComponent(c.email)}?subject=${encodeURIComponent(asunto)}`,
        }, '↩️ Responder por email');
        dialogo(`Consulta n.º ${c.id_contacto}`, [
            el('dl', { class: 'ficha' },
                ...[['De:', `${c.nombre} <${c.email}>`], ['Fecha:', c.fecha], ['Usuario:', c.usuario_texto],
                    ['Correo:', c.mail_enviado ? 'enviado con mail()' : 'no enviado (servidor sin correo)']]
                    .map(([t, v]) => el('div', { class: 'ficha-par' }, el('dt', {}, t), el('dd', {}, v)))),
            el('h3', {}, c.asunto),
            el('p', { class: 'mensaje-consulta' }, c.mensaje),
        ], { acciones: [responder], ancho: 'medio' });
        if (!c.leido) {
            try {
                await accion(c, 'leido');
                cargar();
            } catch (error) {
                manejarError(error, 'No se pudo marcar como leída');
            }
        }
    }

    async function marcarNoLeida() {
        const c = tabla.seleccionada;
        if (!c) return;
        try {
            await accion(c, 'no_leido');
            cargar();
        } catch (error) {
            manejarError(error, 'No se pudo actualizar la consulta');
        }
    }

    async function eliminar() {
        const c = tabla.seleccionada;
        if (!c) return;
        const ok = await confirmar('Eliminar consulta',
            `¿Eliminar la consulta n.º ${c.id_contacto} de ${c.nombre} ("${c.asunto}")? No se puede deshacer.`,
            { aceptar: 'Eliminar', peligro: true });
        if (!ok) return;
        try {
            await accion(c, 'eliminar');
            aviso('Consulta eliminada.', 'exito');
            cargar();
        } catch (error) {
            manejarError(error, 'No se pudo eliminar la consulta');
        }
    }

    function manejarError(error, contexto) {
        if (error instanceof SesionExpirada || error instanceof ClavePendiente) {
            return;
        }
        console.error(error);
        aviso(`${contexto}: ${error instanceof ApiError ? error.message : 'error inesperado'}`, 'error');
    }

    return { mostrar: cargar };
}

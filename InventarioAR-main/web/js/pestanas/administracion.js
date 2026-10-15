// Pestaña Administración (equivalente a tabs/tab_administracion.py). Solo administradores.
//
// Usuarios: búsqueda y filtro por perfil, alta, edición, reseteo de clave,
// activar/desactivar y eliminación.
//
// La clave temporal (alta y reseteo) la genera el servidor al azar y se
// muestra una sola vez para pasársela al usuario (decisión de la migración:
// ya no es "1234"). La API impide que un administrador se quite acceso a sí
// mismo y que el sistema quede sin administradores activos; acá los botones
// lo anticipan para la propia cuenta.

import { ApiError, SesionExpirada, ClavePendiente } from '../api.js';
import { el, aviso, confirmar, campoSelect, dialogo, dialogoFormulario } from '../ui.js';
import { tablaSeleccionable } from '../tabla_seleccionable.js';

const PERFILES = ['Técnico', 'Administrador'];
const TODOS = '';

const COLUMNAS = [
    { clave: 'legajo', titulo: 'Legajo' },
    { clave: 'username', titulo: 'Usuario' },
    { clave: 'nombre', titulo: 'Nombre' },
    { clave: 'apellido', titulo: 'Apellido' },
    { clave: 'email', titulo: 'Email' },
    { clave: 'perfil', titulo: 'Perfil' },
    { clave: 'activo_texto', titulo: 'Activo' },
    { clave: 'cambiar_clave_texto', titulo: 'Debe cambiar clave' },
    { clave: 'bloqueado_hasta', titulo: 'Bloqueado hasta' },
    { clave: 'ultima_conexion', titulo: 'Última conexión' },
];

function habilitar(boton, habilitado, motivo = '') {
    boton.disabled = !habilitado;
    boton.title = habilitado ? '' : motivo;
}

export function montar(contenedor, { api, usuario: sesion }) {
    let completos = [];

    const buscar = el('input', { type: 'search', id: 'adm-buscar', placeholder: 'Legajo, usuario, nombre o apellido…', autocomplete: 'off' });
    const estado = el('p', { class: 'estado-carga', role: 'status' });
    const fPerfil = campoSelect('Perfil', [{ valor: TODOS, texto: 'Todos los perfiles' }, ...PERFILES], { id: 'adm-perfil', alCambiar: aplicarFiltros });

    const btnEditar = el('button', { type: 'button', class: 'btn btn-primario', disabled: true, onclick: () => editar() }, '✏️ Editar');
    const btnReset = el('button', { type: 'button', class: 'btn btn-advertencia', disabled: true, onclick: resetearClave }, '🔑 Resetear clave');
    const btnActivo = el('button', { type: 'button', class: 'btn btn-secundario', disabled: true, onclick: cambiarActivo }, '⚡ Activar / desactivar');
    const btnEliminar = el('button', { type: 'button', class: 'btn btn-peligro boton-derecha', disabled: true, onclick: eliminar }, '🗑️ Eliminar');

    const tabla = tablaSeleccionable({
        columnas: COLUMNAS,
        etiqueta: 'Usuarios del sistema',
        unidad: 'usuarios',
        formato: (valor) => (valor === null || valor === undefined || valor === '' ? '-' : String(valor)),
        alSeleccionar: actualizarBotones,
        alActivar: editar,
    });

    contenedor.append(
        el('div', { class: 'cabecera-pestana' }, el('h2', {}, 'Administración de usuarios'), estado),
        el('div', { class: 'filtros' },
            el('div', { class: 'campo campo-ancho' }, el('label', { for: buscar.id }, 'Buscar'), buscar),
            fPerfil.nodo,
            el('button', { type: 'button', class: 'btn btn-secundario', onclick: () => cargar() }, '🔁 Actualizar'),
            el('button', { type: 'button', class: 'btn btn-exito', onclick: () => formulario(null) }, '➕ Crear usuario')),
        tabla.contador,
        tabla.nodo,
        el('div', { class: 'acciones-pie' }, btnEditar, btnReset, btnActivo, btnEliminar));

    buscar.addEventListener('input', aplicarFiltros);

    // ═══════════════ Datos ═══════════════
    async function cargar() {
        estado.textContent = 'Cargando…';
        try {
            completos = (await api.get('usuarios.php')).map((u) => ({
                ...u,
                activo_texto: u.activo ? 'Sí' : 'No',
                cambiar_clave_texto: u.debe_cambiar_clave ? 'Sí' : 'No',
            }));
            aplicarFiltros();
        } catch (error) {
            manejarError(error, 'No se pudieron cargar los usuarios');
        } finally {
            estado.textContent = '';
        }
    }

    function aplicarFiltros() {
        const texto = buscar.value.trim().toLowerCase();
        const perfil = fPerfil.select.value;
        const filtrados = completos.filter((u) =>
            (!texto || [u.legajo, u.username, u.nombre, u.apellido].some((v) => String(v ?? '').toLowerCase().includes(texto)))
            && (perfil === TODOS || u.perfil === perfil));
        tabla.mostrar(filtrados, completos.length);
    }

    function esPropio(u) {
        return Number(u?.id_usuario) === Number(sesion.id);
    }

    function actualizarBotones(u) {
        habilitar(btnEditar, !!u);
        if (!u) {
            for (const b of [btnReset, btnActivo, btnEliminar]) habilitar(b, false);
            btnActivo.textContent = '⚡ Activar / desactivar';
            return;
        }
        const propio = esPropio(u);
        btnActivo.textContent = u.activo ? '⏸️ Desactivar' : '▶️ Activar';
        habilitar(btnReset, !propio, 'Para tu propia cuenta usá "Cambiar contraseña"');
        habilitar(btnActivo, !propio || !u.activo, 'No podés desactivar tu propio usuario');
        habilitar(btnEliminar, !propio, 'No podés eliminar tu propio usuario');
    }

    // ═══════════════ Alta y edición ═══════════════
    function editar(u = tabla.seleccionada) {
        if (u) formulario(u);
    }

    function formulario(u) {
        const creando = !u;
        const campo = (id, etiqueta, atributos) => {
            const input = el('input', { type: 'text', id, autocomplete: 'off', ...atributos });
            return { input, nodo: el('div', { class: 'campo' }, el('label', { for: id }, etiqueta), input) };
        };
        const legajo = campo('usr-legajo', 'Legajo', { maxlength: 50, readonly: !creando, value: u?.legajo ?? '' });
        const username = campo('usr-username', 'Usuario', { maxlength: 100, value: u?.username ?? '' });
        const nombre = campo('usr-nombre', 'Nombre', { maxlength: 100, value: u?.nombre ?? '' });
        const apellido = campo('usr-apellido', 'Apellido', { maxlength: 100, value: u?.apellido ?? '' });
        const email = campo('usr-email', 'Email (opcional)', { type: 'email', maxlength: 150, value: u?.email ?? '' });
        const perfil = campoSelect('Perfil', PERFILES, { id: 'usr-perfil' });
        perfil.select.value = u?.perfil ?? 'Técnico';
        const activo = el('input', { type: 'checkbox', id: 'usr-activo', checked: creando || !!u.activo });

        // La propia cuenta no puede quitarse el perfil ni desactivarse (la API también lo impide).
        if (!creando && esPropio(u)) {
            perfil.select.disabled = true;
            activo.disabled = true;
        }

        const { form } = dialogoFormulario(creando ? 'Crear usuario' : `Editar usuario · ${u.legajo}`, [
            el('div', { class: 'rejilla-form' }, legajo.nodo, username.nodo, nombre.nodo, apellido.nodo, email.nodo, perfil.nodo),
            el('label', { class: 'casilla' }, activo, ' Usuario activo'),
            creando ? el('p', { class: 'mensaje-info' }, 'Al guardar se genera una contraseña temporal que se muestra una sola vez. El usuario la debe cambiar en su primer ingreso.') : null,
            !creando && esPropio(u) ? el('p', { class: 'texto-suave' }, 'Es tu cuenta: el perfil y el estado los puede cambiar otro administrador.') : null,
        ], {
            textoAceptar: creando ? '💾 Crear usuario' : '💾 Guardar cambios',
            ancho: 'medio',
            alAceptar: async () => {
                const datos = {
                    legajo: legajo.input.value.trim(),
                    username: username.input.value.trim(),
                    nombre: nombre.input.value.trim(),
                    apellido: apellido.input.value.trim(),
                    email: email.input.value.trim(),
                    perfil: perfil.select.value,
                    activo: activo.checked,
                };
                const faltantes = [[legajo, 'el legajo'], [username, 'el usuario'], [nombre, 'el nombre'], [apellido, 'el apellido']]
                    .filter(([c]) => !c.input.value.trim());
                if (faltantes.length) {
                    aviso(`Falta completar ${faltantes.map(([, n]) => n).join(', ')}.`, 'error');
                    faltantes[0][0].input.focus();
                    return false;
                }
                if (/\s/.test(datos.legajo) || /\s/.test(datos.username)) {
                    aviso('El legajo y el usuario no pueden tener espacios.', 'error');
                    return false;
                }
                if (datos.email && !email.input.checkValidity()) {
                    aviso('El email no es válido.', 'error');
                    email.input.focus();
                    return false;
                }
                try {
                    const r = await api.post(creando ? 'alta_usuario.php' : 'modi_usuarios.php', datos);
                    if (creando) {
                        mostrarClaveTemporal(`Usuario ${datos.legajo} creado`, datos.legajo, r.clave_temporal);
                    } else {
                        aviso(`Usuario ${datos.legajo} actualizado.`, 'exito');
                    }
                } catch (error) {
                    manejarError(error, creando ? 'No se pudo crear el usuario' : 'No se pudo modificar el usuario');
                    return false;
                }
                cargar();
                return true;
            },
        });
        (creando ? legajo : username).input.focus();
        return form;
    }

    function mostrarClaveTemporal(titulo, legajo, clave) {
        const valor = el('code', { class: 'clave-temporal' }, clave);
        const copiar = el('button', { type: 'button', class: 'btn btn-secundario' }, '📋 Copiar');
        copiar.addEventListener('click', async () => {
            try {
                await navigator.clipboard.writeText(clave);
                aviso('Contraseña copiada al portapapeles.', 'exito');
            } catch {
                aviso('No se pudo copiar: seleccionala y copiala a mano.', 'error');
            }
        });
        dialogo(titulo, [
            el('p', {}, `Contraseña temporal del usuario ${legajo}:`),
            el('div', { class: 'fila-programacion' }, valor, copiar),
            el('p', { class: 'mensaje-error' }, 'Anotala y entregásela al usuario: no se vuelve a mostrar. Deberá cambiarla en su primer ingreso.'),
        ], { ancho: 'medio' });
    }

    // ═══════════════ Acciones ═══════════════
    async function resetearClave() {
        const u = tabla.seleccionada;
        if (!u || esPropio(u)) return;
        const ok = await confirmar('Resetear contraseña',
            `¿Resetear la contraseña de ${u.username} (legajo ${u.legajo})? Se genera una temporal, se quita el bloqueo por intentos fallidos y se cierran sus sesiones abiertas.`,
            { aceptar: 'Resetear' });
        if (!ok) return;
        try {
            const r = await api.post('resetear_clave.php', { legajo: u.legajo });
            mostrarClaveTemporal('Contraseña reseteada', u.legajo, r.clave_temporal);
            cargar();
        } catch (error) {
            manejarError(error, 'No se pudo resetear la contraseña');
        }
    }

    async function cambiarActivo() {
        const u = tabla.seleccionada;
        if (!u) return;
        const activar = !u.activo;
        const ok = await confirmar(activar ? 'Activar usuario' : 'Desactivar usuario',
            activar
                ? `¿Activar a ${u.username} (legajo ${u.legajo})? Podrá volver a ingresar.`
                : `¿Desactivar a ${u.username} (legajo ${u.legajo})? No podrá ingresar y se cierran sus sesiones abiertas.`,
            { aceptar: activar ? 'Activar' : 'Desactivar', peligro: !activar });
        if (!ok) return;
        try {
            await api.post('toggle_activo.php', { legajo: u.legajo, activo: activar });
            aviso(`Usuario ${u.legajo} ${activar ? 'activado' : 'desactivado'}.`, 'exito');
            cargar();
        } catch (error) {
            manejarError(error, 'No se pudo cambiar el estado');
        }
    }

    async function eliminar() {
        const u = tabla.seleccionada;
        if (!u || esPropio(u)) return;
        const ok = await confirmar('Eliminar usuario',
            `¿Eliminar PERMANENTEMENTE a ${u.username} (${u.nombre} ${u.apellido}, legajo ${u.legajo})? Esta acción no se puede deshacer. Si el usuario tiene registros asociados, conviene desactivarlo.`,
            { aceptar: 'Eliminar', peligro: true });
        if (!ok) return;
        try {
            await api.post('eliminar_usuario.php', { legajo: u.legajo });
            aviso(`Usuario ${u.legajo} eliminado.`, 'exito');
            cargar();
        } catch (error) {
            manejarError(error, 'No se pudo eliminar el usuario');
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

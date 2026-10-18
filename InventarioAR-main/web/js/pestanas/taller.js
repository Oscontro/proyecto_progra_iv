// Pestaña Taller (equivalente a tabs/tab_taller.py).
//
// Circuito: Inventario envía el equipo a reparación ("No ingresado") ->
// acá se registra el INGRESO (elementos recibidos, N° de SD) -> se ACTUALIZA
// el estado mientras se repara -> EGRESO (tareas, repuestos, guía), que lo
// deja "Reparado" y fuera del taller.
//
// Diferencias deliberadas con el escritorio:
//  - El egreso funciona: en el escritorio el diálogo dependía de un servicio
//    de stock que nunca se conectó y fallaba al abrirse.
//  - Los repuestos del egreso son los del catálogo vinculados al modelo del
//    equipo, con cantidad; salen del stock del taller y pasan a "en uso"
//    (migración 2026-10-14). "Otros" queda como texto y no toca stock.
//  - Los botones se habilitan según el estado: Ingreso solo para
//    "No ingresado"; Actualizar estado y Egreso solo para equipos ingresados.
//  - El texto automático para correo se genera a partir del egreso, se puede
//    editar antes de guardar y queda en el historial del equipo.

import { ApiError, SesionExpirada, ClavePendiente } from '../api.js';
import { el, aviso, campoSelect, llenarSelect, dialogo, dialogoFormulario, grupoCasillas, textoCelda } from '../ui.js';
import { tablaSeleccionable } from '../tabla_seleccionable.js';
import { verHistorialEquipo } from '../historial.js';

const NO_INGRESADO = 'No ingresado';
const TODOS = '';
const SIN_SELECCION = 'Seleccioná un equipo de la tabla';

function habilitar(boton, habilitado, motivo) {
    boton.disabled = !habilitado;
    boton.title = habilitado ? '' : motivo;
}

const COLUMNAS = [
    { clave: 'tipo', titulo: 'Tipo' },
    { clave: 'marca', titulo: 'Marca' },
    { clave: 'modelo_equipo', titulo: 'Modelo' },
    { clave: 'serie', titulo: 'N° Serie', mono: true },
    { clave: 'taller', titulo: 'Taller' },
    { clave: 'fecha_recepcion', titulo: 'Fecha recepción' },
    { clave: 'fecha_ingreso', titulo: 'Fecha ingreso' },
    { clave: 'dias', titulo: 'Días' },
    { clave: 'estado_taller', titulo: 'Estado', pildora: true },
    { clave: 'observaciones', titulo: 'Observaciones' },
];

// Columnas de taller_ingresos que acepta ingreso_taller.php.
const ELEMENTOS_INGRESO = [
    { valor: 'componente_equipo', texto: 'Equipo' },
    { valor: 'componente_antena', texto: 'Antena' },
    { valor: 'componente_cargador', texto: 'Cargador' },
    { valor: 'componente_bateria', texto: 'Batería' },
    { valor: 'componente_fuente', texto: 'Fuente' },
    { valor: 'componente_cables', texto: 'Cables' },
    { valor: 'componente_otros', texto: 'Otros' },
];

// Columnas de taller_egresos que acepta egreso_taller.php.
const TAREAS_EGRESO = [
    { valor: 'tarea_soldadura_smd', texto: 'Soldadura SMD' },
    { valor: 'tarea_verificacion_rf', texto: 'Verificación RF' },
    { valor: 'tarea_reprogramacion', texto: 'Reprogramación' },
    { valor: 'tarea_otros', texto: 'Otros' },
];

export function montar(contenedor, { api }) {
    let completos = [];
    let estadosTaller = [];   // [{id_estado, estado}] para "Actualizar estado"

    const buscar = el('input', { type: 'search', id: 'tal-buscar', placeholder: 'N° de serie…', autocomplete: 'off' });
    const estado = el('p', { class: 'estado-carga', role: 'status' });
    const fTaller = campoSelect('Taller', [], { id: 'tal-taller', alCambiar: aplicarFiltros });
    const fEstado = campoSelect('Estado', [], { id: 'tal-estado', alCambiar: aplicarFiltros });

    const btnIngreso = el('button', { type: 'button', class: 'btn btn-primario', disabled: true, onclick: ingresar }, '🔧 Ingreso a taller');
    const btnHistorial = el('button', { type: 'button', class: 'btn btn-secundario', disabled: true, onclick: () => verHistorial() }, '📜 Ver historial');
    const btnEstado = el('button', { type: 'button', class: 'btn btn-secundario', disabled: true, onclick: actualizarEstado }, 'Actualizar estado');
    const btnEgreso = el('button', { type: 'button', class: 'btn btn-exito', disabled: true, onclick: egresar }, '✅ Egreso del taller');

    const tabla = tablaSeleccionable({
        columnas: COLUMNAS,
        etiqueta: 'Equipos en taller',
        unidad: 'equipos',
        alSeleccionar: (fila) => {
            const ingresado = fila && fila.estado_taller !== NO_INGRESADO;
            // Cada botón deshabilitado explica por qué (tooltip).
            habilitar(btnIngreso, fila && fila.estado_taller === NO_INGRESADO,
                fila ? `Solo para equipos en estado "${NO_INGRESADO}" (este está "${fila.estado_taller}")` : SIN_SELECCION);
            habilitar(btnHistorial, !!fila, SIN_SELECCION);
            habilitar(btnEstado, ingresado, fila ? 'Primero hay que registrar el ingreso a taller' : SIN_SELECCION);
            habilitar(btnEgreso, ingresado && !!fila.id_ingreso, fila ? 'Primero hay que registrar el ingreso a taller' : SIN_SELECCION);
        },
        alActivar: verHistorial,
    });

    contenedor.append(
        el('div', { class: 'cabecera-pestana' }, el('h2', {}, 'Taller'), estado),
        el('div', { class: 'filtros' },
            el('div', { class: 'campo campo-ancho' }, el('label', { for: buscar.id }, 'Buscar'), buscar),
            el('button', { type: 'button', class: 'btn btn-secundario', onclick: limpiarFiltros }, 'Limpiar filtros'),
            el('button', { type: 'button', class: 'btn btn-secundario', onclick: () => cargar() }, '🔁 Actualizar')),
        el('div', { class: 'filtros' }, fTaller.nodo, fEstado.nodo),
        tabla.contador,
        tabla.nodo,
        el('div', { class: 'acciones-pie' }, btnIngreso, btnHistorial, btnEstado, btnEgreso,
            el('p', { class: 'texto-suave nota' }, 'Los equipos llegan acá desde Inventario → "Enviar a reparación".')));

    buscar.addEventListener('input', aplicarFiltros);

    // ═══════════════ Datos y filtros ═══════════════
    async function cargar() {
        estado.textContent = 'Cargando…';
        try {
            const [equipos, talleres, estados] = await Promise.all([
                api.get('vista_taller.php'),
                api.get('talleres.php'),
                api.get('estados_taller.php'),
            ]);
            completos = equipos;
            estadosTaller = estados;
            llenarSelect(fTaller.select, [{ valor: TODOS, texto: 'Todos' }, ...talleres.map((t) => t.taller)]);
            // Además de los del catálogo, los estados que tengan los equipos (p. ej. "No ingresado").
            const nombres = [...new Set([...estados.map((e) => e.estado), ...equipos.map((e) => e.estado_taller).filter(Boolean)])];
            llenarSelect(fEstado.select, [{ valor: TODOS, texto: 'Todos' }, ...nombres]);
            aplicarFiltros();
        } catch (error) {
            manejarError(error, 'No se pudieron cargar los equipos en taller');
        } finally {
            estado.textContent = '';
        }
    }

    function limpiarFiltros() {
        buscar.value = '';
        fTaller.select.value = TODOS;
        fEstado.select.value = TODOS;
        aplicarFiltros();
    }

    function aplicarFiltros() {
        const texto = buscar.value.trim().toUpperCase();
        const taller = fTaller.select.value;
        const est = fEstado.select.value;
        tabla.mostrar(completos.filter((e) =>
            (!texto || String(e.serie ?? '').toUpperCase().includes(texto))
            && (!taller || e.taller === taller)
            && (!est || e.estado_taller === est)), completos.length);
    }

    // ═══════════════ Acciones ═══════════════
    async function verHistorial(equipo = tabla.seleccionada) {
        if (!equipo) return;
        try {
            await verHistorialEquipo(api, { id_equipo: equipo.id_equipo, marca: equipo.marca,
                                            modelo_equipo: equipo.modelo_equipo, numero_serie: equipo.serie });
        } catch (error) {
            manejarError(error, 'No se pudo cargar el historial');
        }
    }

    function ingresar() {
        const equipo = tabla.seleccionada;
        if (!equipo || equipo.estado_taller !== NO_INGRESADO) return;

        const sd = el('input', { type: 'text', id: 'tal-ing-sd', name: 'nro_sd', placeholder: 'Opcional', autocomplete: 'off' });
        const elementos = grupoCasillas('Elementos recibidos', 'elementos', ELEMENTOS_INGRESO);
        const detalle = el('textarea', { id: 'tal-ing-detalle', name: 'detalle_otros', disabled: true });
        const otros = elementos.casillas.find((c) => c.value === 'componente_otros');
        otros.addEventListener('change', () => {
            detalle.disabled = !otros.checked;
            if (!otros.checked) detalle.value = '';
        });

        dialogoFormulario(`Ingreso a taller · ${equipo.serie}`, [
            fichaEquipo(equipo),
            el('label', { for: sd.id }, 'N° de SD'), sd,
            elementos.nodo,
            el('label', { for: detalle.id }, 'Detalle de otros'), detalle,
        ], {
            textoAceptar: 'Ingresar equipo',
            ancho: 'medio',
            alAceptar: async () => {
                const marcados = elementos.marcadas();
                if (!marcados.length) {
                    aviso('Debe seleccionar al menos un elemento.', 'error');
                    return false;
                }
                try {
                    await api.post('ingreso_taller.php', {
                        id_equipo: equipo.id_equipo,
                        id_estado: equipo.id_estado,
                        id_taller: equipo.id_taller,
                        id_recepcion: equipo.id_recepcion,
                        estado: equipo.estado_taller,
                        nro_sd: sd.value.trim(),
                        elementos: marcados,
                        detalle_otros: detalle.value.trim(),
                    });
                } catch (error) {
                    manejarError(error, 'No se pudo realizar el ingreso al taller');
                    return false;
                }
                aviso(`El equipo ${equipo.serie} fue ingresado correctamente.`, 'exito');
                cargar();
                return true;
            },
        });
        sd.focus();
    }

    function actualizarEstado() {
        const equipo = tabla.seleccionada;
        if (!equipo || equipo.estado_taller === NO_INGRESADO) return;

        const { nodo, select } = campoSelect('Nuevo estado', estadosTaller.map((e) => e.estado), { id: 'tal-nuevo-estado' });
        if (estadosTaller.some((e) => e.estado === equipo.estado_taller)) {
            select.value = equipo.estado_taller;
        }

        dialogoFormulario(`Estado de ${equipo.serie}`, [
            fichaEquipo(equipo),
            el('p', {}, 'Estado actual: ', el('strong', {}, textoCelda(equipo.estado_taller))),
            nodo,
        ], {
            textoAceptar: 'Actualizar',
            alAceptar: async () => {
                try {
                    await api.post('actualizar_estado.php', {
                        id: equipo.id_estado, id_equipo: equipo.id_equipo, estado: select.value,
                    });
                } catch (error) {
                    manejarError(error, 'No se pudo actualizar el estado');
                    return false;
                }
                aviso(`El estado del equipo ${equipo.serie} se actualizó a "${select.value}".`, 'exito');
                cargar();
                return true;
            },
        });
        select.focus();
    }

    async function egresar() {
        const equipo = tabla.seleccionada;
        if (!equipo || equipo.estado_taller === NO_INGRESADO || !equipo.id_ingreso) return;

        // Repuestos del catálogo vinculados al modelo, con el stock de este taller.
        let catalogo;
        try {
            catalogo = await api.get('repuestos_equipo.php', { id_ingreso: equipo.id_ingreso });
        } catch (error) {
            manejarError(error, 'No se pudieron cargar los repuestos del equipo');
            return;
        }

        const guia = el('input', { type: 'text', id: 'tal-egr-guia', placeholder: 'Opcional', autocomplete: 'off' });
        const tareas = grupoCasillas('Tareas realizadas', 'tareas', TAREAS_EGRESO);
        const detalleTareas = el('input', { type: 'text', id: 'tal-egr-det-tareas', placeholder: 'Detalle de otras tareas…', disabled: true });
        const repuestos = selectorRepuestos(catalogo);
        const otros = el('input', { type: 'checkbox', id: 'tal-egr-otros' });
        const detalleOtros = el('input', { type: 'text', id: 'tal-egr-det-rep', placeholder: 'Detalle de otros repuestos (no descuenta stock)…', disabled: true });
        const texto = el('textarea', { id: 'tal-egr-texto', rows: 7 });
        let textoEditado = false;

        habilitarDetalle(tareas, 'tarea_otros', detalleTareas);
        otros.addEventListener('change', () => {
            detalleOtros.disabled = !otros.checked;
            if (!otros.checked) detalleOtros.value = '';
        });

        // El texto para correo se arma solo, hasta que el usuario lo edite a mano.
        const regenerar = () => {
            if (!textoEditado) {
                texto.value = textoCorreo(equipo, guia.value, tareas, detalleTareas.value,
                    repuestos.usados(), otros.checked ? detalleOtros.value : null);
            }
        };
        texto.addEventListener('input', () => { textoEditado = true; });
        for (const nodo of [guia, detalleTareas, detalleOtros, otros, ...tareas.casillas, ...repuestos.campos]) {
            nodo.addEventListener('input', regenerar);
            nodo.addEventListener('change', regenerar);
        }
        regenerar();

        dialogoFormulario(`Egreso de taller · ${equipo.serie}`, [
            fichaEquipo(equipo),
            el('label', { for: guia.id }, 'Número de guía'), guia,
            tareas.nodo, detalleTareas,
            repuestos.nodo,
            el('label', { class: 'casilla' }, otros, ' Otros repuestos (fuera del catálogo)'), detalleOtros,
            el('label', { for: texto.id }, 'Texto para correo (queda en el historial del equipo)'), texto,
        ], {
            textoAceptar: 'Guardar egreso',
            ancho: 'medio',
            alAceptar: async () => {
                const marcadasTareas = tareas.marcadas();
                if (!marcadasTareas.length) {
                    aviso('Debe seleccionar al menos una tarea.', 'error');
                    return false;
                }
                if (marcadasTareas.includes('tarea_otros') && !detalleTareas.value.trim()) {
                    aviso("Marcó 'Otros' en tareas pero no escribió el detalle.", 'error');
                    detalleTareas.focus();
                    return false;
                }
                const problema = repuestos.validar();
                if (problema) {
                    aviso(problema, 'error');
                    return false;
                }
                if (otros.checked && !detalleOtros.value.trim()) {
                    aviso("Marcó 'Otros' en repuestos pero no escribió el detalle.", 'error');
                    detalleOtros.focus();
                    return false;
                }
                try {
                    await api.post('egreso_taller.php', {
                        id_equipo: equipo.id_equipo,
                        id_ingreso: equipo.id_ingreso,
                        id_estado: equipo.id_estado,
                        numero_guia: guia.value.trim(),
                        elementos_tareas: marcadasTareas,
                        detalle_tareas: detalleTareas.value.trim(),
                        repuestos_usados: repuestos.usados().map((u) => ({ id_repuesto: u.id_repuesto, cantidad: u.cantidad })),
                        elementos_repuestos: otros.checked ? ['repuesto_otros'] : [],
                        detalle_otros: detalleOtros.value.trim(),
                        texto_email_informe: texto.value.trim(),
                    });
                } catch (error) {
                    manejarError(error, 'No se pudo registrar el egreso');
                    return false;
                }
                aviso(`El equipo ${equipo.serie} fue egresado del taller.`, 'exito');
                mostrarTextoCorreo(texto.value.trim());
                cargar();
                return true;
            },
        });
        guia.focus();
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

// ═══════════════ Auxiliares ═══════════════

function fichaEquipo(equipo) {
    // Cada par etiqueta/valor va junto en un <div> (válido dentro de <dl>) para que corte de línea entre pares.
    const dato = (t, v) => el('div', { class: 'ficha-par' }, el('dt', {}, t), el('dd', {}, textoCelda(v) || '-'));
    return el('dl', { class: 'ficha' },
        dato('Tipo:', equipo.tipo), dato('Marca:', equipo.marca), dato('Modelo:', equipo.modelo_equipo),
        dato('N° de serie:', equipo.serie), dato('Taller:', equipo.taller), dato('Estado:', equipo.estado_taller));
}

function habilitarDetalle(grupo, valorOtros, campo) {
    const casilla = grupo.casillas.find((c) => c.value === valorOtros);
    casilla.addEventListener('change', () => {
        campo.disabled = !casilla.checked;
        if (!casilla.checked) campo.value = '';
    });
}

// Repuestos del catálogo con un campo de cantidad cada uno (0 = no se usó).
function selectorRepuestos({ taller, repuestos }) {
    const filas = repuestos.map((r) => ({
        r,
        campo: el('input', {
            type: 'number', min: '0', max: String(r.stock_taller), step: '1', value: '0',
            id: `tal-egr-rep-${r.id_repuesto}`, disabled: r.stock_taller === 0,
        }),
    }));
    const nodo = el('fieldset', { class: 'casillas repuestos-egreso' },
        el('legend', {}, `Repuestos utilizados (stock de ${taller})`),
        filas.length
            ? filas.map(({ r, campo }) => el('div', { class: 'repuesto-egreso' },
                el('label', { for: campo.id }, r.nombre,
                    el('small', {}, ` ${r.numero_parte || ''} · disponible: ${r.stock_taller}`)),
                campo))
            : el('p', { class: 'texto-suave' }, 'Este modelo no tiene repuestos vinculados en el catálogo.'));

    return {
        nodo,
        campos: filas.map((f) => f.campo),
        usados: () => filas
            .map(({ r, campo }) => ({ ...r, cantidad: Number(campo.value) }))
            .filter((u) => u.cantidad > 0),
        validar() {
            for (const { r, campo } of filas) {
                const n = Number(campo.value);
                if (!Number.isInteger(n) || n < 0) return `La cantidad de "${r.nombre}" tiene que ser un entero mayor o igual a 0.`;
                if (n > r.stock_taller) return `No alcanza el stock de "${r.nombre}" en ${taller} (disponible: ${r.stock_taller}).`;
            }
            return null;
        },
    };
}

function textoCorreo(equipo, guia, tareas, detalleTareas, usados, detalleOtros) {
    const listaTareas = tareas.marcadas().map((v) => {
        const texto = TAREAS_EGRESO.find((o) => o.valor === v).texto;
        return v === 'tarea_otros' && detalleTareas.trim() ? `${texto}: ${detalleTareas.trim()}` : texto;
    });
    const listaRepuestos = usados.map((u) => `${u.nombre} x${u.cantidad}`);
    if (detalleOtros !== null) listaRepuestos.push(`Otros: ${detalleOtros.trim()}`);
    return [
        `Equipo: ${textoCelda(equipo.tipo)} ${textoCelda(equipo.marca)} ${textoCelda(equipo.modelo_equipo)} - N° de serie ${textoCelda(equipo.serie)}`,
        `Taller: ${textoCelda(equipo.taller)}`,
        `Tareas realizadas: ${listaTareas.length ? listaTareas.join(', ') : '-'}`,
        `Repuestos utilizados: ${listaRepuestos.length ? listaRepuestos.join(', ') : 'Ninguno'}`,
        guia.trim() ? `N° de guía: ${guia.trim()}` : null,
        'Estado: Reparado',
    ].filter(Boolean).join('\n');
}

function mostrarTextoCorreo(texto) {
    if (!texto) return;
    const area = el('textarea', { class: 'lista-series', readonly: true, rows: 8, 'aria-label': 'Texto para correo' }, texto);
    dialogo('Texto automático para correo', area, {
        acciones: [el('button', {
            type: 'button', class: 'btn btn-primario',
            onclick: async () => {
                try {
                    await navigator.clipboard.writeText(texto);
                    aviso('El texto se copió al portapapeles.', 'exito');
                } catch {
                    area.select();
                    aviso('No se pudo copiar automáticamente: el texto quedó seleccionado (Ctrl+C).', 'error');
                }
            },
        }, 'Copiar texto')],
    });
}

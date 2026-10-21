// Pestaña Repuestos (equivalente a tabs/tab_repuestos.py).
//
// Estados de cada repuesto (conteos, sin identificar unidades):
//   EN STOCK (por taller) · EN USO (general) · FUERA DE SERVICIO (por taller)
// Ciclo: Ingreso (+stock) -> Usar en equipo (stock -> en uso) ->
//        Fuera de servicio (en uso -> F/S) -> Reparar (F/S -> stock) | Descartar (- F/S)
//
// Diferencias deliberadas con el escritorio:
//  - Tras cada operación se recargan los datos del servidor (el escritorio
//    modificaba su copia local; un repuesto nuevo no aparecía hasta reiniciar).
//  - "Compatible con" se arma con las marcas y modelos reales de la base
//    (el escritorio usaba tablas fijas en el código, desactualizadas).
//  - Los talleres salen de la base, no de una lista fija.
//  - No se migran las herramientas provisorias de carga inicial (exportar a
//    SQL, "borrar todos", borrar modelos de la lista): solo actuaban en memoria.
//  - Modificar cambia solo los datos de catálogo; el stock se cambia con los
//    movimientos o con el ajuste forzado (así no se pisan movimientos ajenos).

import { ApiError, SesionExpirada, ClavePendiente } from '../api.js';
import { el, aviso, confirmar, campoSelect, llenarSelect, dialogoFormulario, textoCelda } from '../ui.js';
import { tablaSeleccionable } from '../tabla_seleccionable.js';

const UMBRAL_BAJO = 10;
const TODOS = '';
const formatoFecha = new Intl.DateTimeFormat('es-AR', { day: '2-digit', month: '2-digit', year: 'numeric' });

export function montar(contenedor, { api, usuario }) {
    let repuestos = [];   // filas enriquecidas para la tabla
    let modelos = [];     // [{id_modelo, marca, modelo_equipo}]
    let talleres = [];    // ['Aeroparque', 'Ezeiza']

    const buscar = el('input', { type: 'search', id: 'rep-buscar', placeholder: 'N° de parte, nombre o modelo…', autocomplete: 'off' });
    const estado = el('p', { class: 'estado-carga', role: 'status' });
    const resumen = el('p', { class: 'resumen-repuestos' });
    const fTaller = campoSelect('Taller', [], { id: 'rep-taller', alCambiar: aplicarFiltros });
    const fModelo = campoSelect('Modelo', [], { id: 'rep-modelo', alCambiar: aplicarFiltros });
    const fEstado = campoSelect('Estado', [
        { valor: TODOS, texto: 'Todos' }, 'Stock bajo', 'Sin stock', 'Con stock', 'En uso', 'Con fuera de servicio',
    ], { id: 'rep-estado', alCambiar: aplicarFiltros });

    const detalle = el('section', { class: 'detalle-repuesto', 'aria-live': 'polite' });
    let tabla = null;   // se crea al conocer los talleres (columnas dinámicas)
    const zonaTabla = el('div', { class: 'zona-tabla' });

    contenedor.append(
        el('div', { class: 'cabecera-pestana' }, el('h2', {}, 'Stock de repuestos'), estado,
            el('button', { type: 'button', class: 'btn btn-primario boton-derecha', onclick: () => formularioRepuesto(null) }, '➕ Nuevo repuesto')),
        resumen,
        el('div', { class: 'filtros' },
            el('div', { class: 'campo campo-ancho' }, el('label', { for: buscar.id }, 'Buscar'), buscar),
            el('button', { type: 'button', class: 'btn btn-secundario', onclick: limpiarFiltros }, 'Limpiar filtros'),
            el('button', { type: 'button', class: 'btn btn-secundario', onclick: () => cargar() }, '🔁 Actualizar')),
        el('div', { class: 'filtros' }, fTaller.nodo, fModelo.nodo, fEstado.nodo),
        zonaTabla,
        detalle);
    buscar.addEventListener('input', aplicarFiltros);
    mostrarDetalle(null);

    // ═══════════════ Datos ═══════════════
    async function cargar(idSeleccionar = tabla?.seleccionada?.id_repuesto) {
        estado.textContent = 'Cargando…';
        try {
            const [lista, listaModelos, listaTalleres] = await Promise.all([
                api.get('repuestos.php'), api.get('modelo_con_marca.php'), api.get('talleres.php'),
            ]);
            modelos = listaModelos;
            const nombresTalleres = listaTalleres.map((t) => t.taller);
            if (!tabla || nombresTalleres.join() !== talleres.join()) {
                talleres = nombresTalleres;
                crearTabla();
            }
            repuestos = lista.map(enriquecer);
            llenarSelect(fTaller.select, [{ valor: TODOS, texto: 'Ambos' }, ...talleres]);
            llenarSelect(fModelo.select, [{ valor: TODOS, texto: 'Todos' },
                ...modelos.map((m) => ({ valor: String(m.id_modelo), texto: `${m.marca} ${m.modelo_equipo}` }))]);
            aplicarFiltros();
            if (idSeleccionar) tabla.seleccionarDonde((r) => r.id_repuesto === idSeleccionar);
            actualizarResumen();
        } catch (error) {
            manejarError(error, 'No se pudieron cargar los repuestos');
        } finally {
            estado.textContent = '';
        }
    }

    function crearTabla() {
        const columnas = [
            { clave: '_estado', titulo: 'Estado', pildora: true },
            { clave: 'numero_parte', titulo: 'N° de parte' },
            { clave: 'nombre', titulo: 'Nombre' },
            { clave: '_compat', titulo: 'Compatible con' },
            ...talleres.flatMap((t, i) => [
                { clave: `_st${i}`, titulo: `🟢 ${t}` },
                { clave: `_fs${i}`, titulo: `🔴 ${t}` },
            ]),
            { clave: 'en_uso', titulo: '🔵 En uso' },
            { clave: '_total', titulo: 'Σ Total' },
            { clave: '_ultimo', titulo: 'Último ingreso' },
        ];
        tabla = tablaSeleccionable({
            columnas,
            etiqueta: 'Repuestos registrados',
            unidad: 'repuestos',
            formato: (valor) => (valor === null || valor === undefined || valor === '' ? '-' : String(valor)),
            alSeleccionar: mostrarDetalle,
        });
        zonaTabla.replaceChildren(tabla.contador, tabla.nodo);
    }

    // Campos calculados, como columnas para poder ordenar y filtrar.
    function enriquecer(r) {
        const fila = { ...r };
        let stock = 0;
        let fs = 0;
        let ultimo = null;
        talleres.forEach((t, i) => {
            const datos = r.talleres?.[t] || {};
            fila[`_st${i}`] = Number(datos.stock_actual || 0);
            fila[`_fs${i}`] = Number(datos.fuera_servicio || 0);
            stock += fila[`_st${i}`];
            fs += fila[`_fs${i}`];
            if (datos.fecha_ingreso && (!ultimo || datos.fecha_ingreso > ultimo)) ultimo = datos.fecha_ingreso;
        });
        fila.en_uso = Number(r.en_uso || 0);
        fila._stock = stock;
        fila._fs = fs;
        fila._total = stock + fila.en_uso + fs;
        fila._ultimo = ultimo ? formatoFecha.format(new Date(ultimo.replace(' ', 'T'))) : null;
        fila._ultimoIso = ultimo;
        fila._compat = textoCompatible(r.modelos);
        // Indicador con ícono + texto (nunca solo color).
        fila._estado = stock === 0 ? 'Sin stock' : stock <= UMBRAL_BAJO ? 'Stock bajo' : 'OK';
        return fila;
    }

    // "MOTOROLA DEM300, DEP450 · ICOM IC-A210": marca una vez + sus modelos.
    function textoCompatible(ids = []) {
        const grupos = new Map();
        for (const id of ids) {
            const m = modelos.find((x) => x.id_modelo === id);
            const marca = m ? m.marca : '';
            if (!grupos.has(marca)) grupos.set(marca, []);
            grupos.get(marca).push(m ? m.modelo_equipo : `#${id}`);
        }
        return [...grupos].map(([marca, lista]) => `${marca} ${lista.join(', ')}`.trim()).join(' · ');
    }

    // ═══════════════ Filtros y resumen ═══════════════
    function limpiarFiltros() {
        buscar.value = '';
        for (const f of [fTaller, fModelo, fEstado]) f.select.value = TODOS;
        aplicarFiltros();
    }

    function aplicarFiltros() {
        if (!tabla) return;
        const texto = buscar.value.trim().toUpperCase();
        const iTaller = talleres.indexOf(fTaller.select.value);   // -1 = ambos
        const stockSegun = (r) => (iTaller >= 0 ? r[`_st${iTaller}`] : r._stock);
        const fsSegun = (r) => (iTaller >= 0 ? r[`_fs${iTaller}`] : r._fs);
        const idModelo = Number(fModelo.select.value) || null;
        const condicion = {
            'Stock bajo': (r) => stockSegun(r) > 0 && stockSegun(r) <= UMBRAL_BAJO,
            'Sin stock': (r) => stockSegun(r) === 0,
            'Con stock': (r) => stockSegun(r) > 0,
            'En uso': (r) => r.en_uso > 0,
            'Con fuera de servicio': (r) => fsSegun(r) > 0,
        }[fEstado.select.value] || (() => true);

        tabla.mostrar(repuestos.filter((r) =>
            (!texto || [r.numero_parte, r.nombre, r._compat].some((v) => String(v ?? '').toUpperCase().includes(texto)))
            && (!idModelo || (r.modelos || []).includes(idModelo))
            && condicion(r)), repuestos.length);
    }

    function actualizarResumen() {
        const suma = (f) => repuestos.reduce((s, r) => s + f(r), 0);
        const enStock = suma((r) => r._stock);
        const enUso = suma((r) => r.en_uso);
        const fs = suma((r) => r._fs);
        const porTaller = talleres.map((t, i) => `${t}: ${suma((r) => r[`_st${i}`])} en stock / ${suma((r) => r[`_fs${i}`])} F/S`);
        resumen.textContent = `${repuestos.length} repuestos · ${enStock} en stock · ${enUso} en uso · ${fs} fuera de servicio · `
            + `Σ ${enStock + enUso + fs} · ${repuestos.filter((r) => r._stock === 0).length} sin stock · `
            + `${repuestos.filter((r) => r._stock > 0 && r._stock <= UMBRAL_BAJO).length} con stock bajo — ${porTaller.join(' · ')}`;
    }

    // ═══════════════ Detalle y acciones ═══════════════
    function mostrarDetalle(rep) {
        if (!rep) {
            detalle.replaceChildren(el('p', { class: 'texto-suave' }, 'Seleccioná un repuesto de la tabla para ver su estado y operar.'));
            return;
        }
        const boton = (texto, clase, accion) => el('button', { type: 'button', class: `btn ${clase}`, onclick: accion }, texto);
        detalle.replaceChildren(
            el('h3', {}, `${rep.nombre} · ${rep.numero_parte || 'sin N° de parte'}`),
            el('p', { class: 'texto-suave' }, `Compatible con: ${rep._compat || '-'}`),
            el('div', { class: 'tabla-contenedor' }, el('table', { class: 'tabla' },
                el('thead', {}, el('tr', {}, ['Taller', '🟢 En stock', '🔴 Fuera de servicio', '📅 Último ingreso'].map((t) => el('th', { scope: 'col' }, t)))),
                el('tbody', {}, talleres.map((t, i) => el('tr', {},
                    el('th', { scope: 'row' }, t),
                    el('td', { class: 'num' }, String(rep[`_st${i}`])),
                    el('td', { class: 'num' }, String(rep[`_fs${i}`])),
                    el('td', {}, textoCelda(rep.talleres?.[t]?.fecha_ingreso) || '-')))))),
            el('p', { class: 'dato-destacado' }, `🔵 En uso: ${rep.en_uso} · Σ Total: ${rep._total}`),
            el('div', { class: 'acciones-pie' },
                boton('📥 Registrar ingreso', 'btn-primario', () => movimiento(rep, 'ingreso')),
                boton('🔧 Usar en equipo', 'btn-secundario', () => movimiento(rep, 'usar')),
                boton('🔴 Fuera de servicio', 'btn-secundario', () => movimiento(rep, 'fuera')),
                boton('♻️ Reparar', 'btn-secundario', () => movimiento(rep, 'reparar')),
                boton('🗑️ Descartar F/S', 'btn-secundario', () => movimiento(rep, 'descartar')),
                boton('✏️ Ajustar stock', 'btn-secundario', () => ajustar(rep)),
                boton('📝 Modificar', 'btn-secundario', () => formularioRepuesto(rep)),
                usuario.es_admin ? boton('❌ Dar de baja', 'btn-peligro', () => darDeBaja(rep)) : null));
    }

    // Cada movimiento: endpoint, texto y cuánto hay disponible para mover.
    const MOVIMIENTOS = {
        ingreso: { titulo: 'Registrar ingreso', endpoint: 'ingreso_repuesto.php', etiqueta: 'Unidades que ingresan a stock',
                   disponible: () => null, exito: (n, t) => `Ingresaron ${n} unidad(es) a ${t}.` },
        usar: { titulo: 'Usar en equipo', endpoint: 'usar_repuesto.php', etiqueta: 'Unidades que pasan a EN USO (salen del stock)',
                disponible: (r, i) => ({ valor: r[`_st${i}`], texto: 'en stock en el taller' }), exito: (n) => `${n} unidad(es) pasaron a en uso.` },
        fuera: { titulo: 'Fuera de servicio', endpoint: 'fuera_servicio.php', etiqueta: 'Unidades en uso que salen de servicio (quedan a reparar en el taller)',
                 disponible: (r) => ({ valor: r.en_uso, texto: 'en uso (total)' }),
                 exito: (n, t) => `${n} unidad(es) quedaron fuera de servicio en ${t}. Recordá ponerles la etiqueta física.` },
        reparar: { titulo: 'Reparar', endpoint: 'reparar_repuesto.php', etiqueta: 'Unidades reparadas que vuelven al stock',
                   disponible: (r, i) => ({ valor: r[`_fs${i}`], texto: 'fuera de servicio en el taller' }), exito: (n, t) => `${n} unidad(es) volvieron al stock en ${t}.` },
        descartar: { titulo: 'Descartar fuera de servicio', endpoint: 'descartar_repuesto.php', etiqueta: 'Unidades irreparables a descartar',
                     disponible: (r, i) => ({ valor: r[`_fs${i}`], texto: 'fuera de servicio en el taller' }), exito: (n, t) => `Se descartaron ${n} unidad(es) en ${t}.`,
                     confirmar: true },
    };

    function movimiento(rep, tipo) {
        const mov = MOVIMIENTOS[tipo];
        const { nodo: campoTaller, select: taller } = campoSelect('Taller', talleres, { id: 'rep-mov-taller' });
        const cantidad = el('input', { type: 'number', id: 'rep-mov-cantidad', min: '1', step: '1', value: '1', required: true });
        const info = el('p', { class: 'texto-suave' });
        const actualizarMaximo = () => {
            const d = mov.disponible(rep, talleres.indexOf(taller.value));
            if (d) {
                cantidad.max = String(Math.max(1, d.valor));
                info.textContent = `Disponible: ${d.valor} ${d.texto}.`;
            } else {
                cantidad.removeAttribute('max');
                info.textContent = '';
            }
        };
        taller.addEventListener('change', actualizarMaximo);
        actualizarMaximo();

        dialogoFormulario(`${mov.titulo} · ${rep.nombre}`, [
            campoTaller, el('label', { for: cantidad.id }, mov.etiqueta), cantidad, info,
        ], {
            textoAceptar: mov.titulo,
            alAceptar: async () => {
                const n = Number(cantidad.value);
                const d = mov.disponible(rep, talleres.indexOf(taller.value));
                if (!Number.isInteger(n) || n < 1) {
                    aviso('La cantidad tiene que ser un número entero mayor a 0.', 'error');
                    return false;
                }
                if (d && n > d.valor) {
                    aviso(`No alcanza: hay ${d.valor} ${d.texto}.`, 'error');
                    return false;
                }
                if (mov.confirmar && !(await confirmar('Confirmar descarte',
                    `¿Descartar ${n} unidad(es) de "${rep.nombre}" en ${taller.value}? Esta acción no se puede deshacer.`,
                    { aceptar: 'Descartar', peligro: true }))) {
                    return false;
                }
                try {
                    await api.post(mov.endpoint, { id_repuesto: rep.id_repuesto, taller: taller.value, cantidad: n });
                } catch (error) {
                    manejarError(error, `No se pudo ${mov.titulo.toLowerCase()}`);
                    return false;
                }
                aviso(mov.exito(n, taller.value), 'exito');
                cargar(rep.id_repuesto);
                return true;
            },
        });
        cantidad.select();
    }

    function ajustar(rep) {
        const campos = talleres.map((t, i) => ({
            taller: t,
            stock: el('input', { type: 'number', min: '0', step: '1', value: String(rep[`_st${i}`]), id: `rep-aj-st${i}`, 'aria-label': `En stock en ${t}` }),
            fs: el('input', { type: 'number', min: '0', step: '1', value: String(rep[`_fs${i}`]), id: `rep-aj-fs${i}`, 'aria-label': `Fuera de servicio en ${t}` }),
        }));
        const enUso = el('input', { type: 'number', min: '0', step: '1', value: String(rep.en_uso), id: 'rep-aj-uso' });

        dialogoFormulario(`Ajustar stock (forzar) · ${rep.nombre}`, [
            el('p', { class: 'mensaje-info' }, 'Escribí los valores exactos. Se guardan tal cual, sin pasar por los movimientos.'),
            el('table', { class: 'tabla tabla-ajuste' },
                el('thead', {}, el('tr', {}, ['Taller', '🟢 En stock', '🔴 Fuera de servicio'].map((t) => el('th', { scope: 'col' }, t)))),
                el('tbody', {}, campos.map((c) => el('tr', {}, el('th', { scope: 'row' }, c.taller), el('td', {}, c.stock), el('td', {}, c.fs))))),
            el('label', { for: enUso.id }, '🔵 En uso (general)'), enUso,
        ], {
            textoAceptar: 'Guardar ajuste',
            alAceptar: async () => {
                const valores = [...campos.flatMap((c) => [c.stock, c.fs]), enUso].map((x) => Number(x.value));
                if (valores.some((v) => !Number.isInteger(v) || v < 0)) {
                    aviso('Todos los valores tienen que ser enteros mayores o iguales a 0.', 'error');
                    return false;
                }
                try {
                    await api.post('ajustar_stock.php', {
                        id_repuesto: rep.id_repuesto,
                        en_uso: Number(enUso.value),
                        talleres: Object.fromEntries(campos.map((c) => [c.taller, { stock: Number(c.stock.value), fuera_servicio: Number(c.fs.value) }])),
                    });
                } catch (error) {
                    manejarError(error, 'No se pudo ajustar el stock');
                    return false;
                }
                aviso(`Stock de "${rep.nombre}" actualizado (forzado).`, 'exito');
                cargar(rep.id_repuesto);
                return true;
            },
        });
    }

    // Alta (rep = null) o modificación de los datos de catálogo.
    function formularioRepuesto(rep) {
        const numeroParte = el('input', { type: 'text', id: 'rep-f-parte', value: rep?.numero_parte || '', placeholder: 'Ej: FUE-YED-138', autocomplete: 'off' });
        const nombre = el('input', { type: 'text', id: 'rep-f-nombre', value: rep?.nombre || '', placeholder: 'Ej: FUENTE YEDRO 13,8V', autocomplete: 'off' });
        const stocks = rep ? [] : talleres.map((t, i) => el('input', { type: 'number', min: '0', step: '1', value: '0', id: `rep-f-st${i}` }));
        const selector = selectorModelos(modelos, rep?.modelos || []);

        dialogoFormulario(rep ? `Modificar · ${rep.nombre}` : 'Nuevo repuesto', [
            el('label', { for: numeroParte.id }, 'N° de parte'), numeroParte,
            el('label', { for: nombre.id }, 'Nombre'), nombre,
            ...(rep ? [] : talleres.flatMap((t, i) => [el('label', { for: stocks[i].id }, `Stock inicial en ${t}`), stocks[i]])),
            selector.nodo,
        ], {
            textoAceptar: rep ? 'Guardar cambios' : 'Guardar repuesto',
            ancho: 'medio',
            alAceptar: async () => {
                const datos = { numero_parte: numeroParte.value.trim(), nombre: nombre.value.trim(), modelos: selector.elegidos() };
                if (!datos.numero_parte) { aviso('Ingresá el número de parte.', 'error'); numeroParte.focus(); return false; }
                if (!datos.nombre) { aviso('Ingresá el nombre del repuesto.', 'error'); nombre.focus(); return false; }
                if (!datos.modelos.length) { aviso('Vinculá al menos un modelo de equipo al repuesto.', 'error'); return false; }
                if (!rep) {
                    const valores = stocks.map((s) => Number(s.value));
                    if (valores.some((v) => !Number.isInteger(v) || v < 0)) {
                        aviso('El stock inicial tiene que ser un entero mayor o igual a 0.', 'error');
                        return false;
                    }
                    datos.talleres = Object.fromEntries(talleres.map((t, i) => [t, { stock: valores[i] }]));
                }
                let respuesta;
                try {
                    respuesta = rep
                        ? await api.post('modificar_repuesto.php', { id_repuesto: rep.id_repuesto, ...datos })
                        : await api.post('guardar_repuesto.php', datos);
                } catch (error) {
                    manejarError(error, rep ? 'No se pudo modificar el repuesto' : 'No se pudo guardar el repuesto');
                    return false;
                }
                aviso(rep ? 'Repuesto modificado correctamente.' : `Repuesto "${datos.nombre}" agregado.`, 'exito');
                cargar(rep ? rep.id_repuesto : respuesta?.id_repuesto);
                return true;
            },
        });
        numeroParte.focus();
    }

    async function darDeBaja(rep) {
        const ok = await confirmar('Dar de baja repuesto',
            `¿Dar de baja "${rep.nombre}" (N° de parte ${rep.numero_parte || '-'})? Se borra del catálogo con su stock y sus modelos vinculados.`,
            { aceptar: 'Dar de baja', peligro: true });
        if (!ok) return;
        try {
            await api.post('baja_repuesto.php', { id_repuesto: rep.id_repuesto });
        } catch (error) {
            manejarError(error, 'No se pudo dar de baja el repuesto');
            return;
        }
        aviso(`Repuesto "${rep.nombre}" dado de baja.`, 'exito');
        cargar(null);
    }

    function manejarError(error, contexto) {
        if (error instanceof SesionExpirada || error instanceof ClavePendiente) {
            return;
        }
        console.error(error);
        aviso(`${contexto}: ${error instanceof ApiError ? error.message : 'error inesperado'}`, 'error');
    }

    return { mostrar: () => cargar() };
}

// Lista de modelos con casillas y búsqueda, agrupable por marca.
function selectorModelos(modelos, iniciales) {
    const elegidos = new Set(iniciales);
    const filtro = el('input', { type: 'search', id: 'rep-f-modelos-buscar', placeholder: 'Buscar marca o modelo…', autocomplete: 'off' });
    const lista = el('div', { class: 'lista-modelos', role: 'group', 'aria-label': 'Modelos vinculados' });
    const resumen = el('p', { class: 'texto-suave' });

    const casillas = modelos.map((m) => {
        const c = el('input', { type: 'checkbox', value: String(m.id_modelo) });
        c.checked = elegidos.has(m.id_modelo);
        c.addEventListener('change', () => {
            if (c.checked) elegidos.add(m.id_modelo); else elegidos.delete(m.id_modelo);
            actualizar();
        });
        return { m, c, etiqueta: el('label', { class: 'casilla' }, c, ` ${m.marca} ${m.modelo_equipo}`) };
    });
    lista.append(...casillas.map((x) => x.etiqueta));

    function actualizar() {
        resumen.textContent = `${elegidos.size} modelo(s) vinculado(s)`;
    }
    filtro.addEventListener('input', () => {
        const texto = filtro.value.trim().toUpperCase();
        for (const { m, etiqueta } of casillas) {
            etiqueta.hidden = !!texto && !`${m.marca} ${m.modelo_equipo}`.toUpperCase().includes(texto);
        }
    });
    actualizar();

    return {
        nodo: el('fieldset', { class: 'casillas casillas-modelos' }, el('legend', {}, 'Modelos vinculados'), filtro, lista, resumen),
        elegidos: () => [...elegidos],
    };
}

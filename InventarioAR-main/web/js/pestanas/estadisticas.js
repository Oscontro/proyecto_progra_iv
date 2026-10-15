// Pestaña Estadísticas (equivalente a tabs/tab_estadisticas.py).
//
// Diferencias deliberadas con el cliente de escritorio:
//  - "Repuestos utilizados" usa datos reales (estadistica_repuestos.php);
//    el cliente de escritorio mostraba valores aleatorios de ejemplo.
//  - Cada gráfico usa un solo color: son conteos de una sola serie y la
//    identidad la da la etiqueta (el escritorio coloreaba cada barra distinto).

import { ApiError, SesionExpirada, ClavePendiente } from '../api.js';
import { el, aviso, subpestanas, tabla, campoSelect, llenarSelect, dialogo } from '../ui.js';
import { barrasHorizontales, contar } from '../graficos.js';

const formatoNumero = new Intl.NumberFormat('es-AR');

export function montar(contenedor, { api }) {
    // Datos crudos de la API; se recargan cada vez que se abre la pestaña.
    const datos = { equipos: [], stock: [], incidencias: [], bajas: [], repuestos: [], anios: [], escalas: [] };

    // ── Resumen (tarjetas) ──
    const anioActual = new Date().getFullYear();
    const tarjetas = {
        total_equipos: tarjeta('Total de equipos'),
        movimientos: tarjeta(`Movimientos ${anioActual}`),
        en_taller: tarjeta('En taller'),
        dados_baja: tarjeta('Dados de baja'),
    };
    const estado = el('p', { class: 'estado-carga', role: 'status' });
    contenedor.append(
        el('div', { class: 'cabecera-pestana' }, el('h2', {}, 'Estadísticas'), estado),
        el('div', { class: 'tarjetas' }, Object.values(tarjetas).map((t) => t.nodo)),
    );

    // ── Sub-pestañas ──
    const vistas = {
        distribucion: crearDistribucion(),
        stock: crearStock(),
        incidencias: crearIncidencias(),
        bajas: crearBajas(),
    };
    const sub = subpestanas(contenedor, [
        { id: 'distribucion', titulo: 'Distribución' },
        { id: 'stock', titulo: 'En stock' },
        { id: 'incidencias', titulo: 'Incidencias' },
        { id: 'bajas', titulo: 'Dados de baja' },
    ], (id, panel) => {
        if (!panel.firstChild) {
            panel.append(vistas[id].nodo);
        }
        vistas[id].dibujar();
    });

    async function cargar() {
        estado.textContent = 'Actualizando…';
        try {
            const [resumen, equipos, stock, incidencias, bajas, repuestos, anios, escalas] = await Promise.all([
                api.get('estadisticas_resumen.php'),
                api.get('estadistica_equipos.php'),
                api.get('estadistica_stock.php'),
                api.get('estadistica_incidencias.php'),
                api.get('estadistica_bajas.php'),
                api.get('estadistica_repuestos.php'),
                api.get('anios.php'),
                api.get('escalas.php'),
            ]);
            Object.assign(datos, {
                equipos, stock, incidencias, bajas, repuestos,
                anios: anios.map((a) => String(a.anio)),
                escalas: escalas.map((e) => e.escala),
            });
            for (const [clave, t] of Object.entries(tarjetas)) {
                t.valor.textContent = formatoNumero.format(resumen?.[clave] ?? 0);
            }
            for (const vista of Object.values(vistas)) {
                vista.actualizarFiltros?.();
            }
            estado.textContent = '';
            sub.refrescar();
        } catch (error) {
            if (error instanceof SesionExpirada || error instanceof ClavePendiente) {
                return;
            }
            estado.textContent = '';
            aviso(`No se pudieron cargar las estadísticas: ${error instanceof ApiError ? error.message : 'error inesperado'}`, 'error');
            console.error(error);
        }
    }

    sub.activar('distribucion');

    // ═══════════════ Distribución (estado actual) ═══════════════
    function crearDistribucion() {
        const porTipo = el('div');
        const porModelo = el('div');
        const infoEscala = el('p', { class: 'dato-destacado' });
        const tablaEscala = el('div');
        const tablaTipoModelo = el('div');
        const { nodo: filtroEscala, select } = campoSelect('Escala', [], { id: 'est-dist-escala', alCambiar: dibujarEscala });

        const nodo = el('div', { class: 'grilla-2' },
            tarjetaGrafico('Por tipo de equipo', porTipo),
            tarjetaGrafico('Por modelo', porModelo),
            el('section', { class: 'tarjeta-grafico' },
                el('h3', {}, 'Por escala'),
                el('div', { class: 'filtros' }, filtroEscala, infoEscala),
                tablaEscala),
            el('section', { class: 'tarjeta-grafico' }, el('h3', {}, 'Tipo · Modelo · Cantidad'), tablaTipoModelo));

        const activos = () => datos.equipos.filter((e) => e.anio_baja === null);

        function dibujarEscala() {
            const escala = select.value;
            const equipos = activos().filter((e) => e.escala === escala);
            const porModeloEscala = [...contar(equipos, (e) => e.modelo)].sort((a, b) => b[1] - a[1]);
            infoEscala.textContent = escala
                ? `Total en ${escala}: ${equipos.length} equipos · ${porModeloEscala.length} modelos`
                : '';
            tablaEscala.replaceChildren(tabla(
                [{ titulo: 'Modelo', valor: (f) => f[0] }, { titulo: 'Cantidad', valor: (f) => f[1], clase: 'num' }],
                porModeloEscala, { vacio: 'Sin equipos activos en esta escala' }));
        }

        return {
            nodo,
            actualizarFiltros() {
                llenarSelect(select, datos.escalas);
            },
            dibujar() {
                const lista = activos();
                barrasHorizontales(porTipo, contar(lista, (e) => e.tipo), { unidad: 'equipos' });
                barrasHorizontales(porModelo, contar(lista, (e) => e.modelo), { unidad: 'equipos', altoMaximo: '420px' });

                // Tipo / Modelo / Cantidad: por tipo y, dentro del tipo, de mayor a menor.
                const combos = [...contar(lista, (e) => `${e.tipo}\u0000${e.modelo}`)]
                    .map(([k, n]) => [...k.split('\u0000'), n])
                    .sort((a, b) => a[0].localeCompare(b[0]) || b[2] - a[2]);
                tablaTipoModelo.replaceChildren(tabla([
                    { titulo: 'Tipo', valor: (f) => f[0] },
                    { titulo: 'Modelo', valor: (f) => f[1] },
                    { titulo: 'Cantidad', valor: (f) => f[2], clase: 'num' },
                ], combos));
                dibujarEscala();
            },
        };
    }

    // ═══════════════ En stock (en taller, sin asignar) ═══════════════
    function crearStock() {
        const buscar = el('input', { type: 'search', id: 'est-stock-buscar', placeholder: 'Tipo o modelo…' });
        const talleres = el('div', { class: 'grilla-2' });
        const nodo = el('div', {},
            el('p', { class: 'texto-suave' }, 'Equipos disponibles en taller, a la espera de ser asignados a una escala.'),
            el('div', { class: 'filtros' },
                el('div', { class: 'campo campo-ancho' }, el('label', { for: buscar.id }, 'Buscar'), buscar)),
            talleres);

        buscar.addEventListener('input', dibujar);

        function dibujar() {
            const texto = buscar.value.trim().toUpperCase();
            const nombres = [...new Set(datos.stock.map((e) => e.en_stock).filter(Boolean))].sort();
            if (!nombres.length) {
                talleres.replaceChildren(el('p', { class: 'grafico-vacio' }, 'No hay equipos en stock.'));
                return;
            }
            talleres.replaceChildren(...nombres.map((taller) => {
                const grupos = new Map();
                for (const e of datos.stock) {
                    if (e.en_stock !== taller) continue;
                    if (texto && !String(e.tipo).toUpperCase().includes(texto) && !String(e.modelo).toUpperCase().includes(texto)) continue;
                    const clave = `${e.tipo}\u0000${e.modelo}`;
                    if (!grupos.has(clave)) grupos.set(clave, { tipo: e.tipo, modelo: e.modelo, series: [] });
                    grupos.get(clave).series.push(e.numero_serie);
                }
                const filas = [...grupos.values()].sort((a, b) => String(a.tipo ?? "").localeCompare(String(b.tipo ?? "")) || b.series.length - a.series.length);
                const total = filas.reduce((s, f) => s + f.series.length, 0);

                return el('section', { class: 'tarjeta-grafico' },
                    el('h3', {}, taller),
                    el('p', { class: 'dato-destacado' }, `${total} equipos sin asignar · ${filas.length} tipo/modelo`),
                    tabla([
                        { titulo: 'Tipo', valor: (f) => f.tipo },
                        { titulo: 'Modelo', valor: (f) => f.modelo },
                        { titulo: 'Cantidad', valor: (f) => f.series.length, clase: 'num' },
                        { titulo: 'N° de serie', valor: () => '', clase: 'accion' },
                    ], filas, {
                        vacio: 'Sin coincidencias',
                        alFila: (tr, f) => tr.lastChild.append(el('button', {
                            type: 'button', class: 'btn btn-chico',
                            'aria-label': `Ver N° de serie de ${f.tipo} ${f.modelo} en ${taller}`,
                            onclick: () => verSeries(`${f.tipo} · ${f.modelo} (${taller})`, f.series),
                        }, 'Ver y copiar')),
                    }));
            }));
        }

        return { nodo, dibujar };
    }

    function verSeries(titulo, series) {
        const texto = series.join('\n');
        const area = el('textarea', { class: 'lista-series', readonly: true, rows: Math.min(16, series.length + 1), 'aria-label': 'N° de serie' }, texto);
        dialogo(titulo, [el('p', { class: 'texto-suave' }, `${series.length} unidad(es)`), area], {
            acciones: [el('button', {
                type: 'button', class: 'btn btn-primario',
                onclick: async () => {
                    try {
                        await navigator.clipboard.writeText(texto);
                        aviso(`${series.length} N° de serie copiados al portapapeles.`, 'exito');
                    } catch {
                        area.select();
                        aviso('No se pudo copiar automáticamente: el texto quedó seleccionado (Ctrl+C).', 'error');
                    }
                },
            }, 'Copiar todo')],
        });
    }

    // ═══════════════ Incidencias ═══════════════
    function crearIncidencias() {
        const porTipo = el('div');
        const repuestos = el('div');
        const anio = campoSelect('Año', [], { id: 'est-inc-anio', alCambiar: () => dibujar() });
        const escala = campoSelect('Escala', [], { id: 'est-inc-escala', alCambiar: () => dibujar() });
        const modelo = campoSelect('Modelo (repuestos)', [], { id: 'est-inc-modelo', alCambiar: () => dibujar() });
        const tituloRepuestos = el('h3', {}, 'Repuestos utilizados');

        const nodo = el('div', {},
            el('div', { class: 'filtros' }, anio.nodo, escala.nodo, modelo.nodo),
            el('div', { class: 'grilla-2' },
                tarjetaGrafico('Incidencias por tipo de equipo', porTipo),
                el('section', { class: 'tarjeta-grafico' }, tituloRepuestos, repuestos)));

        function dibujar() {
            const a = anio.select.value;
            const esc = escala.select.value;
            const mod = modelo.select.value;
            const coincide = (item) => (!a || String(item.anio) === a) && (!esc || item.escala === esc);

            barrasHorizontales(porTipo, contar(datos.incidencias.filter(coincide), (i) => i.tipo),
                               { unidad: 'incidencias', vacio: 'Sin incidencias para los filtros elegidos' });

            tituloRepuestos.textContent = mod ? `Repuestos utilizados · ${mod}` : 'Repuestos utilizados';
            barrasHorizontales(repuestos,
                contar(datos.repuestos.filter((u) => coincide(u) && u.modelo === mod), (u) => u.repuesto),
                { unidad: 'usos', vacio: datos.repuestos.length
                    ? 'Sin repuestos utilizados para los filtros elegidos'
                    : 'Todavía no hay egresos de taller con repuestos registrados' });
        }

        return {
            nodo,
            dibujar,
            actualizarFiltros() {
                llenarSelect(anio.select, [{ valor: '', texto: 'Total' }, ...datos.anios]);
                llenarSelect(escala.select, [{ valor: '', texto: 'Todas' }, ...datos.escalas]);
                const modelos = [...new Set(datos.repuestos.map((u) => u.modelo))].sort();
                llenarSelect(modelo.select, modelos);
                modelo.select.disabled = !modelos.length;
            },
        };
    }

    // ═══════════════ Dados de baja ═══════════════
    function crearBajas() {
        const porModelo = el('div');
        const porEscala = el('div');
        const anio = campoSelect('Año', [], { id: 'est-bajas-anio', alCambiar: () => dibujar() });

        const nodo = el('div', {},
            el('div', { class: 'filtros' }, anio.nodo),
            el('div', { class: 'grilla-2' },
                tarjetaGrafico('Dados de baja por modelo', porModelo),
                tarjetaGrafico('Dados de baja por escala', porEscala)));

        function dibujar() {
            const a = anio.select.value;
            const bajas = datos.bajas.filter((e) => e.anio_baja !== null && (!a || String(e.anio_baja) === a));
            const opciones = { unidad: 'bajas', altoMaximo: '420px', vacio: 'Sin bajas para el año elegido' };
            barrasHorizontales(porModelo, contar(bajas, (e) => e.modelo), opciones);
            barrasHorizontales(porEscala, contar(bajas, (e) => e.escala), opciones);
        }

        return {
            nodo,
            dibujar,
            actualizarFiltros() {
                // Años de baja presentes en los datos (no solo los de anios.php).
                const anios = [...new Set([...datos.anios, ...datos.bajas.map((e) => e.anio_baja).filter((x) => x !== null).map(String)])]
                    .sort().reverse();
                llenarSelect(anio.select, [{ valor: '', texto: 'Total' }, ...anios]);
            },
        };
    }

    return { mostrar: cargar };
}

function tarjeta(etiqueta) {
    const valor = el('p', { class: 'tarjeta-valor' }, '—');
    return { valor, nodo: el('div', { class: 'tarjeta-dato' }, el('p', { class: 'tarjeta-etiqueta' }, etiqueta), valor) };
}

function tarjetaGrafico(titulo, cuerpo) {
    return el('section', { class: 'tarjeta-grafico' }, el('h3', {}, titulo), cuerpo);
}

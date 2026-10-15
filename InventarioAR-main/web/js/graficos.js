// Gráficos livianos en HTML/CSS (sin librerías), para conteos por categoría.
//
// Criterios (guía de visualización):
//  - Una sola serie por gráfico -> un solo color; la identidad la da la etiqueta.
//  - Barras horizontales ordenadas de mayor a menor, finas (<= 22px),
//    extremo redondeado y base recta; valor al final de cada barra.
//  - Texto siempre en tinta neutra (nunca del color de la barra).
//  - Tooltip al pasar el mouse o con foco de teclado (valor y porcentaje).
//  - Muchas categorías -> el contenedor hace scroll vertical.

import { el } from './ui.js';

const formatoNumero = new Intl.NumberFormat('es-AR');
const formatoPorcentaje = new Intl.NumberFormat('es-AR', { style: 'percent', maximumFractionDigits: 1 });

/**
 * Cuenta ocurrencias: contar(lista, e => e.tipo) -> Map(tipo -> cantidad).
 * Con `peso`, suma ese valor en vez de contar 1 (p. ej. unidades por fila).
 */
export function contar(lista, clave, peso = () => 1) {
    const mapa = new Map();
    for (const item of lista) {
        const k = clave(item);
        if (k === null || k === undefined || k === '') {
            continue;
        }
        mapa.set(k, (mapa.get(k) || 0) + peso(item));
    }
    return mapa;
}

/**
 * Dibuja barras horizontales dentro de `contenedor`.
 *   datos: Map o array de [etiqueta, valor]
 *   opciones: { unidad: 'equipos', vacio: 'Sin datos', altoMaximo: '420px' }
 */
export function barrasHorizontales(contenedor, datos, { unidad = '', vacio = 'Sin datos', altoMaximo = null } = {}) {
    const filas = [...datos].filter(([, v]) => v > 0).sort((a, b) => b[1] - a[1] || String(a[0]).localeCompare(String(b[0])));
    const total = filas.reduce((s, [, v]) => s + v, 0);
    const maximo = filas.length ? filas[0][1] : 0;

    const resumen = el('p', { class: 'grafico-total' },
        'Total: ', el('strong', {}, formatoNumero.format(total)), unidad ? ` ${unidad}` : '');

    if (!filas.length) {
        contenedor.replaceChildren(el('p', { class: 'grafico-vacio' }, vacio));
        return;
    }

    const lista = el('ul', { class: 'barras', role: 'list' });
    if (altoMaximo) {
        lista.style.maxHeight = altoMaximo;
    }

    for (const [etiqueta, valor] of filas) {
        const detalle = `${etiqueta}: ${formatoNumero.format(valor)}${unidad ? ` ${unidad}` : ''} (${formatoPorcentaje.format(valor / total)})`;
        const barra = el('span', { class: 'barra-dato' });
        barra.style.width = `${(valor / maximo) * 100}%`;
        lista.append(el('li', { class: 'barras-fila', tabindex: '0', 'aria-label': detalle, dataset: { detalle } },
            el('span', { class: 'barras-etiqueta' }, String(etiqueta)),
            el('span', { class: 'barras-pista' }, barra, el('span', { class: 'barras-valor' }, formatoNumero.format(valor)))));
    }

    conectarTooltip(lista);
    contenedor.replaceChildren(resumen, lista);
}

// Un único tooltip por documento, reutilizado por todos los gráficos.
let tooltip = null;

function conectarTooltip(lista) {
    if (!tooltip) {
        tooltip = el('div', { class: 'tooltip', role: 'tooltip', hidden: true });
        document.body.append(tooltip);
    }

    const mostrar = (fila, x, y) => {
        tooltip.textContent = fila.dataset.detalle;
        tooltip.hidden = false;
        const ancho = tooltip.offsetWidth;
        const izquierda = Math.min(x + 14, window.innerWidth - ancho - 8);
        tooltip.style.left = `${Math.max(8, izquierda)}px`;
        tooltip.style.top = `${y + 14}px`;
    };
    const ocultar = () => { tooltip.hidden = true; };

    lista.addEventListener('mousemove', (evento) => {
        const fila = evento.target.closest('.barras-fila');
        if (fila) {
            mostrar(fila, evento.clientX, evento.clientY);
        } else {
            ocultar();
        }
    });
    lista.addEventListener('mouseleave', ocultar);
    lista.addEventListener('focusin', (evento) => {
        const fila = evento.target.closest('.barras-fila');
        if (fila) {
            const caja = fila.getBoundingClientRect();
            mostrar(fila, caja.left + caja.width / 2, caja.bottom - 10);
        }
    });
    lista.addEventListener('focusout', ocultar);
    lista.addEventListener('scroll', ocultar);
}

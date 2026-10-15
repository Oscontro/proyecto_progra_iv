// Tabla con selección de una fila, orden por columna y navegación por teclado.
// La usan Inventario y Papelera (equivale a los QTableWidget de selección
// por filas del cliente de escritorio).
//
//   const t = tablaSeleccionable({
//       columnas: [{ clave: 'tipo', titulo: 'Tipo' }, ...],
//       etiqueta: 'Equipos del inventario',
//       unidad: 'equipos',
//       alSeleccionar: (fila | null) => {...},
//       alActivar: (fila) => {...},          // doble clic o Enter
//       formato: (valor) => texto,           // opcional
//   });
//   contenedor.append(t.contador, t.nodo);
//   t.mostrar(filasFiltradas, totalSinFiltrar);

import { el, textoCelda } from './ui.js';

const comparar = new Intl.Collator('es', { numeric: true, sensitivity: 'base' }).compare;

export function tablaSeleccionable({ columnas, etiqueta, unidad = 'filas', alSeleccionar, alActivar, formato = textoCelda }) {
    let filas = [];
    let total = 0;
    let seleccionada = null;   // el registro (no el índice: sobrevive a ordenar y filtrar)
    let orden = { clave: null, ascendente: true };

    const cuerpo = el('tbody');
    const cabeceras = columnas.map((c) => el('th', { scope: 'col', 'aria-sort': 'none' },
        el('button', { type: 'button', class: 'th-orden', onclick: () => ordenarPor(c.clave) }, c.titulo)));
    const nodo = el('div', {
        class: 'tabla-contenedor tabla-alta', tabindex: '0', role: 'region',
        'aria-label': `${etiqueta}. Usá las flechas para elegir una fila${alActivar ? ' y Enter para abrirla' : ''}.`,
    }, el('table', { class: 'tabla tabla-seleccionable' },
        el('thead', {}, el('tr', {}, cabeceras)), cuerpo));
    const contador = el('p', { class: 'texto-suave contador' });

    cuerpo.addEventListener('click', (evento) => {
        const tr = evento.target.closest('tr[data-indice]');
        if (tr) seleccionar(filas[Number(tr.dataset.indice)]);
    });
    cuerpo.addEventListener('dblclick', (evento) => {
        const tr = evento.target.closest('tr[data-indice]');
        if (tr && alActivar) alActivar(filas[Number(tr.dataset.indice)]);
    });
    nodo.addEventListener('keydown', (evento) => {
        if (!filas.length) return;
        const actual = filas.indexOf(seleccionada);
        const destino = {
            ArrowDown: Math.min(actual + 1, filas.length - 1),
            ArrowUp: Math.max(actual - 1, 0),
            Home: 0,
            End: filas.length - 1,
        }[evento.key];
        if (evento.key === 'Enter' && seleccionada && alActivar) {
            evento.preventDefault();
            alActivar(seleccionada);
        } else if (destino !== undefined) {
            evento.preventDefault();
            seleccionar(filas[destino]);
            cuerpo.children[destino]?.scrollIntoView({ block: 'nearest' });
        }
    });

    function ordenarPor(clave) {
        orden = { clave, ascendente: orden.clave === clave ? !orden.ascendente : true };
        cabeceras.forEach((th, i) => th.setAttribute('aria-sort',
            columnas[i].clave === clave ? (orden.ascendente ? 'ascending' : 'descending') : 'none'));
        mostrar(filas, total);
    }

    function mostrar(nuevas, nuevoTotal = nuevas.length) {
        filas = [...nuevas];
        total = nuevoTotal;
        if (orden.clave) {
            const { clave, ascendente } = orden;
            filas.sort((a, b) => (ascendente ? 1 : -1) * comparar(textoCelda(a[clave]), textoCelda(b[clave])));
        }

        const fragmento = document.createDocumentFragment();
        filas.forEach((fila, i) => {
            fragmento.append(el('tr', { dataset: { indice: i } },
                columnas.map((c) => el('td', {}, formato(fila[c.clave], c.clave)))));
        });
        if (!filas.length) {
            fragmento.append(el('tr', {}, el('td', { colspan: columnas.length, class: 'tabla-vacia' },
                total ? 'Ningún registro coincide con los filtros' : 'Sin datos')));
        }
        cuerpo.replaceChildren(fragmento);
        contador.textContent = `Mostrando ${filas.length} de ${total} ${unidad}`;
        seleccionar(filas.includes(seleccionada) ? seleccionada : null);
    }

    function seleccionar(fila) {
        seleccionada = fila;
        for (const tr of cuerpo.querySelectorAll('tr[data-indice]')) {
            const elegida = filas[Number(tr.dataset.indice)] === fila;
            tr.classList.toggle('seleccionada', elegida);
            tr.setAttribute('aria-selected', String(elegida));
        }
        alSeleccionar?.(fila);
    }

    return {
        nodo,
        contador,
        mostrar,
        get seleccionada() { return seleccionada; },
        get filas() { return filas; },
    };
}

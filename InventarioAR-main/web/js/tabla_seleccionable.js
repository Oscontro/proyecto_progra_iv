// Tabla con selección de filas, orden por columna y navegación por teclado.
// La usan Inventario, Papelera, Taller y Repuestos (equivale a los QTableWidget de selección
// por filas del cliente de escritorio).
//
//   const t = tablaSeleccionable({
//       columnas: [{ clave: 'tipo', titulo: 'Tipo' }, ...],
//       etiqueta: 'Equipos del inventario',
//       unidad: 'equipos',
//       multiple: true,                      // opcional: permite elegir varias filas
//       alSeleccionar: (fila | null, seleccionadas) => {...},
//       alActivar: (fila) => {...},          // doble clic o Enter
//       formato: (valor) => texto,           // opcional
//   });
//
// Con `multiple`: Ctrl+clic suma o quita una fila, Mayús+clic (o Mayús+flechas)
// elige un rango, Ctrl+A elige todas las visibles, y hay una columna de casillas
// (útil con el mouse y en pantallas táctiles). `fila` es la elegida solo cuando
// hay exactamente una; `seleccionadas` trae todas, en el orden de la tabla.
//
// Opciones por columna: `pildora: true` muestra el valor como etiqueta de color
// según su texto (estados); `mono: true` usa letra monoespaciada (números de serie).
//   contenedor.append(t.contador, t.nodo);
//   t.mostrar(filasFiltradas, totalSinFiltrar);

import { el, textoCelda } from './ui.js';

const comparar = new Intl.Collator('es', { numeric: true, sensitivity: 'base' }).compare;

// Tono de la píldora según el texto del estado (los estados son texto libre en la base).
// El orden importa: "desactivado" contiene "activ" y "reparado" contiene "repar".
const TONOS = [
    ['rojo', /sin stock|baja|fallid|desactivad|irreparable|bloquead/],
    ['verde', /^ok$|en uso|operativ|servicio|activ|reparad|egresad|leida|exitos/],
    ['ambar', /bajo|repar|diagnost|taller|pendiente|nueva|ingresad|espera|recib/],
    ['azul', /stock|disponible/],
];

function tonoDe(texto) {
    const normal = texto.toLowerCase().normalize('NFD').replace(/[̀-ͯ]/g, '');
    return TONOS.find(([, patron]) => patron.test(normal))?.[0] ?? 'neutro';
}

function celda(texto, columna) {
    if (columna.pildora && texto && texto !== '-') {
        return el('td', {}, el('span', { class: `pildora pildora-${tonoDe(texto)}` }, texto));
    }
    return el('td', { class: columna.mono ? 'mono' : null }, texto);
}

export function tablaSeleccionable({ columnas, etiqueta, unidad = 'filas', multiple = false, alSeleccionar, alActivar, formato = textoCelda }) {
    let filas = [];
    let total = 0;
    // Registros (no índices: sobreviven a ordenar y filtrar). `ancla` es el
    // origen de los rangos (la última fila elegida a mano) y `extremo` la
    // punta que mueven las flechas.
    let elegidas = new Set();
    let ancla = null;
    let extremo = null;
    let orden = { clave: null, ascendente: true };

    const cuerpo = el('tbody');
    const cabeceras = columnas.map((c) => el('th', { scope: 'col', 'aria-sort': 'none' },
        el('button', { type: 'button', class: 'th-orden', onclick: () => ordenarPor(c.clave) }, c.titulo)));
    const casillaTodas = multiple
        ? el('input', { type: 'checkbox', 'aria-label': 'Seleccionar todas las filas visibles', onchange: () => elegirTodas(casillaTodas.checked) })
        : null;
    const nodo = el('div', {
        class: 'tabla-contenedor tabla-alta', tabindex: '0', role: 'region',
        'aria-label': `${etiqueta}. Usá las flechas para elegir una fila${multiple ? ' (con Mayús, varias)' : ''}${alActivar ? ' y Enter para abrirla' : ''}.`,
    }, el('table', { class: 'tabla tabla-seleccionable', 'aria-multiselectable': multiple ? 'true' : null },
        el('thead', {}, el('tr', {}, multiple ? el('th', { scope: 'col', class: 'col-casilla' }, casillaTodas) : null, cabeceras)),
        cuerpo));
    const contador = el('p', { class: 'texto-suave contador' });

    cuerpo.addEventListener('click', (evento) => {
        const tr = evento.target.closest('tr[data-indice]');
        if (!tr) return;
        const fila = filas[Number(tr.dataset.indice)];
        const ctrl = evento.ctrlKey || evento.metaKey;
        if (!multiple) {
            seleccionar(fila);
        } else if (evento.shiftKey && ancla) {
            elegirRango(fila, ctrl);
        } else if (ctrl || evento.target.matches('input[type="checkbox"]')) {
            alternar(fila);
        } else {
            seleccionar(fila);
        }
    });
    // Mayús+clic no tiene que seleccionar el texto de las celdas.
    cuerpo.addEventListener('mousedown', (evento) => {
        if (multiple && evento.shiftKey) evento.preventDefault();
    });
    cuerpo.addEventListener('dblclick', (evento) => {
        const tr = evento.target.closest('tr[data-indice]');
        if (tr && alActivar && !evento.target.matches('input')) alActivar(filas[Number(tr.dataset.indice)]);
    });
    nodo.addEventListener('keydown', (evento) => {
        if (!filas.length || evento.target.matches('input')) return;
        if (multiple && (evento.ctrlKey || evento.metaKey) && evento.key.toLowerCase() === 'a') {
            evento.preventDefault();
            elegirTodas(true);
            return;
        }
        const actual = filas.indexOf(extremo);
        const destino = {
            ArrowDown: Math.min(actual + 1, filas.length - 1),
            ArrowUp: Math.max(actual - 1, 0),
            Home: 0,
            End: filas.length - 1,
        }[evento.key];
        const unica = unicaElegida();
        if (evento.key === 'Enter' && unica && alActivar) {
            evento.preventDefault();
            alActivar(unica);
        } else if (destino !== undefined) {
            evento.preventDefault();
            if (multiple && evento.shiftKey && ancla) {
                elegirRango(filas[destino], false);
            } else {
                seleccionar(filas[destino]);
            }
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
                multiple ? el('td', { class: 'col-casilla' }, el('input', { type: 'checkbox', tabindex: '-1', 'aria-label': 'Seleccionar fila' })) : null,
                columnas.map((c) => celda(formato(fila[c.clave], c.clave), c))));
        });
        if (!filas.length) {
            fragmento.append(el('tr', {}, el('td', { colspan: columnas.length + (multiple ? 1 : 0), class: 'tabla-vacia' },
                total ? 'Ningún registro coincide con los filtros' : 'Sin datos')));
        }
        cuerpo.replaceChildren(fragmento);
        // Las filas que el filtro ocultó dejan de estar elegidas: las acciones solo tocan lo que se ve.
        elegidas = new Set(filas.filter((f) => elegidas.has(f)));
        if (!filas.includes(ancla)) ancla = null;
        if (!filas.includes(extremo)) extremo = ancla;
        aplicarSeleccion();
    }

    // Contador + pista: mientras no haya fila elegida, se indica cómo habilitar las acciones.
    function actualizarContador() {
        let pista = '';
        if (!elegidas.size && filas.length) {
            pista = ` · Seleccioná una fila para habilitar las acciones${multiple ? ' (Ctrl o Mayús para elegir varias)' : ''}`;
        } else if (multiple && elegidas.size) {
            pista = ` · ${elegidas.size} seleccionad${elegidas.size === 1 ? 'a' : 'as'}`;
        }
        contador.replaceChildren(`Mostrando ${filas.length} de ${total} ${unidad}`,
            pista ? el('span', { class: 'pista' }, pista) : '');
    }

    function unicaElegida() {
        return elegidas.size === 1 ? elegidas.values().next().value : null;
    }

    function seleccionar(fila) {
        elegidas = new Set(fila ? [fila] : []);
        ancla = extremo = fila;
        aplicarSeleccion();
    }

    function alternar(fila) {
        if (elegidas.has(fila)) {
            elegidas.delete(fila);
        } else {
            elegidas.add(fila);
        }
        ancla = extremo = fila;
        aplicarSeleccion();
    }

    // Rango entre el ancla y `fila`; con `sumar` (Ctrl+Mayús) se conserva lo ya elegido.
    function elegirRango(fila, sumar) {
        const desde = filas.indexOf(ancla);
        const hasta = filas.indexOf(fila);
        const rango = filas.slice(Math.min(desde, hasta), Math.max(desde, hasta) + 1);
        elegidas = new Set(sumar ? [...elegidas, ...rango] : rango);
        extremo = fila;
        aplicarSeleccion();
    }

    function elegirTodas(todas) {
        elegidas = new Set(todas ? filas : []);
        aplicarSeleccion();
    }

    function aplicarSeleccion() {
        actualizarContador();
        for (const tr of cuerpo.querySelectorAll('tr[data-indice]')) {
            const elegida = elegidas.has(filas[Number(tr.dataset.indice)]);
            tr.classList.toggle('seleccionada', elegida);
            tr.setAttribute('aria-selected', String(elegida));
            if (multiple) tr.querySelector('.col-casilla input').checked = elegida;
        }
        if (casillaTodas) {
            casillaTodas.checked = filas.length > 0 && elegidas.size === filas.length;
            casillaTodas.indeterminate = elegidas.size > 0 && elegidas.size < filas.length;
        }
        alSeleccionar?.(unicaElegida(), filas.filter((f) => elegidas.has(f)));
    }

    return {
        nodo,
        contador,
        mostrar,
        /** Vuelve a seleccionar la fila que cumpla `condicion` (p. ej. tras recargar los datos). */
        seleccionarDonde(condicion) {
            const indice = filas.findIndex(condicion);
            seleccionar(indice >= 0 ? filas[indice] : null);
            if (indice >= 0) cuerpo.children[indice]?.scrollIntoView({ block: 'nearest' });
        },
        /** La fila elegida si hay exactamente una; si no, null. */
        get seleccionada() { return unicaElegida(); },
        /** Todas las filas elegidas, en el orden de la tabla. */
        get seleccionadas() { return filas.filter((f) => elegidas.has(f)); },
        get filas() { return filas; },
    };
}

// Utilidades de interfaz compartidas por todas las vistas y pestañas.
//
// Regla: los datos que vienen de la API se insertan SIEMPRE como texto
// (textContent), nunca como HTML, para evitar inyección de código (XSS).

/**
 * Crea un elemento. Los hijos de tipo string se agregan como texto.
 *   el('button', { class: 'btn', type: 'button', onclick: fn }, 'Guardar')
 */
export function el(tag, atributos = {}, ...hijos) {
    const nodo = document.createElement(tag);
    for (const [clave, valor] of Object.entries(atributos)) {
        if (valor === null || valor === undefined || valor === false) {
            continue;
        }
        if (clave.startsWith('on') && typeof valor === 'function') {
            nodo.addEventListener(clave.slice(2), valor);
        } else if (clave === 'dataset') {
            Object.assign(nodo.dataset, valor);
        } else if (valor === true) {
            nodo.setAttribute(clave, '');
        } else {
            nodo.setAttribute(clave, valor);
        }
    }
    for (const hijo of hijos.flat()) {
        if (hijo === null || hijo === undefined || hijo === false) {
            continue;
        }
        nodo.append(hijo instanceof Node ? hijo : String(hijo));
    }
    return nodo;
}

/** Clona el contenido de un <template id="..."> de app.php. */
export function plantilla(id) {
    return document.getElementById(id).content.firstElementChild.cloneNode(true);
}

// ─────────────────────────────────────────────────────────
// Avisos breves (reemplazan a los QMessageBox informativos)
// ─────────────────────────────────────────────────────────
export function aviso(mensaje, tipo = 'info') {
    const zona = document.getElementById('avisos');
    const nodo = el('div', { class: `aviso aviso-${tipo}`, role: tipo === 'error' ? 'alert' : 'status' }, mensaje);
    zona.append(nodo);
    setTimeout(() => nodo.classList.add('saliendo'), 4500);
    setTimeout(() => nodo.remove(), 5000);
}

// ─────────────────────────────────────────────────────────
// Diálogo modal de confirmación. Devuelve una promesa con true/false.
// ─────────────────────────────────────────────────────────
export function confirmar(titulo, mensaje, { aceptar = 'Aceptar', cancelar = 'Cancelar', peligro = false } = {}) {
    return new Promise((resolver) => {
        // Los botones resuelven y cierran directamente (sin depender del
        // evento 'close'); Escape dispara 'close' y cuenta como cancelar.
        let resuelto = false;
        const terminar = (valor) => {
            if (resuelto) return;
            resuelto = true;
            resolver(valor);
            if (dialogo.open) dialogo.close();
            dialogo.remove();
        };
        const dialogo = el('dialog', { class: 'modal', 'aria-label': titulo },
            el('h2', {}, titulo),
            el('p', {}, mensaje),
            el('div', { class: 'modal-acciones' },
                el('button', { type: 'button', class: 'btn btn-secundario', onclick: () => terminar(false) }, cancelar),
                el('button', { type: 'button', class: peligro ? 'btn btn-peligro' : 'btn btn-primario', onclick: () => terminar(true) }, aceptar),
            ),
        );
        dialogo.addEventListener('close', () => terminar(false));
        document.body.append(dialogo);
        dialogo.showModal();
    });
}

/** Deshabilita un formulario mientras corre una operación asíncrona. */
export async function ocupado(formulario, operacion) {
    // Se recuerda el estado de cada control para no habilitar al final
    // uno que ya estaba deshabilitado a propósito.
    const controles = [...formulario.querySelectorAll('input, button, select, textarea')]
        .map((c) => [c, c.disabled]);
    controles.forEach(([c]) => { c.disabled = true; });
    formulario.setAttribute('aria-busy', 'true');
    try {
        return await operacion();
    } finally {
        controles.forEach(([c, estabaDeshabilitado]) => { c.disabled = estabaDeshabilitado; });
        formulario.removeAttribute('aria-busy');
    }
}

// ─────────────────────────────────────────────────────────
// Sub-pestañas (patrón ARIA tablist) dentro de una pestaña.
//   const sub = subpestanas(contenedor, [{ id, titulo }], (id, panel) => {...})
// `alAbrir` se llama cada vez que se activa una sub-pestaña.
// ─────────────────────────────────────────────────────────
export function subpestanas(contenedor, definiciones, alAbrir) {
    const barra = el('div', { class: 'subpestanas', role: 'tablist' });
    const paneles = new Map();
    const botones = new Map();
    let activa = null;

    function activar(id, enfocar = false) {
        activa = id;
        for (const [otro, boton] of botones) {
            boton.setAttribute('aria-selected', String(otro === id));
            boton.tabIndex = otro === id ? 0 : -1;
            paneles.get(otro).hidden = otro !== id;
        }
        if (enfocar) {
            botones.get(id).focus();
        }
        alAbrir(id, paneles.get(id));
    }

    for (const { id, titulo } of definiciones) {
        const idBoton = `sub-${id}`;
        const panel = el('div', { class: 'subpanel', role: 'tabpanel', id: `subpanel-${id}`, 'aria-labelledby': idBoton, hidden: true });
        const boton = el('button', {
            type: 'button', role: 'tab', id: idBoton, 'aria-controls': panel.id,
            'aria-selected': 'false', tabindex: '-1', onclick: () => activar(id),
        }, titulo);
        paneles.set(id, panel);
        botones.set(id, boton);
        barra.append(boton);
    }

    barra.addEventListener('keydown', (evento) => {
        const ids = definiciones.map((d) => d.id);
        const i = ids.indexOf(activa);
        const destino = { ArrowRight: (i + 1) % ids.length, ArrowLeft: (i - 1 + ids.length) % ids.length,
                          Home: 0, End: ids.length - 1 }[evento.key];
        if (destino !== undefined) {
            evento.preventDefault();
            activar(ids[destino], true);
        }
    });

    contenedor.append(barra, ...paneles.values());
    return {
        activar,
        get activa() { return activa; },
        refrescar() { if (activa) alAbrir(activa, paneles.get(activa)); },
    };
}

// ─────────────────────────────────────────────────────────
// Tabla simple. columnas: [{ titulo, valor: fila => texto, clase }]
// ─────────────────────────────────────────────────────────
export function tabla(columnas, filas, { vacio = 'Sin datos', alFila = null } = {}) {
    const cuerpo = el('tbody');
    if (!filas.length) {
        cuerpo.append(el('tr', {}, el('td', { colspan: columnas.length, class: 'tabla-vacia' }, vacio)));
    }
    for (const fila of filas) {
        const tr = el('tr', {}, columnas.map((c) => el('td', { class: c.clase }, textoCelda(c.valor(fila)))));
        alFila?.(tr, fila);
        cuerpo.append(tr);
    }
    return el('div', { class: 'tabla-contenedor' },
        el('table', { class: 'tabla' },
            el('thead', {}, el('tr', {}, columnas.map((c) => el('th', { scope: 'col', class: c.clase }, c.titulo)))),
            cuerpo));
}

/** null/undefined se muestran vacíos (equivale a pd.notna en el cliente de escritorio). */
export function textoCelda(valor) {
    return valor === null || valor === undefined ? '' : String(valor);
}

// ─────────────────────────────────────────────────────────
// <select> con etiqueta. opciones: array de strings o de { valor, texto }.
// ─────────────────────────────────────────────────────────
export function campoSelect(etiqueta, opciones, { id, alCambiar } = {}) {
    const select = el('select', { id, onchange: () => alCambiar?.(select.value) });
    llenarSelect(select, opciones);
    return { nodo: el('div', { class: 'campo' }, el('label', { for: id }, etiqueta), select), select };
}

// ─────────────────────────────────────────────────────────
// Texto con sugerencias: se elige de la lista o se escribe un valor libre.
// Reemplaza a <datalist>, cuyo desplegable dibuja el navegador sin estilo y
// fuera de lugar. Al elegir dispara 'input' y 'change' como el nativo.
//
//   const c = campoSugerencias({ id: 'ing-marca', maxlength: 100 });
//   contenedor.append(c.nodo);  c.sugerir(['Motorola', 'ICOM']);  c.input.value
// ─────────────────────────────────────────────────────────
export function campoSugerencias(atributos = {}) {
    let valores = [];
    let activo = -1;
    const lista = el('ul', { class: 'sugerencias', role: 'listbox', id: `${atributos.id}-lista`, hidden: true });
    const input = el('input', {
        type: 'text', autocomplete: 'off', role: 'combobox', 'aria-autocomplete': 'list',
        'aria-expanded': 'false', 'aria-controls': lista.id, ...atributos,
    });
    const normal = (t) => t.toLowerCase().normalize('NFD').replace(/[̀-ͯ]/g, '');

    // filtrar: al escribir se muestran las que coinciden; al hacer clic, todas.
    function abrir(filtrar = false) {
        const texto = filtrar ? normal(input.value.trim()) : '';
        const items = texto ? valores.filter((v) => normal(v).includes(texto)) : valores;
        if (!items.length || (filtrar && items.length === 1 && items[0] === input.value)) {
            cerrar();
            return;
        }
        activo = -1;
        lista.replaceChildren(...items.map((v, i) => el('li', {
            role: 'option', id: `${lista.id}-${i}`, 'aria-selected': 'false',
            // mousedown (no click): elige antes de que el input pierda el foco
            onmousedown: (evento) => { evento.preventDefault(); elegir(v); },
        }, v)));
        lista.hidden = false;
        input.setAttribute('aria-expanded', 'true');
        input.removeAttribute('aria-activedescendant');
        ubicar();
        addEventListener('scroll', ubicar, true);
        addEventListener('resize', ubicar);
        const actual = items.indexOf(input.value);
        if (actual >= 0) marcar(actual);
    }

    function cerrar() {
        lista.hidden = true;
        activo = -1;
        input.setAttribute('aria-expanded', 'false');
        input.removeAttribute('aria-activedescendant');
        removeEventListener('scroll', ubicar, true);
        removeEventListener('resize', ubicar);
    }

    // Posición fija bajo el campo y con su mismo ancho: así no la recortan los
    // contenedores con scroll (diálogos). Si abajo no entra, se abre hacia arriba.
    function ubicar() {
        const r = input.getBoundingClientRect();
        const abajo = innerHeight - r.bottom;
        const arriba = abajo < 200 && r.top > abajo;
        lista.style.left = `${r.left}px`;
        lista.style.width = `${r.width}px`;
        lista.style.top = arriba ? '' : `${r.bottom + 4}px`;
        lista.style.bottom = arriba ? `${innerHeight - r.top + 4}px` : '';
        lista.style.maxHeight = `${Math.min(260, (arriba ? r.top : abajo) - 16)}px`;
    }

    function marcar(indice) {
        const opciones = [...lista.children];
        activo = (indice + opciones.length) % opciones.length;
        opciones.forEach((o, i) => o.setAttribute('aria-selected', String(i === activo)));
        input.setAttribute('aria-activedescendant', opciones[activo].id);
        opciones[activo].scrollIntoView({ block: 'nearest' });
    }

    function elegir(valor) {
        input.value = valor;
        cerrar();
        input.dispatchEvent(new Event('input', { bubbles: true }));
        input.dispatchEvent(new Event('change', { bubbles: true }));
    }

    input.addEventListener('click', () => abrir());
    input.addEventListener('input', (evento) => { if (evento.isTrusted) abrir(true); });
    input.addEventListener('blur', cerrar);
    input.addEventListener('keydown', (evento) => {
        if (evento.key === 'ArrowDown') {
            evento.preventDefault();
            if (lista.hidden) abrir();
            if (!lista.hidden) marcar(activo + 1);
        } else if (evento.key === 'ArrowUp' && !lista.hidden) {
            evento.preventDefault();
            marcar(activo - 1);
        } else if (evento.key === 'Enter' && !lista.hidden && activo >= 0) {
            evento.preventDefault();
            elegir(lista.children[activo].textContent);
        } else if (evento.key === 'Escape' && !lista.hidden) {
            evento.preventDefault();   // en un diálogo, cierra la lista y no el diálogo
            cerrar();
        }
    });

    return {
        nodo: el('div', { class: 'combo' }, input, lista),
        input,
        sugerir(nuevos) {
            valores = [...new Set(nuevos.filter(Boolean))];
            if (!lista.hidden) abrir(true);
        },
    };
}

/** Reemplaza las opciones conservando la elegida si sigue existiendo. */
export function llenarSelect(select, opciones) {
    const anterior = select.value;
    select.replaceChildren(...opciones.map((o) => {
        const { valor, texto } = typeof o === 'object' ? o : { valor: o, texto: o };
        return el('option', { value: valor }, texto);
    }));
    if ([...select.options].some((o) => o.value === anterior)) {
        select.value = anterior;
    }
}

// ─────────────────────────────────────────────────────────
// Diálogo modal genérico con contenido libre y botón Cerrar.
// ─────────────────────────────────────────────────────────
export function dialogo(titulo, contenido, { acciones = [], ancho = 'normal' } = {}) {
    const cerrar = () => {
        if (modal.open) modal.close();
        modal.remove();
    };
    const modal = el('dialog', { class: `modal modal-${ancho}`, 'aria-label': titulo },
        el('div', { class: 'modal-cabecera' },
            el('h2', {}, titulo),
            el('button', { type: 'button', class: 'modal-cerrar', 'aria-label': 'Cerrar', onclick: cerrar }, '✕')),
        el('div', { class: 'modal-cuerpo' }, contenido),
        el('div', { class: 'modal-acciones' },
            ...acciones,
            el('button', { type: 'button', class: 'btn btn-secundario', onclick: cerrar }, 'Cerrar')));
    modal.addEventListener('close', cerrar);   // Escape
    document.body.append(modal);
    modal.showModal();
    return modal;
}

// ─────────────────────────────────────────────────────────
// Diálogo con formulario. `alAceptar` recibe el <form> y devuelve true si
// la operación salió bien (entonces se cierra); si devuelve false o lanza
// un error, el diálogo queda abierto con los datos cargados.
// ─────────────────────────────────────────────────────────
export function dialogoFormulario(titulo, contenido, { textoAceptar = 'Guardar', alAceptar, ancho = 'normal' }) {
    const cerrar = () => {
        if (modal.open) modal.close();
        modal.remove();
    };
    const form = el('form', { class: 'formulario', novalidate: true },
        el('div', { class: 'modal-cuerpo' }, contenido),
        el('div', { class: 'modal-acciones' },
            el('button', { type: 'button', class: 'btn btn-secundario', onclick: cerrar }, 'Cancelar'),
            el('button', { type: 'submit', class: 'btn btn-primario' }, textoAceptar)));
    const modal = el('dialog', { class: `modal modal-${ancho}`, 'aria-label': titulo },
        el('div', { class: 'modal-cabecera' },
            el('h2', {}, titulo),
            el('button', { type: 'button', class: 'modal-cerrar', 'aria-label': 'Cerrar', onclick: cerrar }, '✕')),
        form);

    form.addEventListener('submit', async (evento) => {
        evento.preventDefault();
        let ok = false;
        try {
            ok = await ocupado(form, () => alAceptar(form));
        } catch (error) {
            console.error(error);
        }
        if (ok) cerrar();
    });
    modal.addEventListener('close', cerrar);   // Escape
    document.body.append(modal);
    modal.showModal();
    return { modal, form, cerrar };
}

/** Grupo de casillas. opciones: [{ valor, texto }]. Devuelve { nodo, marcadas() }. */
export function grupoCasillas(leyenda, nombre, opciones) {
    const casillas = opciones.map((o) => el('input', { type: 'checkbox', name: nombre, value: o.valor }));
    const nodo = el('fieldset', { class: 'casillas' },
        el('legend', {}, leyenda),
        opciones.map((o, i) => el('label', { class: 'casilla' }, casillas[i], ` ${o.texto}`)));
    return { nodo, casillas, marcadas: () => casillas.filter((c) => c.checked).map((c) => c.value) };
}

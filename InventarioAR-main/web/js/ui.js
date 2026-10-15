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

/** Clona el contenido de un <template id="..."> de index.html. */
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
        const dialogo = el('dialog', { class: 'modal' },
            el('form', { method: 'dialog' },
                el('h2', {}, titulo),
                el('p', {}, mensaje),
                el('div', { class: 'modal-acciones' },
                    el('button', { class: 'btn btn-secundario', value: 'no' }, cancelar),
                    el('button', { class: peligro ? 'btn btn-peligro' : 'btn btn-primario', value: 'si' }, aceptar),
                ),
            ),
        );
        dialogo.addEventListener('close', () => {
            resolver(dialogo.returnValue === 'si');
            dialogo.remove();
        });
        document.body.append(dialogo);
        dialogo.showModal();
    });
}

/** Deshabilita un formulario mientras corre una operación asíncrona. */
export async function ocupado(formulario, operacion) {
    const controles = formulario.querySelectorAll('input, button, select, textarea');
    controles.forEach((c) => { c.disabled = true; });
    formulario.setAttribute('aria-busy', 'true');
    try {
        return await operacion();
    } finally {
        controles.forEach((c) => { c.disabled = false; });
        formulario.removeAttribute('aria-busy');
    }
}

/** Muestra u oculta el texto de un campo de contraseña. */
export function conectarVerClave(boton, campo) {
    boton.addEventListener('click', () => {
        const visible = campo.type === 'text';
        campo.type = visible ? 'password' : 'text';
        boton.setAttribute('aria-pressed', String(!visible));
        boton.setAttribute('aria-label', visible ? 'Mostrar contraseña' : 'Ocultar contraseña');
        campo.focus();
    });
}

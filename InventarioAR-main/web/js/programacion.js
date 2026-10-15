// Diálogo de programación de frecuencias y canales (equivale a
// DialogoProgramacionModi de tabs/tab_inventario.py).
//
//   const prog = await editarProgramacion(api, programacionActual);
//   // prog === null si se canceló; si no: { cantidad_canales, canales: [...] }
//
// Cada canal: { nombre_config, numero_canal, frecuencia_tx, frecuencia_rx,
//               codificacion: 'SQL'|'DPL'|'TPL'|null, codigo_squelch }.
// Lo usa Inventario al editar un equipo; Ingreso lo va a reutilizar.

import { ApiError, SesionExpirada, ClavePendiente } from './api.js';
import { el, aviso, llenarSelect, dialogoFormulario } from './ui.js';

const CANALES_POR_DEFECTO = 16;
const MAX_CANALES = 999;
const CODIFICACIONES = [
    { valor: '', texto: 'Ninguna' },
    { valor: 'SQL', texto: 'SQL' },
    { valor: 'DPL', texto: 'DPL' },
    { valor: 'TPL', texto: 'TPL' },
];
// Mismo formato que acepta modiEquipo.php: DECIMAL(10,3) en MHz.
const FORMATO_FRECUENCIA = /^\d{1,7}([.,]\d{1,3})?$/;

/** Texto de resumen para mostrar junto al botón que abre el diálogo. */
export function resumenProgramacion(prog) {
    const cantidad = prog?.canales?.length || prog?.cantidad_canales || 0;
    if (!cantidad) return 'No configurado';
    const nombre = prog.canales?.[0]?.nombre_config || prog.nombre_plantilla;
    return `Configurado (${cantidad} canales)${nombre ? ` · Plantilla: ${nombre}` : ' · Sin plantilla'}`;
}

export function editarProgramacion(api, actual = null) {
    return new Promise((resolver) => {
        let resultado = null;

        // ── Controles superiores ──
        const cantidad = el('input', { type: 'number', id: 'prog-cantidad', min: 1, max: MAX_CANALES, step: 1 });
        const btnGenerar = el('button', { type: 'button', class: 'btn btn-secundario', onclick: () => generarFilas(Number(cantidad.value)) }, '🔄 Generar tabla');
        const selPlantilla = el('select', { id: 'prog-plantilla' });
        const btnCargar = el('button', { type: 'button', class: 'btn btn-secundario', onclick: cargarPlantilla }, '📥 Cargar plantilla');
        const nombre = el('input', { type: 'text', id: 'prog-nombre', maxlength: 150, autocomplete: 'off', placeholder: 'Nombre de la plantilla (opcional)' });

        const cuerpo = el('tbody');
        const tablaCanales = el('div', { class: 'tabla-contenedor tabla-canales' },
            el('table', { class: 'tabla' },
                el('thead', {}, el('tr', {},
                    el('th', { scope: 'col' }, 'Canal'),
                    el('th', { scope: 'col' }, 'TX (MHz)'),
                    el('th', { scope: 'col' }, 'RX (MHz)'),
                    el('th', { scope: 'col' }, 'Codificación'),
                    el('th', { scope: 'col' }, 'Código'))),
                cuerpo));

        /** @type {{tx, rx, cod, codigo, rxManual: boolean}[]} */
        let filas = [];

        const { modal } = dialogoFormulario('⚙️ Programación de frecuencias y canales', [
            el('div', { class: 'filtros' },
                el('div', { class: 'campo' }, el('label', { for: cantidad.id }, 'Cantidad de canales'), cantidad),
                btnGenerar),
            tablaCanales,
            el('div', { class: 'filtros' },
                el('div', { class: 'campo campo-ancho' }, el('label', { for: selPlantilla.id }, 'Plantilla guardada'), selPlantilla),
                btnCargar),
            el('label', { for: nombre.id }, 'Nombre de la plantilla'),
            nombre,
            el('p', { class: 'texto-suave' }, 'RX copia a TX mientras no lo edites. El código solo se usa con DPL o TPL.'),
        ], {
            textoAceptar: '✅ Aceptar y aplicar',
            ancho: 'ancho',
            alAceptar: aceptar,
        });

        // Al cerrar (aceptar, cancelar o Escape) se resuelve una sola vez.
        modal.addEventListener('close', () => resolver(resultado));

        // Enter dentro de la tabla pasa al campo siguiente en vez de enviar el formulario.
        tablaCanales.addEventListener('keydown', (evento) => {
            if (evento.key !== 'Enter' || evento.target.tagName !== 'INPUT') return;
            evento.preventDefault();
            const campos = [...tablaCanales.querySelectorAll('input:not(:disabled)')];
            campos[campos.indexOf(evento.target) + 1]?.focus();
        });
        cantidad.addEventListener('keydown', (evento) => {
            if (evento.key === 'Enter') {
                evento.preventDefault();
                generarFilas(Number(cantidad.value));
            }
        });

        cargarDatos(actual);
        llenarPlantillas();

        // ═══════════════ Tabla de canales ═══════════════
        function generarFilas(n) {
            if (!Number.isInteger(n) || n < 1 || n > MAX_CANALES) {
                aviso(`La cantidad de canales debe estar entre 1 y ${MAX_CANALES}.`, 'error');
                return;
            }
            // Conserva lo ya cargado en los canales que siguen existiendo.
            const previos = filas.map(leerFila);
            cantidad.value = n;
            filas = [];
            cuerpo.replaceChildren();
            for (let i = 0; i < n; i++) {
                filas.push(crearFila(i + 1, previos[i]));
            }
        }

        function crearFila(numero, datos = null) {
            const etiqueta = (campo) => `${campo} del canal ${numero}`;
            const tx = el('input', { type: 'text', inputmode: 'decimal', placeholder: '000.000', 'aria-label': etiqueta('TX'), autocomplete: 'off' });
            const rx = el('input', { type: 'text', inputmode: 'decimal', placeholder: '000.000', 'aria-label': etiqueta('RX'), autocomplete: 'off' });
            const cod = el('select', { 'aria-label': etiqueta('Codificación') });
            llenarSelect(cod, CODIFICACIONES);
            const codigo = el('input', { type: 'text', maxlength: 50, placeholder: 'Código', 'aria-label': etiqueta('Código'), autocomplete: 'off', disabled: true });
            const fila = { tx, rx, cod, codigo, rxManual: false };

            tx.addEventListener('input', () => {
                if (!fila.rxManual) rx.value = tx.value;
            });
            rx.addEventListener('input', () => {
                // Si se borra RX, vuelve a seguir a TX.
                fila.rxManual = rx.value !== '';
            });
            cod.addEventListener('change', () => {
                const conCodigo = cod.value === 'DPL' || cod.value === 'TPL';
                codigo.disabled = !conCodigo;
                if (conCodigo) codigo.focus();
                else codigo.value = '';
            });

            if (datos) {
                tx.value = datos.frecuencia_tx ?? '';
                rx.value = datos.frecuencia_rx ?? '';
                fila.rxManual = rx.value !== '' && rx.value !== tx.value;
                cod.value = CODIFICACIONES.some((c) => c.valor === datos.codificacion) ? datos.codificacion : '';
                codigo.disabled = !(cod.value === 'DPL' || cod.value === 'TPL');
                codigo.value = codigo.disabled ? '' : (datos.codigo_squelch ?? '');
            }

            cuerpo.append(el('tr', {},
                el('th', { scope: 'row' }, String(numero)),
                el('td', {}, tx), el('td', {}, rx), el('td', {}, cod), el('td', {}, codigo)));
            return fila;
        }

        function leerFila(fila, i) {
            // Se decide por la codificación y no por codigo.disabled: mientras se
            // valida, ocupado() deshabilita todos los campos del formulario.
            const conCodigo = fila.cod.value === 'DPL' || fila.cod.value === 'TPL';
            return {
                numero_canal: i + 1,
                frecuencia_tx: fila.tx.value.trim().replace(',', '.'),
                frecuencia_rx: fila.rx.value.trim().replace(',', '.'),
                codificacion: fila.cod.value || null,
                codigo_squelch: conCodigo ? fila.codigo.value.trim() : '',
            };
        }

        /** Vuelca una programación ({cantidad_canales, canales}) en la tabla. */
        function cargarDatos(prog) {
            const canales = prog?.canales ?? [];
            const n = Math.max(prog?.cantidad_canales || 0, ...canales.map((c) => Number(c.numero_canal) || 0))
                || CANALES_POR_DEFECTO;
            const porNumero = new Map(canales.map((c) => [Number(c.numero_canal), c]));
            filas = [];
            cuerpo.replaceChildren();
            cantidad.value = Math.min(n, MAX_CANALES);
            for (let i = 1; i <= Number(cantidad.value); i++) {
                filas.push(crearFila(i, porNumero.get(i)));
            }
            const nombrePrevio = canales[0]?.nombre_config ?? prog?.nombre_plantilla;
            if (nombrePrevio) nombre.value = nombrePrevio;
        }

        // ═══════════════ Plantillas ═══════════════
        async function llenarPlantillas() {
            try {
                const lista = await api.get('plantillas.php');
                llenarSelect(selPlantilla, [{ valor: '', texto: lista.length ? 'Elegí una plantilla…' : 'No hay plantillas guardadas' },
                    ...lista.map((p) => p.nombre_plantilla)]);
                selPlantilla.disabled = !lista.length;
                btnCargar.disabled = !lista.length;
            } catch (error) {
                manejarError(error, 'No se pudieron cargar las plantillas');
            }
        }

        async function cargarPlantilla() {
            const elegida = selPlantilla.value;
            if (!elegida) {
                aviso('Seleccioná una plantilla.', 'error');
                return;
            }
            btnCargar.disabled = true;
            try {
                const prog = await api.get('cargar_plantillas.php', { nombre_config: elegida });
                cargarDatos({ ...prog, nombre_plantilla: elegida });
                nombre.value = elegida;
                aviso(`Plantilla "${elegida}" cargada.`, 'exito');
            } catch (error) {
                manejarError(error, 'No se pudo cargar la plantilla');
            } finally {
                btnCargar.disabled = false;
            }
        }

        // ═══════════════ Aceptar ═══════════════
        function aceptar() {
            const canales = filas.map(leerFila);
            for (const c of canales) {
                for (const [campo, valor] of [['TX', c.frecuencia_tx], ['RX', c.frecuencia_rx]]) {
                    if (valor && !FORMATO_FRECUENCIA.test(valor)) {
                        aviso(`Canal ${c.numero_canal}: la frecuencia ${campo} "${valor}" no es válida (formato 000.000).`, 'error');
                        return false;
                    }
                }
                if ((c.codificacion === 'DPL' || c.codificacion === 'TPL') && !c.codigo_squelch) {
                    aviso(`Canal ${c.numero_canal}: falta el código ${c.codificacion}.`, 'error');
                    return false;
                }
            }
            if (!canales.some((c) => c.frecuencia_tx || c.frecuencia_rx)) {
                aviso('Cargá al menos una frecuencia.', 'error');
                return false;
            }
            const nombreConfig = nombre.value.trim();
            resultado = {
                cantidad_canales: canales.length,
                canales: canales.map((c) => ({ nombre_config: nombreConfig, ...c })),
            };
            return true;
        }
    });
}

function manejarError(error, contexto) {
    if (error instanceof SesionExpirada || error instanceof ClavePendiente) {
        return;
    }
    console.error(error);
    aviso(`${contexto}: ${error instanceof ApiError ? error.message : 'error inesperado'}`, 'error');
}

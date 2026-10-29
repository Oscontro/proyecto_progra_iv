// Pestaña Papelera (equivalente a tabs/tab_papelera.py).
//
// Lista equipos y vehículos dados de baja, con búsqueda y filtros, y permite
// ver el historial, restaurar y (solo administradores) eliminar
// definitivamente, con confirmación escribiendo ELIMINAR. Restaurar y
// eliminar funcionan con varias filas elegidas a la vez.
// Los vehículos siguen apareciendo aunque su pestaña se retiró de la migración:
// pueden restaurarse o eliminarse desde acá, como en el escritorio.

import { ApiError, SesionExpirada, ClavePendiente } from '../api.js';
import { el, aviso, confirmar, campoSelect, llenarSelect, dialogo } from '../ui.js';
import { tablaSeleccionable } from '../tabla_seleccionable.js';
import { verHistorialEquipo, verHistorialVehiculo } from '../historial.js';
import { enLote, listaLote, rotular } from '../lote.js';

const COLUMNAS = [
    { clave: 'tipo', titulo: 'Tipo' },
    { clave: 'marca', titulo: 'Marca' },
    { clave: 'modelo_equipo', titulo: 'Modelo' },
    { clave: 'numero_serie', titulo: 'N° Serie', mono: true },
    { clave: 'escala', titulo: 'Escala' },
    { clave: 'sector', titulo: 'Sector' },
    { clave: 'fecha_eliminacion', titulo: 'Fecha de eliminación' },
];

const TODOS = '';
const PALABRA_CONFIRMACION = 'ELIMINAR';
const TEXTO_RESTAURAR = '♻️ Restaurar';
const TEXTO_ELIMINAR = '🔥 Eliminar de la base de datos';

const esEquipo = (item) => item.origen === 'equipo';
const descripcion = (item) => (esEquipo(item)
    ? `Equipo N° de serie ${item.numero_serie} · Modelo ${item.modelo_equipo || '-'}`
    : `Vehículo ${item.numero_serie} · Escala ${item.escala || '-'}`);

export function montar(contenedor, { api, usuario }) {
    let completos = [];

    const buscar = el('input', { type: 'search', id: 'pap-buscar', placeholder: 'N° de serie…', autocomplete: 'off' });
    const estado = el('p', { class: 'estado-carga', role: 'status' });
    const fTipo = campoSelect('Tipo', [], { id: 'pap-tipo', alCambiar: aplicarFiltros });
    const fMarca = campoSelect('Marca', [], { id: 'pap-marca', alCambiar: aplicarFiltros });
    const fEscala = campoSelect('Escala', [], { id: 'pap-escala', alCambiar: aplicarFiltros });

    const btnHistorial = el('button', { type: 'button', class: 'btn btn-primario', disabled: true, onclick: () => verHistorial() }, '📜 Ver historial');
    const btnRestaurar = el('button', { type: 'button', class: 'btn btn-exito', disabled: true, onclick: restaurar }, TEXTO_RESTAURAR);
    const btnEliminar = usuario.es_admin
        ? el('button', { type: 'button', class: 'btn btn-peligro', disabled: true, onclick: eliminarDefinitivo }, TEXTO_ELIMINAR)
        : null;

    const tabla = tablaSeleccionable({
        columnas: COLUMNAS,
        etiqueta: 'Equipos y vehículos en la papelera',
        unidad: 'ítems',
        multiple: true,
        // El escritorio muestra "-" en los campos vacíos (los vehículos no tienen marca ni modelo).
        formato: (valor) => (valor === null || valor === undefined || valor === '' ? '-' : String(valor)),
        alSeleccionar: (fila, seleccionadas) => {
            btnHistorial.disabled = !fila;
            btnRestaurar.disabled = !seleccionadas.length;
            rotular(btnRestaurar, TEXTO_RESTAURAR, seleccionadas.length);
            if (btnEliminar) {
                btnEliminar.disabled = !seleccionadas.length;
                rotular(btnEliminar, TEXTO_ELIMINAR, seleccionadas.length);
            }
        },
        alActivar: verHistorial,
    });

    contenedor.append(
        el('div', { class: 'cabecera-pestana' }, el('h2', {}, 'Papelera'), estado),
        el('p', { class: 'texto-suave' }, 'Equipos y vehículos eliminados. Pueden restaurarse al inventario.'),
        el('div', { class: 'filtros' },
            el('div', { class: 'campo campo-ancho' }, el('label', { for: buscar.id }, 'Buscar'), buscar),
            el('button', { type: 'button', class: 'btn btn-secundario', onclick: limpiarFiltros }, 'Limpiar filtros'),
            el('button', { type: 'button', class: 'btn btn-secundario', onclick: () => cargar() }, '🔁 Actualizar')),
        el('div', { class: 'filtros' }, fTipo.nodo, fMarca.nodo, fEscala.nodo),
        tabla.contador,
        tabla.nodo,
        el('div', { class: 'acciones-pie' }, btnHistorial, btnRestaurar, btnEliminar));

    buscar.addEventListener('input', aplicarFiltros);

    // ═══════════════ Datos y filtros ═══════════════
    async function cargar() {
        estado.textContent = 'Cargando…';
        try {
            const [items, tipos, marcas, escalas] = await Promise.all([
                api.get('inventario_historial.php'),
                api.get('tipos.php'),
                api.get('marcas.php'),
                api.get('escalas.php'),
            ]);
            completos = items;
            llenarSelect(fTipo.select, conTodos(tipos.map((t) => t.tipo)));
            llenarSelect(fMarca.select, conTodos(marcas.map((m) => m.marca)));
            llenarSelect(fEscala.select, conTodos(escalas.map((e) => e.escala)));
            aplicarFiltros();
        } catch (error) {
            manejarError(error, 'No se pudo cargar la papelera');
        } finally {
            estado.textContent = '';
        }
    }

    function conTodos(valores) {
        return [{ valor: TODOS, texto: 'Todos' }, ...valores];
    }

    function limpiarFiltros() {
        buscar.value = '';
        for (const f of [fTipo, fMarca, fEscala]) {
            f.select.value = TODOS;
        }
        aplicarFiltros();
    }

    function aplicarFiltros() {
        const texto = buscar.value.trim().toUpperCase();
        const filtros = [['tipo', fTipo.select.value], ['marca', fMarca.select.value], ['escala', fEscala.select.value]]
            .filter(([, valor]) => valor !== TODOS);
        const filtrados = completos.filter((e) =>
            (!texto || String(e.numero_serie ?? '').toUpperCase().includes(texto))
            && filtros.every(([campo, valor]) => e[campo] === valor));
        tabla.mostrar(filtrados, completos.length);
    }

    // ═══════════════ Acciones ═══════════════
    async function verHistorial(item = tabla.seleccionada) {
        if (!item) {
            aviso('Debe seleccionar un ítem de la tabla.', 'error');
            return;
        }
        try {
            if (item.origen === 'equipo') {
                await verHistorialEquipo(api, { id_equipo: item.id_referencia, marca: item.marca,
                                                modelo_equipo: item.modelo_equipo, numero_serie: item.numero_serie });
            } else {
                await verHistorialVehiculo(api, { tipo: item.tipo, identificacion: item.numero_serie });
            }
        } catch (error) {
            manejarError(error, 'No se pudo cargar el historial');
        }
    }

    async function restaurar() {
        const items = tabla.seleccionadas;
        if (!items.length) return;
        const [item] = items;
        const ok = await confirmar('Confirmar restauración', items.length > 1
            ? `¿Restaurar los ${items.length} ítems seleccionados? Volverán a estar disponibles en el inventario.`
            : esEquipo(item)
                ? `¿Restaurar el equipo N° de serie ${item.numero_serie} (${item.modelo_equipo || 'sin modelo'})? Volverá a estar disponible en el inventario.`
                : `¿Restaurar el vehículo ${item.numero_serie} (escala ${item.escala || '-'})? Volverá a estar disponible.`,
            { aceptar: 'Restaurar' });
        if (!ok) return;

        let resultado;
        try {
            resultado = await enLote(items, (x) => (esEquipo(x)
                ? api.post('restaurar_equipo.php', { id_equipo: x.id_referencia })
                : api.post('restaurar_vehiculo.php', { id_vehiculo: x.id_referencia })));
        } catch (error) {
            manejarError(error, 'No se pudo restaurar');
            cargar();
            return;
        }
        informar(resultado, items.length === 1
            ? `${esEquipo(item) ? 'El equipo' : 'El vehículo'} ${item.numero_serie} fue restaurado correctamente.`
            : `Se restauraron ${resultado.hechos.length} ítems.`, 'No se pudo restaurar');
    }

    function eliminarDefinitivo() {
        const items = tabla.seleccionadas;
        if (!items.length || !usuario.es_admin) return;
        const [item] = items;

        // Confirmación reforzada: hay que escribir la palabra exacta (como en el escritorio).
        const campo = el('input', { type: 'text', id: 'pap-confirmar', autocomplete: 'off', spellcheck: 'false' });
        const boton = el('button', { type: 'button', class: 'btn btn-peligro', disabled: true },
            items.length > 1 ? `Eliminar ${items.length} definitivamente` : 'Eliminar definitivamente');
        const modal = dialogo('Eliminar definitivamente', [
            el('p', { class: 'mensaje-error' }, items.length > 1
                ? `Esta acción es IRREVERSIBLE. Se borran los ${items.length} ítems seleccionados, con su historial y sus datos asociados.`
                : 'Esta acción es IRREVERSIBLE. Se borran también su historial y sus datos asociados.'),
            items.length > 1 ? listaLote(items.map(descripcion)) : el('p', {}, descripcion(item)),
            el('label', { for: campo.id }, `Escribí ${PALABRA_CONFIRMACION} para confirmar`),
            campo,
        ], { acciones: [boton] });

        campo.addEventListener('input', () => {
            boton.disabled = campo.value !== PALABRA_CONFIRMACION;
        });
        campo.focus();

        boton.addEventListener('click', async () => {
            boton.disabled = true;
            let resultado;
            try {
                resultado = await enLote(items, (x) => api.post('eliminar_definitivo.php', {
                    origen: x.origen, id_referencia: x.id_referencia, numero_serie: x.numero_serie,
                }));
            } catch (error) {
                boton.disabled = campo.value !== PALABRA_CONFIRMACION;
                manejarError(error, 'No se pudo eliminar');
                return;
            }
            modal.querySelector('.modal-cerrar').click();
            informar(resultado, items.length === 1
                ? `${esEquipo(item) ? 'El equipo' : 'El vehículo'} ${item.numero_serie} fue eliminado permanentemente.`
                : `Se eliminaron permanentemente ${resultado.hechos.length} ítems.`, 'No se pudo eliminar');
        });
    }

    // Saca de la tabla lo que salió bien y avisa qué falló (con el motivo del servidor).
    function informar({ hechos, fallidos }, textoExito, contextoError) {
        quitar(...hechos);
        if (hechos.length) aviso(textoExito, 'exito');
        if (fallidos.length === 1) {
            aviso(`${contextoError} ${fallidos[0].item.numero_serie}: ${fallidos[0].mensaje}`, 'error');
        } else if (fallidos.length) {
            aviso(`${contextoError} ${fallidos.length} ítems: ${fallidos.map((f) => `${f.item.numero_serie} (${f.mensaje})`).join('; ')}`, 'error');
        }
    }

    function quitar(...items) {
        completos = completos.filter((x) => !items.includes(x));
        aplicarFiltros();
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

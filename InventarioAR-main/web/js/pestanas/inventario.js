// Pestaña Inventario - consulta (equivalente de solo lectura de tabs/tab_inventario.py).
//
// Incluye: búsqueda por N° de serie, filtros (tipo -> marca -> modelo en
// cascada, escala, sector, estado), tabla ordenable, historial del equipo,
// copiar fila y exportación a Excel de lo filtrado.
// Pendiente para una etapa posterior: editar, enviar a papelera y a reparación.

import { ApiError, SesionExpirada, ClavePendiente } from '../api.js';
import { el, aviso, textoCelda, campoSelect, llenarSelect } from '../ui.js';
import { exportarExcel, fechaArchivo } from '../excel.js';
import { tablaSeleccionable } from '../tabla_seleccionable.js';
import { verHistorialEquipo } from '../historial.js';

// Columnas visibles (el escritorio oculta potencia y nombre de plantilla).
const COLUMNAS = [
    { clave: 'tipo', titulo: 'Tipo' },
    { clave: 'marca', titulo: 'Marca' },
    { clave: 'modelo_equipo', titulo: 'Modelo' },
    { clave: 'numero_serie', titulo: 'N° Serie' },
    { clave: 'escala', titulo: 'Escala' },
    { clave: 'sector', titulo: 'Sector' },
    { clave: 'estado', titulo: 'Estado' },
    { clave: 'ult_observacion', titulo: 'Observaciones' },
];

const TODOS = '';

export function montar(contenedor, { api }) {
    let completos = [];
    let filtrados = [];
    let tipos = [];                     // [{id_tipo, tipo}]
    let marcas = [];                    // [{id_marca, marca}] del tipo elegido

    // ── Barra de búsqueda ──
    const buscar = el('input', { type: 'search', id: 'inv-buscar', placeholder: 'N° de serie…', autocomplete: 'off' });
    const estado = el('p', { class: 'estado-carga', role: 'status' });

    // ── Filtros ──
    const fTipo = campoSelect('Tipo', [], { id: 'inv-tipo', alCambiar: alCambiarTipo });
    const fMarca = campoSelect('Marca', [], { id: 'inv-marca', alCambiar: alCambiarMarca });
    const fModelo = campoSelect('Modelo', [], { id: 'inv-modelo', alCambiar: aplicarFiltros });
    const fEscala = campoSelect('Escala', [], { id: 'inv-escala', alCambiar: aplicarFiltros });
    const fSector = campoSelect('Sector', [], { id: 'inv-sector', alCambiar: aplicarFiltros });
    const fEstado = campoSelect('Estado', [], { id: 'inv-estado', alCambiar: aplicarFiltros });
    reiniciarCascada();

    // ── Tabla y acciones ──
    const btnHistorial = el('button', { type: 'button', class: 'btn btn-primario', disabled: true, onclick: () => verHistorial() }, '📜 Ver historial');
    const btnCopiar = el('button', { type: 'button', class: 'btn btn-secundario', disabled: true, onclick: copiarFila }, '📋 Copiar fila');
    const btnExcel = el('button', { type: 'button', class: 'btn btn-exito', onclick: generarExcel }, '📊 Generar Excel');

    const tabla = tablaSeleccionable({
        columnas: COLUMNAS,
        etiqueta: 'Equipos del inventario',
        unidad: 'equipos',
        alSeleccionar: (fila) => {
            btnHistorial.disabled = !fila;
            btnCopiar.disabled = !fila;
        },
        alActivar: verHistorial,
    });

    contenedor.append(
        el('div', { class: 'cabecera-pestana' }, el('h2', {}, 'Inventario'), estado),
        el('div', { class: 'filtros' },
            el('div', { class: 'campo campo-ancho' }, el('label', { for: buscar.id }, 'Buscar'), buscar),
            el('button', { type: 'button', class: 'btn btn-secundario', onclick: limpiarFiltros }, 'Limpiar filtros'),
            el('button', { type: 'button', class: 'btn btn-secundario', onclick: () => cargar() }, '🔁 Actualizar')),
        el('div', { class: 'filtros' }, fTipo.nodo, fMarca.nodo, fModelo.nodo, fEscala.nodo, fSector.nodo, fEstado.nodo),
        tabla.contador,
        tabla.nodo,
        el('div', { class: 'acciones-pie' },
            btnHistorial, btnCopiar, btnExcel,
            el('p', { class: 'texto-suave nota' },
                'Editar, enviar a papelera y enviar a reparación: por ahora desde el cliente de escritorio.')));

    buscar.addEventListener('input', aplicarFiltros);

    // ═══════════════ Datos ═══════════════
    async function cargar() {
        estado.textContent = 'Cargando…';
        try {
            const [equipos, listaTipos, escalas, sectores, estados] = await Promise.all([
                api.get('consultaInventario.php'),
                api.get('tipos.php'),
                api.get('escalas.php'),
                api.get('sectores.php'),
                api.get('estados.php'),
            ]);
            completos = equipos;
            tipos = listaTipos;
            llenarSelect(fTipo.select, opcionesConTodos(tipos.map((t) => t.tipo)));
            llenarSelect(fEscala.select, opcionesConTodos(escalas.map((e) => e.escala)));
            llenarSelect(fSector.select, opcionesConTodos(sectores.map((s) => s.sector)));
            llenarSelect(fEstado.select, opcionesConTodos(estados.map((e) => e.estado)));
            aplicarFiltros();
        } catch (error) {
            manejarError(error, 'No se pudo cargar el inventario');
        } finally {
            estado.textContent = '';
        }
    }

    // ═══════════════ Filtros ═══════════════
    function opcionesConTodos(valores) {
        return [{ valor: TODOS, texto: 'Todos' }, ...valores];
    }

    function reiniciarCascada() {
        marcas = [];
        llenarSelect(fMarca.select, [{ valor: TODOS, texto: 'Primero seleccione el tipo' }]);
        llenarSelect(fModelo.select, [{ valor: TODOS, texto: 'Primero seleccione la marca' }]);
        fMarca.select.disabled = true;
        fModelo.select.disabled = true;
    }

    async function alCambiarTipo() {
        reiniciarCascada();
        const tipo = tipos.find((t) => t.tipo === fTipo.select.value);
        if (tipo) {
            try {
                marcas = await api.get('marcas.php', { id_tipo: tipo.id_tipo });
                llenarSelect(fMarca.select, opcionesConTodos(marcas.map((m) => m.marca)));
                fMarca.select.disabled = false;
            } catch (error) {
                manejarError(error, 'No se pudieron cargar las marcas');
            }
        }
        aplicarFiltros();
    }

    async function alCambiarMarca() {
        llenarSelect(fModelo.select, [{ valor: TODOS, texto: 'Primero seleccione la marca' }]);
        fModelo.select.disabled = true;
        const tipo = tipos.find((t) => t.tipo === fTipo.select.value);
        const marca = marcas.find((m) => m.marca === fMarca.select.value);
        if (tipo && marca) {
            try {
                const modelos = await api.get('modelos.php', { id_marca: marca.id_marca, id_tipo: tipo.id_tipo });
                if (modelos.length) {
                    llenarSelect(fModelo.select, opcionesConTodos(modelos.map((m) => m.modelo_equipo)));
                    fModelo.select.disabled = false;
                } else {
                    llenarSelect(fModelo.select, [{ valor: TODOS, texto: 'Sin modelos para esta marca y tipo' }]);
                }
            } catch (error) {
                manejarError(error, 'No se pudieron cargar los modelos');
            }
        }
        aplicarFiltros();
    }

    function limpiarFiltros() {
        buscar.value = '';
        for (const f of [fTipo, fEscala, fSector, fEstado]) {
            f.select.value = TODOS;
        }
        reiniciarCascada();
        aplicarFiltros();
    }

    function aplicarFiltros() {
        const texto = buscar.value.trim().toUpperCase();
        const filtros = [
            ['tipo', fTipo.select.value],
            ['marca', fMarca.select.value],
            ['modelo_equipo', fModelo.select.value],
            ['escala', fEscala.select.value],
            ['sector', fSector.select.value],
            ['estado', fEstado.select.value],
        ].filter(([, valor]) => valor !== TODOS);

        filtrados = completos.filter((e) =>
            (!texto || String(e.numero_serie ?? '').toUpperCase().includes(texto))
            && filtros.every(([campo, valor]) => e[campo] === valor));

        tabla.mostrar(filtrados, completos.length);
        btnExcel.disabled = !filtrados.length;
    }

    // ═══════════════ Acciones ═══════════════
    async function verHistorial(equipo = tabla.seleccionada) {
        if (!equipo) {
            aviso('Debe seleccionar un equipo.', 'error');
            return;
        }
        try {
            await verHistorialEquipo(api, equipo);
        } catch (error) {
            manejarError(error, 'No se pudo cargar el historial');
        }
    }

    async function copiarFila() {
        const equipo = tabla.seleccionada;
        if (!equipo) return;
        const texto = COLUMNAS.map((c) => textoCelda(equipo[c.clave])).join('\t');
        try {
            await navigator.clipboard.writeText(texto);
            aviso('Fila copiada al portapapeles.', 'exito');
        } catch {
            aviso('No se pudo copiar al portapapeles.', 'error');
        }
    }

    async function generarExcel() {
        btnExcel.disabled = true;
        try {
            // Igual que el escritorio: se exportan los registros filtrados con todas sus columnas.
            await exportarExcel(filtrados, `inventario_${fechaArchivo()}.xlsx`, { margen: 3 });
            aviso(`Excel generado con ${filtrados.length} equipos.`, 'exito');
        } catch (error) {
            console.error(error);
            aviso('No se pudo generar el Excel.', 'error');
        } finally {
            btnExcel.disabled = !filtrados.length;
        }
    }

    function manejarError(error, contexto) {
        if (error instanceof SesionExpirada || error instanceof ClavePendiente) {
            return; // la aplicación ya cambió de vista
        }
        console.error(error);
        aviso(`${contexto}: ${error instanceof ApiError ? error.message : 'error inesperado'}`, 'error');
    }

    return { mostrar: cargar };
}

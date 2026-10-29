// Pestaña Inventario (equivalente a tabs/tab_inventario.py).
//
// Incluye: búsqueda por N° de serie, filtros (tipo -> marca -> modelo en
// cascada, escala, sector, estado), tabla ordenable, historial del equipo,
// copiar fila, exportación a Excel de lo filtrado, edición del equipo (con
// su programación de canales), envío a papelera y envío a reparación (taller).
// Copiar, enviar a papelera y enviar a reparación funcionan con varias filas
// elegidas a la vez; editar y ver historial, con una sola.

import { ApiError, SesionExpirada, ClavePendiente } from '../api.js';
import { el, aviso, textoCelda, campoSelect, llenarSelect, dialogoFormulario, campoSugerencias } from '../ui.js';
import { exportarExcel, fechaArchivo } from '../excel.js';
import { tablaSeleccionable } from '../tabla_seleccionable.js';
import { verHistorialEquipo } from '../historial.js';
import { editarProgramacion, resumenProgramacion } from '../programacion.js';
import { enLote, listaLote, rotular } from '../lote.js';

// Columnas visibles (el escritorio oculta potencia y nombre de plantilla).
const COLUMNAS = [
    { clave: 'tipo', titulo: 'Tipo' },
    { clave: 'marca', titulo: 'Marca' },
    { clave: 'modelo_equipo', titulo: 'Modelo' },
    { clave: 'numero_serie', titulo: 'N° Serie', mono: true },
    { clave: 'escala', titulo: 'Escala' },
    { clave: 'sector', titulo: 'Sector' },
    { clave: 'estado', titulo: 'Estado', pildora: true },
    { clave: 'ult_observacion', titulo: 'Observaciones' },
];

const TODOS = '';
const TEXTO_COPIAR = '📋 Copiar fila';
const TEXTO_PAPELERA = '🗑️ Enviar a papelera';
const TEXTO_REPARACION = '🔧 Enviar a reparación';

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
    const btnCopiar = el('button', { type: 'button', class: 'btn btn-secundario', disabled: true, onclick: copiarFila }, TEXTO_COPIAR);
    const btnExcel = el('button', { type: 'button', class: 'btn btn-exito', onclick: generarExcel }, '📊 Generar Excel');
    const btnEditar = el('button', { type: 'button', class: 'btn btn-primario', disabled: true, onclick: editar }, '📝 Editar');
    const btnPapelera = el('button', { type: 'button', class: 'btn btn-peligro boton-derecha', disabled: true, onclick: enviarAPapelera }, TEXTO_PAPELERA);
    const btnReparacion = el('button', { type: 'button', class: 'btn btn-advertencia', disabled: true, onclick: enviarAReparacion }, TEXTO_REPARACION);

    const tabla = tablaSeleccionable({
        columnas: COLUMNAS,
        etiqueta: 'Equipos del inventario',
        unidad: 'equipos',
        multiple: true,
        alSeleccionar: (fila, seleccionadas) => {
            btnEditar.disabled = btnHistorial.disabled = !fila;
            for (const [boton, texto] of [[btnCopiar, TEXTO_COPIAR], [btnPapelera, TEXTO_PAPELERA], [btnReparacion, TEXTO_REPARACION]]) {
                boton.disabled = !seleccionadas.length;
                rotular(boton, texto, seleccionadas.length);
            }
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
            btnEditar, btnHistorial, btnCopiar, btnExcel, btnPapelera, btnReparacion));

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
        const equipos = tabla.seleccionadas;
        if (!equipos.length) return;
        // Una línea por equipo, columnas separadas por tabulación (se pega bien en Excel).
        const texto = equipos.map((equipo) => COLUMNAS.map((c) => textoCelda(equipo[c.clave])).join('\t')).join('\n');
        try {
            await navigator.clipboard.writeText(texto);
            aviso(equipos.length > 1 ? `${equipos.length} filas copiadas al portapapeles.` : 'Fila copiada al portapapeles.', 'exito');
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

    // ── Editar ──
    async function editar() {
        const equipo = tabla.seleccionada;
        if (!equipo) return;
        btnEditar.disabled = true;
        let catalogos;
        try {
            const [escalas, sectores, estados, potencias, programacion] = await Promise.all([
                api.get('escalas.php'),
                api.get('sectores.php'),
                api.get('estados.php'),
                api.get('potencias.php'),
                api.get('cargar_programacion.php', { id_equipo: equipo.id_equipo }),
            ]);
            catalogos = { escalas, sectores, estados, potencias, programacion };
        } catch (error) {
            manejarError(error, 'No se pudieron cargar los datos del equipo');
            return;
        } finally {
            btnEditar.disabled = !tabla.seleccionada;
        }
        abrirEdicion(equipo, catalogos);
    }

    function abrirEdicion(equipo, { escalas, sectores, estados, potencias, programacion }) {
        // null = no se tocó la programación: se conserva la que tiene el equipo.
        let programacionNueva = null;
        let marcasTipo = [];   // marcas del tipo elegido en el formulario

        const selTipo = el('select', { id: 'ed-tipo', required: true });
        const selMarca = el('select', { id: 'ed-marca', required: true });
        const selModelo = el('select', { id: 'ed-modelo', required: true });
        const serie = el('input', { type: 'text', id: 'ed-serie', value: equipo.numero_serie, readonly: true });
        const selEscala = el('select', { id: 'ed-escala', required: true });
        // Sector y estado son texto libre en la base: se sugieren los existentes.
        const sugSector = campoSugerencias({ id: 'ed-sector', maxlength: 100, required: true });
        const sugEstado = campoSugerencias({ id: 'ed-estado', maxlength: 100, required: true });
        const sector = sugSector.input;
        const estadoEq = sugEstado.input;
        sugSector.sugerir(sectores.map((s) => s.sector));
        sugEstado.sugerir(estados.map((e) => e.estado));
        const selPotencia = el('select', { id: 'ed-potencia' });
        const observaciones = el('textarea', { id: 'ed-observaciones', maxlength: 255, placeholder: 'Observaciones adicionales…' });
        const resumenProg = el('span', { class: 'texto-suave' }, resumenProgramacion(programacion));
        const btnProg = el('button', { type: 'button', class: 'btn btn-secundario', onclick: configurarCanales }, '⚙️ Configurar canales');

        llenarSelect(selEscala, conActual(escalas.map((e) => e.escala), equipo.escala));
        llenarSelect(selPotencia, [{ valor: '', texto: 'Sin especificar' }, ...conActual(potencias.map((p) => p.potencia), equipo.potencia)]);
        selEscala.value = equipo.escala;
        selPotencia.value = equipo.potencia ?? '';
        sector.value = equipo.sector ?? '';
        estadoEq.value = equipo.estado ?? '';
        observaciones.value = equipo.ult_observacion ?? '';

        const campo = (control, etiqueta, nodo = control) => el('div', { class: 'campo' }, el('label', { for: control.id }, etiqueta), nodo);

        dialogoFormulario(`Modificar equipo · ${equipo.numero_serie}`, [
            el('div', { class: 'rejilla-form' },
                campo(selTipo, 'Tipo'), campo(selMarca, 'Marca'), campo(selModelo, 'Modelo'),
                campo(serie, 'N° de serie'), campo(selEscala, 'Escala'), campo(selPotencia, 'Potencia'),
                campo(sector, 'Sector', sugSector.nodo), campo(estadoEq, 'Estado', sugEstado.nodo)),
            el('label', {}, 'Programación'),
            el('div', { class: 'fila-programacion' }, btnProg, resumenProg),
            el('label', { for: observaciones.id }, 'Observaciones'),
            observaciones,
        ], {
            textoAceptar: '💾 Modificar equipo',
            ancho: 'medio',
            alAceptar: guardar,
        });

        selTipo.addEventListener('change', () => cascadaMarcas());
        selMarca.addEventListener('change', () => cascadaModelos());
        cascadaInicial();

        async function cascadaInicial() {
            llenarSelect(selTipo, conActual(tipos.map((t) => t.tipo), equipo.tipo));
            selTipo.value = equipo.tipo;
            await cascadaMarcas(equipo.marca, equipo.modelo_equipo);
        }

        async function cascadaMarcas(marcaElegida = null, modeloElegido = null) {
            llenarSelect(selMarca, [{ valor: '', texto: 'Cargando…' }]);
            llenarSelect(selModelo, [{ valor: '', texto: 'Primero seleccione la marca' }]);
            selMarca.disabled = selModelo.disabled = true;
            const tipo = tipos.find((t) => t.tipo === selTipo.value);
            if (!tipo) return;
            try {
                marcasTipo = await api.get('marcas.php', { id_tipo: tipo.id_tipo });
            } catch (error) {
                manejarError(error, 'No se pudieron cargar las marcas');
                return;
            }
            llenarSelect(selMarca, [{ valor: '', texto: 'Seleccione la marca' }, ...marcasTipo.map((m) => m.marca)]);
            selMarca.disabled = false;
            if (marcaElegida && marcasTipo.some((m) => m.marca === marcaElegida)) {
                selMarca.value = marcaElegida;
                await cascadaModelos(modeloElegido);
            }
        }

        async function cascadaModelos(modeloElegido = null) {
            llenarSelect(selModelo, [{ valor: '', texto: 'Primero seleccione la marca' }]);
            selModelo.disabled = true;
            const tipo = tipos.find((t) => t.tipo === selTipo.value);
            const marca = marcasTipo.find((m) => m.marca === selMarca.value);
            if (!tipo || !marca) return;
            let modelos;
            try {
                modelos = await api.get('modelos.php', { id_marca: marca.id_marca, id_tipo: tipo.id_tipo });
            } catch (error) {
                manejarError(error, 'No se pudieron cargar los modelos');
                return;
            }
            if (!modelos.length) {
                llenarSelect(selModelo, [{ valor: '', texto: 'Sin modelos para esta marca y tipo' }]);
                return;
            }
            llenarSelect(selModelo, [{ valor: '', texto: 'Seleccione el modelo' }, ...modelos.map((m) => m.modelo_equipo)]);
            selModelo.disabled = false;
            if (modeloElegido && modelos.some((m) => m.modelo_equipo === modeloElegido)) {
                selModelo.value = modeloElegido;
            }
        }

        async function configurarCanales() {
            const prog = await editarProgramacion(api, programacionNueva ?? programacion);
            if (prog) {
                programacionNueva = prog;
                resumenProg.textContent = `${resumenProgramacion(prog)} · se guarda al modificar el equipo`;
            }
        }

        async function guardar() {
            const faltantes = [[selTipo, 'el tipo'], [selMarca, 'la marca'], [selModelo, 'el modelo'],
                [selEscala, 'la escala'], [sector, 'el sector'], [estadoEq, 'el estado']]
                .filter(([control]) => !control.value.trim());
            if (faltantes.length) {
                aviso(`Falta completar ${faltantes.map(([, nombre]) => nombre).join(', ')}.`, 'error');
                faltantes[0][0].focus();
                return false;
            }
            try {
                const respuesta = await api.post('modiEquipo.php', {
                    equipo: {
                        id_equipo: equipo.id_equipo,
                        numero_serie: equipo.numero_serie,
                        tipo: selTipo.value,
                        marca: selMarca.value,
                        modelo_equipo: selModelo.value,
                        escala: selEscala.value,
                        sector: sector.value.trim(),
                        estado: estadoEq.value.trim(),
                        valor_potencia: selPotencia.value,
                        observaciones: observaciones.value.trim(),
                    },
                    frecuencias: programacionNueva ?? { cantidad_canales: 0, canales: [] },
                });
                aviso(respuesta?.cambios === false
                    ? 'No hubo cambios que aplicar.'
                    : `Equipo ${equipo.numero_serie} modificado correctamente.`, respuesta?.cambios === false ? 'info' : 'exito');
            } catch (error) {
                manejarError(error, 'No se pudo modificar el equipo');
                return false;
            }
            cargar();
            return true;
        }
    }

    /** Opciones del catálogo más el valor actual del equipo si no figura (para no perderlo). */
    function conActual(valores, actual) {
        return actual && !valores.includes(actual) ? [actual, ...valores] : valores;
    }

    // ── Enviar a papelera ──
    function enviarAPapelera() {
        const equipos = tabla.seleccionadas;
        if (!equipos.length) return;
        const varios = equipos.length > 1;
        const motivo = el('textarea', { id: 'pap-motivo', maxlength: 500, placeholder: 'Motivo de la baja…' });
        const { form } = dialogoFormulario('Enviar a papelera', [
            fichaEquipos(equipos),
            el('p', {}, varios
                ? `¿Enviar estos ${equipos.length} equipos a la papelera? Se podrán restaurar desde la pestaña Papelera.`
                : '¿Enviar este equipo a la papelera? Se podrá restaurar desde la pestaña Papelera.'),
            el('label', { for: motivo.id }, varios ? 'Motivo (el mismo para todos)' : 'Motivo'),
            motivo,
        ], {
            textoAceptar: varios ? `🗑️ Enviar ${equipos.length} a papelera` : TEXTO_PAPELERA,
            ancho: 'medio',
            alAceptar: () => procesarLote(equipos,
                (equipo) => api.post('enviar_papelera.php', { id_equipo: equipo.id_equipo, motivo: motivo.value.trim() }),
                (n) => (varios ? `${n} equipos enviados a la papelera.` : `Equipo ${equipos[0].numero_serie} enviado a la papelera.`),
                'No se pudo enviar a la papelera'),
        });
        form.querySelector('[type="submit"]').className = 'btn btn-peligro';
        motivo.focus();
    }

    // ── Enviar a reparación (taller) ──
    async function enviarAReparacion() {
        const equipos = tabla.seleccionadas;
        if (!equipos.length) return;
        const varios = equipos.length > 1;
        let talleres;
        try {
            talleres = await api.get('talleres.php');
        } catch (error) {
            manejarError(error, 'No se pudieron cargar los talleres');
            return;
        }
        if (!talleres.length) {
            aviso('No hay talleres cargados.', 'error');
            return;
        }
        const selTaller = el('select', { id: 'rep-taller' });
        llenarSelect(selTaller, talleres.map((t) => ({ valor: t.id_taller, texto: t.taller })));
        const motivo = el('textarea', { id: 'rep-motivo', maxlength: 500, placeholder: 'Falla o motivo del envío…' });
        dialogoFormulario('Enviar a reparación', [
            fichaEquipos(equipos),
            el('label', { for: selTaller.id }, 'Taller'),
            selTaller,
            el('label', { for: motivo.id }, varios ? 'Observaciones (las mismas para todos)' : 'Observaciones'),
            motivo,
            el('p', { class: 'texto-suave' }, varios
                ? 'Los equipos salen del inventario y aparecen en Taller como "No ingresado" hasta que el taller los reciba.'
                : 'El equipo sale del inventario y aparece en Taller como "No ingresado" hasta que el taller lo reciba.'),
        ], {
            textoAceptar: varios ? `🔧 Enviar ${equipos.length} a taller` : '🔧 Enviar a taller',
            ancho: 'medio',
            alAceptar: () => {
                const taller = selTaller.selectedOptions[0]?.textContent ?? '';
                return procesarLote(equipos,
                    (equipo) => api.post('enviar_a_taller.php', {
                        id_equipo: equipo.id_equipo,
                        id_taller: Number(selTaller.value),
                        observaciones: motivo.value.trim(),
                    }),
                    (n) => (varios ? `${n} equipos enviados a ${taller}.` : `Equipo ${equipos[0].numero_serie} enviado a ${taller}.`),
                    'No se pudo enviar a taller');
            },
        });
        motivo.focus();
    }

    // Manda cada equipo al endpoint y avisa el resultado. Si alguno falló, el
    // diálogo se cierra igual (los que salieron bien ya no se pueden repetir)
    // y el aviso dice cuáles fallaron y por qué.
    async function procesarLote(equipos, accion, textoExito, contextoError) {
        let resultado;
        try {
            resultado = await enLote(equipos, accion);
        } catch (error) {
            manejarError(error, contextoError);
            cargar();
            return false;
        }
        const { hechos, fallidos } = resultado;
        if (!hechos.length) {
            // No salió ninguno: el diálogo queda abierto para corregir y reintentar.
            aviso(`${contextoError}: ${fallidos.map((f) => (equipos.length > 1 ? `${f.item.numero_serie} (${f.mensaje})` : f.mensaje)).join('; ')}`, 'error');
            return false;
        }
        aviso(textoExito(hechos.length), 'exito');
        if (fallidos.length) {
            aviso(`${contextoError} ${fallidos.length === 1 ? 'el equipo' : `${fallidos.length} equipos`}: ${fallidos.map((f) => `${f.item.numero_serie} (${f.mensaje})`).join('; ')}`, 'error');
        }
        cargar();
        return true;
    }

    // Un equipo: su ficha completa. Varios: la lista de números de serie.
    function fichaEquipos(equipos) {
        return equipos.length === 1
            ? fichaEquipo(equipos[0])
            : listaLote(equipos.map((e) => `${textoCelda(e.numero_serie)} · ${textoCelda(e.marca)} ${textoCelda(e.modelo_equipo)} · ${textoCelda(e.estado)}`));
    }

    function fichaEquipo(equipo) {
        const dato = (t, v) => el('div', { class: 'ficha-par' }, el('dt', {}, t), el('dd', {}, textoCelda(v) || '-'));
        return el('dl', { class: 'ficha' },
            dato('Tipo:', equipo.tipo), dato('Marca:', equipo.marca), dato('Modelo:', equipo.modelo_equipo),
            dato('N° de serie:', equipo.numero_serie), dato('Sector:', equipo.sector), dato('Estado:', equipo.estado));
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

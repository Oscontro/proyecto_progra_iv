// Pestaña Ingreso de Equipos (equivalente a tabs/tab_ingreso_equipos.py).
//
// Alta de un equipo: tipo, marca, modelo, N° de serie, escala, sector,
// estado, potencia, programación de canales y observaciones, con la imagen
// del modelo. También importa equipos desde un Excel.
//
// Los campos de catálogo se eligen de la lista o se escriben. Si un tipo,
// marca, modelo o escala no existe, alta_equipo.php responde 409
// CATALOGO_NUEVO con la lista de valores a crear y se pide confirmación
// antes de crearlos (decisión de la migración: nada se crea sin avisar).

import { ApiError, SesionExpirada, ClavePendiente } from '../api.js';
import { el, aviso, confirmar, dialogo, campoSugerencias } from '../ui.js';
import { leerExcel, exportarExcel, fechaArchivo } from '../excel.js';
import { editarProgramacion, resumenProgramacion } from '../programacion.js';

const IMAGENES = new URL('../resources/images/', document.baseURI);

// Columnas que se aceptan en el Excel (encabezado normalizado -> campo).
const COLUMNAS_EXCEL = {
    tipo: 'tipo', marca: 'marca', modelo: 'modelo',
    nserie: 'numero_serie', numerodeserie: 'numero_serie', numeroserie: 'numero_serie', serie: 'numero_serie',
    escala: 'escala', sector: 'sector', estado: 'estado', potencia: 'potencia',
    observaciones: 'ult_observacion', observacion: 'ult_observacion',
};
const OBLIGATORIAS_EXCEL = ['tipo', 'marca', 'modelo', 'numero_serie', 'escala', 'sector', 'estado'];
// Correcciones que aplica el escritorio al importar (después de pasar a Título).
const CORRECCIONES_EXCEL = {
    'Base Vhf Fm': 'Base VHF FM', 'Vhf Aeronautico': 'VHF Aeronautico', 'Lineal Hf': 'Lineal HF',
    'Receptor Hf': 'Receptor HF', 'Excitador Hf': 'Excitador HF', 'Exitador Hf': 'Excitador HF',
    'Icom': 'ICOM', 'Cubic': 'CUBIC', 'Glidepath': 'GLIDEPATH',
};

export function montar(contenedor, { api }) {
    let tipos = [];          // [{id_tipo, tipo}]
    let marcasTipo = [];     // [{id_marca, marca}] del tipo elegido
    let programacion = null; // null = sin programación

    // ── Campos (texto con sugerencias: se elige o se escribe) ──
    const combos = {};
    const campo = (id, etiqueta, atributos = {}) => {
        combos[id] = campoSugerencias({ id, ...atributos });
        return { input: combos[id].input, nodo: el('div', { class: 'campo' }, el('label', { for: id }, etiqueta), combos[id].nodo) };
    };
    const fTipo = campo('ing-tipo', 'Tipo de equipo', { maxlength: 100 });
    const fMarca = campo('ing-marca', 'Marca', { maxlength: 100 });
    const fModelo = campo('ing-modelo', 'Modelo', { maxlength: 150 });
    const fEscala = campo('ing-escala', 'Escala', { maxlength: 3, class: 'mayusculas' });
    const fSector = campo('ing-sector', 'Sector', { maxlength: 100 });
    const fEstado = campo('ing-estado', 'Estado', { maxlength: 100 });
    const fPotencia = campo('ing-potencia', 'Potencia', { maxlength: 50 });
    const serie = el('input', { type: 'text', id: 'ing-serie', maxlength: 100, autocomplete: 'off', spellcheck: 'false', class: 'mayusculas campo-serie' });
    const observaciones = el('textarea', { id: 'ing-observaciones', maxlength: 255, placeholder: 'Observaciones adicionales…' });
    const resumenProg = el('span', { class: 'texto-suave' }, resumenProgramacion(null));

    const imagen = el('img', { class: 'imagen-modelo', alt: '', hidden: true });
    const sinImagen = el('p', { class: 'sin-imagen' }, '📷 Sin imagen disponible');

    const archivo = el('input', { type: 'file', accept: '.xlsx,.xls', hidden: true, onchange: () => importarExcel(archivo.files[0]) });
    const btnGuardar = el('button', { type: 'submit', class: 'btn btn-exito' }, '💾 Guardar equipo');

    const form = el('form', { class: 'formulario ingreso', novalidate: true },
        el('div', { class: 'ingreso-columnas' },
            el('div', { class: 'panel-ingreso' },
                el('div', { class: 'rejilla-form' },
                    fTipo.nodo, fMarca.nodo, fModelo.nodo,
                    el('div', { class: 'campo' }, el('label', { for: serie.id }, 'N° de serie'), serie),
                    fEscala.nodo, fPotencia.nodo, fSector.nodo, fEstado.nodo),
                el('label', {}, 'Programación'),
                el('div', { class: 'fila-programacion' },
                    el('button', { type: 'button', class: 'btn btn-secundario', onclick: configurarCanales }, '⚙️ Configurar canales'),
                    resumenProg),
                el('label', { for: observaciones.id }, 'Observaciones'),
                observaciones),
            el('div', { class: 'panel-ingreso panel-imagen', 'aria-live': 'polite' },
                el('h3', {}, 'Imagen del modelo'), imagen, sinImagen)),
        el('div', { class: 'acciones-pie' },
            el('button', { type: 'button', class: 'btn btn-secundario', onclick: () => archivo.click() }, '📊 Importar desde Excel'),
            archivo,
            el('button', { type: 'button', class: 'btn btn-secundario boton-derecha', onclick: () => limpiar(true) }, 'Limpiar'),
            btnGuardar));

    contenedor.append(
        el('div', { class: 'cabecera-pestana' }, el('h2', {}, 'Ingreso de equipos')),
        el('p', { class: 'texto-suave' },
            'Elegí de las listas o escribí un valor nuevo: si no existe en el catálogo, se te pide confirmación antes de crearlo.'),
        form);

    // ── Eventos ──
    fTipo.input.addEventListener('change', alCambiarTipo);
    fMarca.input.addEventListener('change', alCambiarMarca);
    fModelo.input.addEventListener('change', mostrarImagen);
    // N° de serie y escala en mayúsculas y sin espacios mientras se escribe (como el escritorio).
    serie.addEventListener('input', () => normalizarMientrasEscribe(serie, (t) => t.toUpperCase().replace(/\s+/g, '')));
    fEscala.input.addEventListener('input', () => normalizarMientrasEscribe(fEscala.input, (t) => t.toUpperCase()));
    imagen.addEventListener('error', () => { imagen.hidden = true; sinImagen.hidden = false; });
    imagen.addEventListener('load', () => { imagen.hidden = false; sinImagen.hidden = true; });
    form.addEventListener('submit', (evento) => {
        evento.preventDefault();
        guardar();
    });

    // ═══════════════ Catálogos ═══════════════
    async function cargar() {
        try {
            const [listaTipos, escalas, sectores, estados, potencias] = await Promise.all([
                api.get('tipos.php'), api.get('escalas.php'), api.get('sectores.php'),
                api.get('estados.php'), api.get('potencias.php'),
            ]);
            tipos = listaTipos;
            sugerir('ing-tipo', tipos.map((t) => t.tipo));
            sugerir('ing-escala', escalas.map((e) => e.escala));
            sugerir('ing-sector', sectores.map((s) => s.sector));
            sugerir('ing-estado', estados.map((e) => e.estado));
            sugerir('ing-potencia', potencias.map((p) => p.potencia));
            await alCambiarTipo();
        } catch (error) {
            manejarError(error, 'No se pudieron cargar los catálogos');
        }
    }

    function sugerir(id, valores) {
        combos[id].sugerir(valores);
    }

    const mismoTexto = (a, b) => a.localeCompare(b, 'es', { sensitivity: 'base' }) === 0;

    async function alCambiarTipo() {
        const tipo = tipos.find((t) => mismoTexto(t.tipo, fTipo.input.value.trim()));
        try {
            // Tipo existente: sus marcas. Tipo nuevo o vacío: todas las marcas.
            marcasTipo = await api.get('marcas.php', tipo ? { id_tipo: tipo.id_tipo } : null);
        } catch (error) {
            manejarError(error, 'No se pudieron cargar las marcas');
            marcasTipo = [];
        }
        sugerir('ing-marca', marcasTipo.map((m) => m.marca));
        await alCambiarMarca();
    }

    async function alCambiarMarca() {
        const tipo = tipos.find((t) => mismoTexto(t.tipo, fTipo.input.value.trim()));
        const marca = marcasTipo.find((m) => mismoTexto(m.marca, fMarca.input.value.trim()));
        let modelos = [];
        if (tipo && marca) {
            try {
                modelos = await api.get('modelos.php', { id_marca: marca.id_marca, id_tipo: tipo.id_tipo });
            } catch (error) {
                manejarError(error, 'No se pudieron cargar los modelos');
            }
        }
        sugerir('ing-modelo', modelos.map((m) => m.modelo_equipo));
        mostrarImagen();
    }

    async function mostrarImagen() {
        const modelo = fModelo.input.value.trim();
        imagen.hidden = true;
        sinImagen.hidden = false;
        sinImagen.textContent = modelo ? `📷 ${modelo}: sin imagen disponible` : '📷 Sin imagen disponible';
        imagen.alt = modelo ? `Imagen del modelo ${modelo}` : '';
        if (!modelo) return;
        try {
            const archivoImagen = await api.get('imagen.php', { imagen_modelo: modelo });
            if (typeof archivoImagen === 'string' && archivoImagen && fModelo.input.value.trim() === modelo) {
                imagen.src = new URL(encodeURIComponent(archivoImagen), IMAGENES).href;
            }
        } catch (error) {
            // Sin imagen (404) no es un error para el usuario; la sesión vencida sí la maneja la app.
            if (!(error instanceof ApiError) || error.status >= 500) console.error(error);
        }
    }

    // ═══════════════ Programación ═══════════════
    async function configurarCanales() {
        const prog = await editarProgramacion(api, programacion);
        if (prog) {
            programacion = prog;
            resumenProg.textContent = resumenProgramacion(prog);
        }
    }

    // ═══════════════ Guardar ═══════════════
    function leerFormulario() {
        return {
            tipo: fTipo.input.value.trim(),
            marca: fMarca.input.value.trim(),
            modelo: fModelo.input.value.trim(),
            numero_serie: serie.value.trim(),
            escala: fEscala.input.value.trim(),
            sector: fSector.input.value.trim(),
            estado: fEstado.input.value.trim(),
            potencia: fPotencia.input.value.trim(),
            ult_observacion: observaciones.value.trim(),
        };
    }

    async function guardar() {
        const equipo = leerFormulario();
        const faltantes = [[fTipo.input, 'el tipo', equipo.tipo], [fMarca.input, 'la marca', equipo.marca],
            [fModelo.input, 'el modelo', equipo.modelo], [serie, 'el N° de serie', equipo.numero_serie],
            [fEscala.input, 'la escala', equipo.escala], [fSector.input, 'el sector', equipo.sector],
            [fEstado.input, 'el estado', equipo.estado]].filter(([, , valor]) => !valor);
        if (faltantes.length) {
            aviso(`Falta completar ${faltantes.map(([, nombre]) => nombre).join(', ')}.`, 'error');
            faltantes[0][0].focus();
            return;
        }
        btnGuardar.disabled = true;
        try {
            const datos = { equipo, frecuencias: programacion ?? { canales: [] } };
            let resultado;
            try {
                resultado = await api.post('alta_equipo.php', { ...datos, crear_nuevos: false });
            } catch (error) {
                if (!(error instanceof ApiError) || error.code !== 'CATALOGO_NUEVO') throw error;
                const ok = await confirmar('Valores nuevos en los catálogos',
                    `No existen todavía y se van a crear: ${describirNuevos(error.datos?.nuevos ?? [])}. ¿Continuar?`,
                    { aceptar: 'Crear y guardar' });
                if (!ok) return;
                resultado = await api.post('alta_equipo.php', { ...datos, crear_nuevos: true });
            }
            aviso(`Equipo ${resultado?.numero_serie ?? equipo.numero_serie} guardado correctamente.`, 'exito');
            limpiar(false);
            if (resultado?.nuevos?.length) cargar();   // que los valores nuevos aparezcan en las listas
        } catch (error) {
            manejarError(error, 'No se pudo guardar el equipo');
        } finally {
            btnGuardar.disabled = false;
        }
    }

    /**
     * todo = true: vacía todo el formulario (botón Limpiar).
     * todo = false: después de guardar se conservan tipo, marca, modelo,
     * escala, sector, estado y potencia para cargar seguido varios equipos iguales.
     */
    function limpiar(todo) {
        serie.value = '';
        observaciones.value = '';
        programacion = null;
        resumenProg.textContent = resumenProgramacion(null);
        if (todo) {
            for (const f of [fTipo, fMarca, fModelo, fEscala, fSector, fEstado, fPotencia]) {
                f.input.value = '';
            }
            alCambiarTipo();
            fTipo.input.focus();
        } else {
            serie.focus();
        }
    }

    // ═══════════════ Importar desde Excel ═══════════════
    async function importarExcel(file) {
        archivo.value = '';   // permite volver a elegir el mismo archivo
        if (!file) return;
        let filas;
        try {
            filas = prepararFilas(await leerExcel(file));
        } catch (error) {
            console.error(error);
            aviso(error.message || 'No se pudo leer el archivo Excel.', 'error');
            return;
        }
        if (!filas.length) {
            aviso('El archivo no tiene filas con datos.', 'error');
            return;
        }
        abrirImportacion(file.name, filas);
    }

    function prepararFilas(registros) {
        if (!registros.length) return [];
        const mapa = {};
        for (const encabezado of Object.keys(registros[0])) {
            const clave = encabezado.normalize('NFD').replace(/[̀-ͯ]/g, '').toLowerCase().replace(/[^a-z0-9]/g, '');
            if (COLUMNAS_EXCEL[clave] && !Object.values(mapa).includes(COLUMNAS_EXCEL[clave])) {
                mapa[encabezado] = COLUMNAS_EXCEL[clave];
            }
        }
        const faltan = OBLIGATORIAS_EXCEL.filter((c) => !Object.values(mapa).includes(c));
        if (faltan.length) {
            throw new Error(`Al Excel le faltan columnas: ${faltan.join(', ')}. Se esperan Tipo, Marca, Modelo, N° Serie, Escala, Sector, Estado (y opcionales Potencia, Observaciones).`);
        }
        return registros
            .map((r) => {
                const fila = {};
                for (const [encabezado, campoDestino] of Object.entries(mapa)) {
                    fila[campoDestino] = String(r[encabezado] ?? '').trim();
                }
                // Misma limpieza que el escritorio: Título y correcciones de nombres conocidos.
                for (const c of ['tipo', 'marca', 'sector', 'estado']) {
                    const titulo = aTitulo(fila[c]);
                    fila[c] = CORRECCIONES_EXCEL[titulo] ?? titulo;
                }
                fila.escala = fila.escala.toUpperCase();
                fila.numero_serie = fila.numero_serie.toUpperCase().replace(/\s+/g, '');
                return fila;
            })
            .filter((f) => Object.values(f).some(Boolean));
    }

    function abrirImportacion(nombreArchivo, filas) {
        const estados = filas.map(() => ({ estado: 'pendiente', texto: 'Pendiente', nuevos: [] }));
        let cancelado = false;
        let ocupado = false;

        const progreso = el('p', { class: 'texto-suave', role: 'status' });
        const resumen = el('div', { class: 'resumen-importacion' });
        const cuerpo = el('tbody');
        const celdasEstado = filas.map((f, i) => {
            const celda = el('td', {}, 'Pendiente');
            cuerpo.append(el('tr', {},
                el('td', {}, String(i + 1)), el('td', {}, f.tipo), el('td', {}, f.marca), el('td', {}, f.modelo),
                el('td', {}, f.numero_serie), el('td', {}, f.escala), el('td', {}, f.sector), el('td', {}, f.estado),
                celda));
            return celda;
        });
        const btnInsertar = el('button', { type: 'button', class: 'btn btn-exito', disabled: true, onclick: insertar }, 'Insertar registros');
        const btnErrores = el('button', { type: 'button', class: 'btn btn-secundario', hidden: true, onclick: descargarErrores }, '📥 Descargar errores');

        const modal = dialogo(`Importar equipos · ${nombreArchivo}`, [
            progreso,
            resumen,
            el('div', { class: 'tabla-contenedor tabla-alta' },
                el('table', { class: 'tabla' },
                    el('thead', {}, el('tr', {}, ['#', 'Tipo', 'Marca', 'Modelo', 'N° Serie', 'Escala', 'Sector', 'Estado', 'Resultado']
                        .map((t) => el('th', { scope: 'col' }, t)))),
                    cuerpo)),
        ], { acciones: [btnErrores, btnInsertar], ancho: 'ancho' });
        modal.addEventListener('close', () => { cancelado = true; });

        revisar();

        function marcar(i, estado, texto, nuevos = []) {
            estados[i] = { estado, texto, nuevos };
            celdasEstado[i].textContent = texto;
            celdasEstado[i].className = `resultado-${estado}`;
        }

        // 1) Revisión sin guardar: duplicados en el archivo y validación de cada fila en el servidor.
        async function revisar() {
            ocupado = true;
            const vistos = new Map();
            filas.forEach((f, i) => {
                if (f.numero_serie && vistos.has(f.numero_serie)) {
                    marcar(i, 'error', `N° de serie repetido en el archivo (fila ${vistos.get(f.numero_serie) + 1})`);
                } else {
                    vistos.set(f.numero_serie, i);
                }
            });
            for (let i = 0; i < filas.length && !cancelado; i++) {
                if (estados[i].estado === 'error') continue;
                progreso.textContent = `Revisando ${i + 1} de ${filas.length}…`;
                try {
                    const r = await api.post('alta_equipo.php', { equipo: filas[i], solo_validar: true });
                    marcar(i, 'lista', r.nuevos.length ? `Lista · crea ${describirNuevos(r.nuevos)}` : 'Lista', r.nuevos);
                } catch (error) {
                    if (error instanceof SesionExpirada || error instanceof ClavePendiente) return;
                    marcar(i, 'error', error instanceof ApiError ? error.message : 'Error inesperado');
                }
            }
            ocupado = false;
            if (cancelado) return;
            mostrarResumen();
        }

        function mostrarResumen() {
            const listas = estados.filter((e) => e.estado === 'lista').length;
            const errores = estados.filter((e) => e.estado === 'error').length;
            const nuevos = nuevosUnicos();
            progreso.textContent = `${filas.length} filas: ${listas} listas para insertar, ${errores} con errores.`;
            resumen.replaceChildren(...(nuevos.length
                ? [el('p', { class: 'mensaje-info' }, `Se van a crear en los catálogos: ${describirNuevos(nuevos)}.`)]
                : []));
            btnInsertar.disabled = !listas;
            btnInsertar.textContent = `Insertar ${listas} equipos`;
            btnErrores.hidden = !errores;
        }

        function nuevosUnicos() {
            const unicos = new Map();
            for (const e of estados) {
                if (e.estado !== 'lista') continue;
                for (const n of e.nuevos) {
                    unicos.set(`${n.catalogo}|${n.valor}|${n.marca ?? ''}|${n.tipo ?? ''}`.toUpperCase(), n);
                }
            }
            return [...unicos.values()];
        }

        // 2) Alta de las filas que pasaron la revisión.
        async function insertar() {
            if (ocupado) return;
            const nuevos = nuevosUnicos();
            if (nuevos.length && !await confirmar('Valores nuevos en los catálogos',
                `Se van a crear ${nuevos.length} valores nuevos: ${describirNuevos(nuevos)}. ¿Continuar con la importación?`,
                { aceptar: 'Crear e insertar' })) {
                return;
            }
            ocupado = true;
            btnInsertar.disabled = true;
            const indices = estados.map((e, i) => (e.estado === 'lista' ? i : -1)).filter((i) => i >= 0);
            let guardados = 0;
            for (const [n, i] of indices.entries()) {
                if (cancelado) break;
                progreso.textContent = `Importando ${n + 1} de ${indices.length}: N° de serie ${filas[i].numero_serie}`;
                try {
                    await api.post('alta_equipo.php', { equipo: filas[i], crear_nuevos: true });
                    marcar(i, 'guardada', 'Guardado');
                    guardados++;
                } catch (error) {
                    if (error instanceof SesionExpirada || error instanceof ClavePendiente) break;
                    marcar(i, 'error', error instanceof ApiError ? error.message : 'Error inesperado');
                }
            }
            ocupado = false;
            const errores = estados.filter((e) => e.estado === 'error').length;
            progreso.textContent = cancelado
                ? `Importación cancelada: se guardaron ${guardados} equipos.`
                : `Se guardaron ${guardados} equipos${errores ? `; ${errores} filas con errores` : ''}.`;
            resumen.replaceChildren();
            btnInsertar.textContent = 'Insertar registros';
            btnErrores.hidden = !errores;
            aviso(`Importación: ${guardados} equipos guardados${errores ? `, ${errores} con errores` : ''}.`, errores ? 'error' : 'exito');
            if (guardados) cargar();
        }

        async function descargarErrores() {
            const errores = filas
                .map((f, i) => ({ f, e: estados[i] }))
                .filter(({ e }) => e.estado === 'error')
                .map(({ f, e }) => ({
                    'N° Serie': f.numero_serie, Tipo: f.tipo, Marca: f.marca, Modelo: f.modelo,
                    Escala: f.escala, Sector: f.sector, Estado: f.estado, 'Motivo del error': e.texto,
                }));
            try {
                await exportarExcel(errores, `errores_importacion_${fechaArchivo()}.xlsx`);
            } catch (error) {
                console.error(error);
                aviso('No se pudo generar el Excel de errores.', 'error');
            }
        }
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

/** "tipo "X", modelo "Y" (Motorola, Handie-Talkie)" */
function describirNuevos(nuevos) {
    return nuevos.map((n) => (n.catalogo === 'modelo'
        ? `modelo "${n.valor}" (${n.marca}, ${n.tipo})`
        : `${n.catalogo} "${n.valor}"`)).join(', ');
}

/** Equivale a str.title() de Python: mayúscula después de cualquier carácter que no sea letra. */
function aTitulo(texto) {
    return texto.toLowerCase().replace(/(^|[^\p{L}])(\p{L})/gu, (_, previo, letra) => previo + letra.toUpperCase());
}

/** Aplica `transformar` al valor del campo conservando la posición del cursor. */
function normalizarMientrasEscribe(input, transformar) {
    const nuevo = transformar(input.value);
    if (nuevo === input.value) return;
    const cursor = input.selectionStart - (input.value.length - nuevo.length);
    input.value = nuevo;
    input.setSelectionRange(Math.max(cursor, 0), Math.max(cursor, 0));
}

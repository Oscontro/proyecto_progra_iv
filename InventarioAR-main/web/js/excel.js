// Exportación a Excel en el navegador (reemplaza pandas.to_excel + openpyxl).
//
// Equivalencia con el cliente de escritorio:
//   pd.DataFrame(filas).to_excel(archivo, index=False)
//     -> columnas = claves de los registros, en orden de aparición
//     -> valores None/NaN quedan como celdas vacías
//   ajuste de openpyxl: ancho de cada columna = largo máximo del texto + margen
//
// SheetJS (vendor/sheetjs, Apache 2.0) pesa ~1 MB: se carga solo al exportar.

let xlsx = null;

async function cargarSheetJS() {
    xlsx ??= await import('../vendor/sheetjs/xlsx.mjs');
    return xlsx;
}

/**
 * Descarga `filas` (array de objetos) como .xlsx.
 *   margen: caracteres extra de ancho por columna (3 en Inventario, como el escritorio)
 */
export async function exportarExcel(filas, nombreArchivo, { hoja = 'Sheet1', margen = 3 } = {}) {
    const XLSX = await cargarSheetJS();

    // Columnas en orden de aparición, como hace pandas con una lista de dicts.
    const columnas = [];
    for (const fila of filas) {
        for (const clave of Object.keys(fila)) {
            if (!columnas.includes(clave)) {
                columnas.push(clave);
            }
        }
    }

    const limpias = filas.map((fila) => Object.fromEntries(
        columnas.map((c) => [c, fila[c] === null || fila[c] === undefined ? '' : fila[c]])));
    const sheet = XLSX.utils.json_to_sheet(limpias, { header: columnas });

    // `width` en unidades de Excel, igual que column_dimensions[...].width de openpyxl.
    sheet['!cols'] = columnas.map((c) => ({
        width: Math.max(String(c).length, ...limpias.map((f) => String(f[c]).length)) + margen,
    }));

    const libro = XLSX.utils.book_new();
    XLSX.utils.book_append_sheet(libro, sheet, hoja);
    XLSX.writeFile(libro, nombreArchivo, { compression: true });
}

/** Fecha local en formato AAAA-MM-DD para nombres de archivo. */
export function fechaArchivo(fecha = new Date()) {
    const dos = (n) => String(n).padStart(2, '0');
    return `${fecha.getFullYear()}-${dos(fecha.getMonth() + 1)}-${dos(fecha.getDate())}`;
}

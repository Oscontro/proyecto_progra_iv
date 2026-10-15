// Diálogo de historial de un equipo o vehículo (equivale a DialogoHistorial
// del cliente de escritorio). Las columnas se mapean por nombre de campo,
// no por posición, para no depender del orden del SELECT.

import { el, aviso, tabla, textoCelda, dialogo } from './ui.js';

const COLUMNAS = [
    { titulo: 'Fecha', valor: (h) => h.fecha_evento },
    { titulo: 'Usuario', valor: (h) => h.usuario_evento },
    { titulo: 'Tipo de evento', valor: (h) => h.tipo_evento },
    { titulo: 'Campo modificado', valor: (h) => h.campo_modificado },
    { titulo: 'Valor anterior', valor: (h) => h.valor_anterior },
    { titulo: 'Valor nuevo', valor: (h) => h.valor_nuevo },
    { titulo: 'Observaciones', valor: (h) => h.observaciones },
];

/** equipo: { id_equipo, marca, modelo_equipo, numero_serie } */
export async function verHistorialEquipo(api, equipo) {
    const historial = await api.get('historialEquipo.php', { id_equipo: equipo.id_equipo });
    mostrar(historial, `Historial de ${textoCelda(equipo.marca)} ${textoCelda(equipo.modelo_equipo)} ${textoCelda(equipo.numero_serie)}`,
            'No hay historial para este equipo.');
}

/** vehiculo: { tipo, identificacion } */
export async function verHistorialVehiculo(api, vehiculo) {
    const historial = await api.get('historialVehiculos.php', { identificacion: vehiculo.identificacion });
    mostrar(historial, `Historial de ${textoCelda(vehiculo.tipo)} ${textoCelda(vehiculo.identificacion)}`,
            'No hay historial para este vehículo.');
}

function mostrar(historial, titulo, vacio) {
    if (!historial?.length) {
        aviso(vacio);
        return;
    }
    dialogo(titulo, [el('p', { class: 'texto-suave' }, `${historial.length} evento(s)`), tabla(COLUMNAS, historial)],
            { ancho: 'ancho' });
}

// Acciones sobre varias filas elegidas a la vez (Inventario y Papelera).
//
// Cada ítem se manda por separado al mismo endpoint que usa la acción
// individual, así el servidor valida cada caso igual que siempre (en la
// papelera, en taller, etc.). Un error de la API en un ítem no frena al resto;
// la sesión vencida o la falta de conexión sí cortan el lote.

import { ApiError, SesionExpirada, ClavePendiente } from './api.js';
import { el } from './ui.js';

/** Devuelve { hechos: [item], fallidos: [{ item, mensaje }] }. */
export async function enLote(items, accion) {
    const hechos = [];
    const fallidos = [];
    for (const item of items) {
        try {
            await accion(item);
            hechos.push(item);
        } catch (error) {
            if (!(error instanceof ApiError) || error instanceof SesionExpirada || error instanceof ClavePendiente) {
                throw error;
            }
            fallidos.push({ item, mensaje: error.message });
        }
    }
    return { hechos, fallidos };
}

/** Lista con desplazamiento de los ítems elegidos, para los diálogos de confirmación. */
export function listaLote(textos) {
    return el('ul', { class: 'lista-lote' }, textos.map((t) => el('li', {}, t)));
}

/** Texto del botón con la cantidad elegida cuando es más de una: "Restaurar (3)". */
export function rotular(boton, texto, cantidad) {
    boton.textContent = cantidad > 1 ? `${texto} (${cantidad})` : texto;
}

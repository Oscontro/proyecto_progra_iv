// Registro de pestañas de la aplicación web.
//
// Cada pestaña migrada es un módulo en js/pestanas/ que exporta:
//
//   export function montar(contenedor, ctx) {
//       // construye la interfaz dentro de `contenedor` (una sola vez)
//       return {
//           mostrar() { ... },   // se llama cada vez que se activa la pestaña
//       };
//   }
//
// ctx = { api, usuario }  (usuario: {id, username, es_admin})
//
// `cargar` en null = pestaña todavía no migrada (se muestra un aviso).
// `soloAdmin` solo oculta la pestaña: el permiso real lo controla la API.

export const PESTANAS = [
    { id: 'ingreso',        titulo: 'Ingreso de Equipos', icono: '📥', cargar: null },
    { id: 'inventario',     titulo: 'Inventario',         icono: '📦', cargar: () => import('./pestanas/inventario.js') },
    { id: 'taller',         titulo: 'Taller',             icono: '🛠️', cargar: () => import('./pestanas/taller.js') },
    { id: 'repuestos',      titulo: 'Repuestos',          icono: '🔩', cargar: null },
    { id: 'papelera',       titulo: 'Papelera',           icono: '🗑️', cargar: () => import('./pestanas/papelera.js') },
    { id: 'estadisticas',   titulo: 'Estadísticas',       icono: '📊', cargar: () => import('./pestanas/estadisticas.js') },
    { id: 'administracion', titulo: 'Administración',     icono: '👤', cargar: null, soloAdmin: true },
];

export function pestanasPara(usuario) {
    return PESTANAS.filter((p) => !p.soloAdmin || usuario.es_admin);
}

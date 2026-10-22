// Tema claro/oscuro de la aplicación.
// Script clásico (no módulo) cargado en el <head> de app.php y de las páginas públicas
// antes de la hoja de estilos, para que la página se pinte directamente con el tema
// correcto, sin parpadeo. Sin elección guardada se sigue la preferencia del sistema.
// Los botones que lo cambian están en js/app.js (alternarTema) y js/sitio.js.

(function () {
    var guardado = null;
    try {
        guardado = localStorage.getItem('tema');
    } catch (e) {
        // almacenamiento bloqueado: se usa la preferencia del sistema
    }
    var oscuro = guardado ? guardado === 'oscuro'
                          : matchMedia('(prefers-color-scheme: dark)').matches;
    document.documentElement.dataset.tema = oscuro ? 'oscuro' : 'claro';
})();

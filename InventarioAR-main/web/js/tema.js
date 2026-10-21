// Tema claro/oscuro de la aplicación.
// Script clásico (no módulo) cargado en el <head> de app.php antes de la hoja de estilos,
// para que la página se pinte directamente con el tema correcto, sin parpadeo.
// Sin elección guardada se sigue la preferencia del sistema operativo.
// El botón que lo cambia está en js/app.js (alternarTema).

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

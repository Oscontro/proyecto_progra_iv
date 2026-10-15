<?php
// Cierre de sesión desde el menú de las páginas públicas (formulario POST con token CSRF).
require_once __DIR__ . '/inc/inicio.php';

if ($_SERVER['REQUEST_METHOD'] !== 'POST' || !csrfValido($_POST['csrf'] ?? null)) {
    redirigir('index.php');
}
cerrarSesion();
redirigir('index.php?salida=1');

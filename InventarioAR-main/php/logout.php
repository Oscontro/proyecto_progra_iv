<?php
// Cierra la sesión de PHP. Responde éxito aunque ya no hubiera sesión
// (cerrar sesión es idempotente). La página web/salir.php hace lo mismo
// desde un formulario HTML.
require_once 'auth.php';

if (($_SERVER['REQUEST_METHOD'] ?? '') !== 'POST') {
    sendError('Método no permitido', 405);
}
exigirXRequestedWith();

cerrarSesion();

sendSuccess(['cerrada' => true], 'Sesión cerrada');

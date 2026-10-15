<?php
// Devuelve el usuario de la sesión actual. Sirve para saber, al abrir la
// aplicación, si el token o la cookie guardados siguen siendo válidos.
require_once 'auth.php';
$user = requireAuth(true);   // también responde si tiene la clave pendiente de cambio

sendSuccess([
    'id'                 => (int)$user['id'],
    'username'           => $user['username'],
    'es_admin'           => (bool)$user['es_administrador'],
    'debe_cambiar_clave' => (bool)$user['debe_cambiar_clave'],
]);

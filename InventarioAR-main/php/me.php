<?php
// Devuelve el usuario de la sesión actual. La aplicación lo pide al abrir
// para saber quién es y si tiene que cambiar la contraseña.
require_once 'auth.php';
$user = requireAuth(true);   // también responde si tiene la clave pendiente de cambio

sendSuccess([
    'id'                 => (int)$user['id'],
    'username'           => $user['username'],
    'nombre'             => $user['nombre'],
    'apellido'           => $user['apellido'],
    'es_admin'           => (bool)$user['es_administrador'],
    'debe_cambiar_clave' => (bool)$user['debe_cambiar_clave'],
]);

<?php
// Autenticación de la API JSON con la sesión nativa de PHP ($_SESSION).
//
// El login lo hace la página web/ingresar.php (formulario HTML); la API solo
// verifica que haya una sesión válida. Cada pedido debe traer además el
// header X-Requested-With, que un formulario de otro sitio no puede enviar
// (protección CSRF de la API).
require_once 'conexion.php';
require_once 'sesion.php';

// Lee el cuerpo JSON de la petición y lo devuelve como array.
function getJsonInput(): array {
    $data = json_decode(file_get_contents('php://input'), true);
    return is_array($data) ? $data : [];
}

function exigirXRequestedWith(): void {
    if (($_SERVER['HTTP_X_REQUESTED_WITH'] ?? '') === '') {
        sendError('Falta el header X-Requested-With', 403);
    }
}

// ─────────────────────────────────────────────────────────
// Poné esto al inicio de CUALQUIER endpoint que requiera login.
// Devuelve el usuario ['id', 'username', 'nombre', 'apellido',
// 'es_administrador', 'debe_cambiar_clave'], o corta con 401.
//
// Si el usuario tiene una clave temporal (debe_cambiar_clave = 1) se
// corta con 403, salvo en los endpoints que lo permiten explícitamente
// (cambiar_clave.php, me.php).
// ─────────────────────────────────────────────────────────
function requireAuth(bool $permitirClavePendiente = false): array {
    exigirXRequestedWith();
    $user = usuarioDeSesion(getConnection());
    if (!$user) {
        sendError('La sesión no es válida o venció', 401);
    }
    if ($user['debe_cambiar_clave'] && !$permitirClavePendiente) {
        sendError('Debés cambiar tu contraseña antes de continuar', 403,
                  ['code' => 'DEBE_CAMBIAR_CLAVE']);
    }
    return $user;
}

// ─────────────────────────────────────────────────────────
// Poné esto en los endpoints que SOLO puede usar un admin.
// Corta con 403 (autenticado, pero sin permiso) si no lo es.
// ─────────────────────────────────────────────────────────
function requireAdmin(): array {
    $user = requireAuth();
    if (!$user['es_administrador']) {
        sendError('No tenés permisos para esta acción', 403);
    }
    return $user;
}

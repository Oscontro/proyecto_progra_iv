<?php
// Cierra la sesión: invalida el token en la base y borra la cookie.
// Responde éxito aunque el token ya no fuera válido (cerrar sesión es idempotente).
require_once 'auth.php';

if (($_SERVER['REQUEST_METHOD'] ?? '') !== 'POST') {
    sendError('Método no permitido', 405);
}

[$token, $origen] = getRequestToken();
if ($origen === 'cookie' && ($_SERVER['HTTP_X_REQUESTED_WITH'] ?? '') === '') {
    sendError('Falta el header X-Requested-With', 403);
}

if ($token) {
    $pdo = getConnection();
    $pdo->prepare("DELETE FROM sessions WHERE token_hash = ?")
        ->execute([hash('sha256', $token)]);
}
clearSessionCookie();

sendSuccess(['cerrada' => true], 'Sesión cerrada');

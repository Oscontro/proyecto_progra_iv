<?php
// Capa de autenticación por token.
// Se apoya en tu conexion.php (que a su vez incluye config.php).
require_once 'conexion.php';

// Lee el cuerpo JSON de la petición y lo devuelve como array.
function getJsonInput(): array {
    $data = json_decode(file_get_contents('php://input'), true);
    return is_array($data) ? $data : [];
}

// Extrae el token del header "Authorization: Bearer xxxxx".
function getBearerToken(): ?string {
    $auth = '';
    if (function_exists('getallheaders')) {
        $headers = array_change_key_case(getallheaders(), CASE_LOWER);
        $auth = $headers['authorization'] ?? '';
    }
    // Fallback: en algunas configuraciones de Apache el header llega por acá.
    if ($auth === '') {
        $auth = $_SERVER['HTTP_AUTHORIZATION'] ?? '';
    }
    if (preg_match('/Bearer\s+(\S+)/i', $auth, $m)) {
        return $m[1];
    }
    return null;
}

// ─────────────────────────────────────────────────────────
// Poné esto al inicio de CUALQUIER endpoint que requiera login.
// Devuelve el usuario, o corta con 401.
// ─────────────────────────────────────────────────────────
function requireAuth(): array {
    $token = getBearerToken();
    if (!$token) {
        sendError('Falta el token', 401);
    }

    $pdo  = getConnection();
    $stmt = $pdo->prepare(
        "SELECT u.id_usuario AS id, u.username, u.es_administrador
           FROM sessions s
           JOIN usuarios u ON u.id_usuario = s.usuario_id
          WHERE s.token_hash = ?
            AND s.expires_at > NOW()
            AND u.activo = 1"
    );
    // En la base guardamos el hash del token, así que hasheamos el que llega.
    $stmt->execute([hash('sha256', $token)]);
    $user = $stmt->fetch();

    if (!$user) {
        sendError('Token inválido o expirado', 401);
    }
    return $user;
}

// ─────────────────────────────────────────────────────────
// Poné esto en los endpoints que SOLO puede usar un admin.
// Corta con 403 (autenticado, pero sin permiso) si no lo es.
// ─────────────────────────────────────────────────────────
function requireAdmin(): array {
    $user = requireAuth();          // primero: ¿está logueado?
    if (!$user['es_administrador']) {       // después: ¿es admin?
        sendError('No tenés permisos para esta acción', 403);
    }
    return $user;
}
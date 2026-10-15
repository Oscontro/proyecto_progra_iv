<?php
// Capa de autenticación por token.
// Se apoya en tu conexion.php (que a su vez incluye config.php).
//
// El token se acepta por dos vías:
//   - Header "Authorization: Bearer xxxxx"  (cliente de escritorio)
//   - Cookie HttpOnly SESSION_COOKIE        (frontend web)
// Cuando llega por cookie se exige además el header X-Requested-With,
// que un formulario de otro sitio no puede enviar (protección CSRF).
require_once 'conexion.php';

const SESSION_COOKIE = 'inv_token';

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

// Devuelve [token, origen] donde origen es 'header' o 'cookie'.
function getRequestToken(): array {
    $token = getBearerToken();
    if ($token) {
        return [$token, 'header'];
    }
    $cookie = $_COOKIE[SESSION_COOKIE] ?? '';
    if ($cookie !== '') {
        return [$cookie, 'cookie'];
    }
    return [null, null];
}

// La cookie solo viaja a la carpeta de la API.
function sessionCookiePath(): string {
    return rtrim(str_replace('\\', '/', dirname($_SERVER['SCRIPT_NAME'] ?? '/')), '/') . '/';
}

function setSessionCookie(string $token, int $expira): void {
    setcookie(SESSION_COOKIE, $token, [
        'expires'  => $expira,
        'path'     => sessionCookiePath(),
        'secure'   => !empty($_SERVER['HTTPS']) && $_SERVER['HTTPS'] !== 'off',
        'httponly' => true,
        'samesite' => 'Strict',
    ]);
}

function clearSessionCookie(): void {
    setcookie(SESSION_COOKIE, '', [
        'expires'  => time() - 3600,
        'path'     => sessionCookiePath(),
        'httponly' => true,
        'samesite' => 'Strict',
    ]);
}

// ─────────────────────────────────────────────────────────
// Poné esto al inicio de CUALQUIER endpoint que requiera login.
// Devuelve el usuario, o corta con 401.
//
// Si el usuario tiene una clave temporal (debe_cambiar_clave = 1) se
// corta con 403, salvo en los endpoints que lo permiten explícitamente
// (cambiar_clave.php, me.php, logout.php).
// ─────────────────────────────────────────────────────────
function requireAuth(bool $permitirClavePendiente = false): array {
    [$token, $origen] = getRequestToken();
    if (!$token) {
        sendError('Falta el token', 401);
    }
    if ($origen === 'cookie' && ($_SERVER['HTTP_X_REQUESTED_WITH'] ?? '') === '') {
        sendError('Falta el header X-Requested-With', 403);
    }

    $pdo  = getConnection();
    $stmt = $pdo->prepare(
        "SELECT u.id_usuario AS id, u.username, u.es_administrador, u.debe_cambiar_clave
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
        if ($origen === 'cookie') {
            clearSessionCookie();
        }
        sendError('Token inválido o expirado', 401);
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
    $user = requireAuth();          // primero: ¿está logueado?
    if (!$user['es_administrador']) {       // después: ¿es admin?
        sendError('No tenés permisos para esta acción', 403);
    }
    return $user;
}

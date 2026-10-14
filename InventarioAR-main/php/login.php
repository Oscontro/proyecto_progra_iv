<?php
require_once 'auth.php';   // trae conexion.php, config.php y getJsonInput()

$input    = getJsonInput();
$username = trim($input['username'] ?? '');
$password = $input['password'] ?? '';

if ($username === '' || $password === '') {
    sendError('Faltan credenciales', 400);
}

$pdo  = getConnection();
$stmt = $pdo->prepare("SELECT * FROM usuarios WHERE username = ?");
$stmt->execute([$username]);
$user = $stmt->fetch();

// Mensaje genérico: no revelamos si falló el usuario o la contraseña.
if (!$user || !$user['activo']) {
    sendError('Usuario o contraseña incorrectos', 401);
}

// ¿Cuenta bloqueada por intentos fallidos?
if ($user['bloqueado_hasta'] !== null && strtotime($user['bloqueado_hasta']) > time()) {
    sendError('Cuenta bloqueada temporalmente. Intente más tarde.', 429);
}

// password_verify compara contra el hash bcrypt guardado.
// Esto vale TAMBIÉN para la clave temporal del primer login o reset:
// el usuario tiene que conocer esa clave temporal para entrar.
if (!password_verify($password, $user['password_hash'])) {
    $intentos = $user['intentos_fallidos'] + 1;
    $bloqueo  = $intentos >= 5 ? date('Y-m-d H:i:s', time() + 900) : null; // 15 min
    $pdo->prepare(
        "UPDATE usuarios SET intentos_fallidos = ?, bloqueado_hasta = ? WHERE id_usuario = ?"
    )->execute([$intentos, $bloqueo, $user['id_usuario']]);
    sendError('Usuario o contraseña incorrectos', 401);
}

// Login correcto: reseteamos el contador de intentos.
$pdo->prepare(
    "UPDATE usuarios SET intentos_fallidos = 0, bloqueado_hasta = NULL WHERE id_usuario = ?"
)->execute([$user['id_usuario']]);

// Generamos el token. El cliente recibe $token; en la base va solo su hash.
$token      = bin2hex(random_bytes(32));                   // 64 caracteres
$token_hash = hash('sha256', $token);
$expires_at = date('Y-m-d H:i:s', time() + 1 * 24 * 3600); // 1 día

$pdo->prepare(
    "INSERT INTO sessions (usuario_id, token_hash, expires_at) VALUES (?, ?, ?)"
)->execute([$user['id_usuario'], $token_hash, $expires_at]);

// El login solo VERIFICA y avisa. NO cambia la contraseña.
// Si debe_cambiar_clave es true, el cliente obliga al cambio en un paso aparte.
sendSuccess([
    'token'      => $token,
    'expires_at' => $expires_at,
    'user' => [
        'id'                 => (int)$user['id_usuario'],
        'username'           => $user['username'],
        'es_admin'           => (bool)$user['es_administrador'],
        'debe_cambiar_clave' => (bool)$user['debe_cambiar_clave'],
    ],
]);
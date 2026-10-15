<?php
// Sesión de usuario con la sesión nativa de PHP ($_SESSION).
//
// La comparten la API JSON (auth.php) y las páginas HTML de web/: no envía
// cabeceras propias ni imprime nada.
//
//   $_SESSION['usuario_id']  usuario logueado
//   $_SESSION['huella']      huella del hash de la contraseña: si la clave
//                            cambia (reseteo, cambio), las sesiones abiertas
//                            con la clave anterior dejan de valer
//   $_SESSION['inicio']      momento del login (vencimiento absoluto)
//   $_SESSION['ultimo']      último pedido (vencimiento por inactividad)
//   $_SESSION['csrf']        token para los formularios HTML
//
// En cada pedido el usuario se vuelve a leer de la base: desactivar una
// cuenta o quitarle el perfil de administrador tiene efecto inmediato.
require_once __DIR__ . '/config.php';

const SESION_NOMBRE      = 'INVSESION';
const SESION_INACTIVIDAD = 2 * 3600;    // 2 horas sin actividad
const SESION_MAXIMA      = 12 * 3600;   // 12 horas desde el login
const LOGIN_INTENTOS     = 5;           // intentos fallidos antes del bloqueo
const LOGIN_BLOQUEO      = 15 * 60;     // duración del bloqueo

function esHttps(): bool {
    return (!empty($_SERVER['HTTPS']) && $_SERVER['HTTPS'] !== 'off')
        || (($_SERVER['HTTP_X_FORWARDED_PROTO'] ?? '') === 'https');
}

/**
 * La cookie de sesión vale para la carpeta del proyecto (la que contiene
 * web/ y php/): la usan tanto las páginas como la API.
 */
function rutaCookieSesion(): string {
    $carpeta = str_replace('\\', '/', dirname($_SERVER['SCRIPT_NAME'] ?? '/'));
    return rtrim(str_replace('\\', '/', dirname($carpeta)), '/') . '/';
}

function iniciarSesion(): void {
    if (session_status() === PHP_SESSION_ACTIVE) {
        return;
    }
    ini_set('session.use_strict_mode', '1');
    ini_set('session.use_only_cookies', '1');
    session_name(SESION_NOMBRE);
    session_set_cookie_params([
        'lifetime' => 0,
        'path'     => rutaCookieSesion(),
        'secure'   => esHttps(),
        'httponly' => true,
        'samesite' => 'Lax',
    ]);
    session_start();
}

function huellaClave(string $hash): string {
    return substr(hash('sha256', $hash), 0, 32);
}

/** Abre la sesión de un usuario recién autenticado (fila completa de usuarios). */
function abrirSesion(array $usuario): void {
    iniciarSesion();
    session_regenerate_id(true);   // evita la fijación de sesión
    $_SESSION = [
        'usuario_id' => (int)$usuario['id_usuario'],
        'huella'     => huellaClave($usuario['password_hash']),
        'inicio'     => time(),
        'ultimo'     => time(),
        'csrf'       => bin2hex(random_bytes(32)),
    ];
}

function cerrarSesion(): void {
    iniciarSesion();
    $_SESSION = [];
    $p = session_get_cookie_params();
    setcookie(session_name(), '', [
        'expires'  => time() - 3600,
        'path'     => $p['path'],
        'secure'   => $p['secure'],
        'httponly' => true,
        'samesite' => $p['samesite'],
    ]);
    session_destroy();
}

/**
 * Usuario de la sesión actual validado contra la base, o null si no hay
 * sesión válida (en ese caso la cierra).
 *   $liberar: suelta el bloqueo del archivo de sesión al terminar, para que
 *             los pedidos simultáneos de la aplicación no se esperen entre sí.
 */
function usuarioDeSesion(PDO $pdo, bool $liberar = true): ?array {
    iniciarSesion();
    $id = $_SESSION['usuario_id'] ?? null;
    if (!$id) {
        if ($liberar) session_write_close();
        return null;
    }
    $ahora = time();
    if ($ahora - ($_SESSION['ultimo'] ?? 0) > SESION_INACTIVIDAD
        || $ahora - ($_SESSION['inicio'] ?? 0) > SESION_MAXIMA) {
        cerrarSesion();
        return null;
    }

    $stmt = $pdo->prepare(
        "SELECT id_usuario AS id, username, nombre, apellido, email, es_administrador,
                debe_cambiar_clave, activo, password_hash
           FROM usuarios WHERE id_usuario = ?");
    $stmt->execute([$id]);
    $usuario = $stmt->fetch(PDO::FETCH_ASSOC);
    if (!$usuario || !$usuario['activo']
        || !hash_equals((string)($_SESSION['huella'] ?? ''), huellaClave($usuario['password_hash']))) {
        cerrarSesion();
        return null;
    }

    $_SESSION['ultimo'] = $ahora;
    if ($liberar) session_write_close();
    unset($usuario['password_hash'], $usuario['activo']);
    $usuario['id'] = (int)$usuario['id'];
    return $usuario;
}

/** Tras cambiar la propia contraseña, la sesión actual sigue valiendo con la clave nueva. */
function actualizarHuellaSesion(string $nuevoHash): void {
    iniciarSesion();
    $_SESSION['huella'] = huellaClave($nuevoHash);
    session_write_close();
}

// ─────────────────────────────────────────────────────────
// Login
// ─────────────────────────────────────────────────────────

/**
 * Verifica usuario y contraseña. Devuelve ['usuario' => fila] si se puede
 * entrar, o ['error' => código]:
 *   credenciales | bloqueada | pendiente | inactiva
 * "pendiente" e "inactiva" solo se informan con la contraseña correcta,
 * así no se revela qué cuentas existen.
 */
function autenticar(PDO $pdo, string $username, string $clave): array {
    $stmt = $pdo->prepare("SELECT * FROM usuarios WHERE username = ?");
    $stmt->execute([$username]);
    $usuario = $stmt->fetch(PDO::FETCH_ASSOC);

    if (!$usuario) {
        password_verify($clave, '$2y$10$KP4U.voJdQ9zgkk4Dp5fPu3AU2Nif7KVjr3QE6Tbl8N9fWWZBmFEG'); // mismo tiempo de respuesta
        return ['error' => 'credenciales'];
    }
    if ($usuario['bloqueado_hasta'] !== null && strtotime($usuario['bloqueado_hasta']) > time()) {
        return ['error' => 'bloqueada'];
    }
    if (!password_verify($clave, $usuario['password_hash'])) {
        $intentos = (int)$usuario['intentos_fallidos'] + 1;
        $bloqueo  = $intentos >= LOGIN_INTENTOS ? date('Y-m-d H:i:s', time() + LOGIN_BLOQUEO) : null;
        $pdo->prepare("UPDATE usuarios SET intentos_fallidos = ?, bloqueado_hasta = ? WHERE id_usuario = ?")
            ->execute([$bloqueo ? 0 : $intentos, $bloqueo, $usuario['id_usuario']]);
        return ['error' => $bloqueo ? 'bloqueada' : 'credenciales'];
    }

    $pdo->prepare("UPDATE usuarios SET intentos_fallidos = 0, bloqueado_hasta = NULL WHERE id_usuario = ?")
        ->execute([$usuario['id_usuario']]);
    if ($usuario['pendiente_aprobacion']) {
        return ['error' => 'pendiente'];
    }
    if (!$usuario['activo']) {
        return ['error' => 'inactiva'];
    }

    // Si PHP mejoró el algoritmo por defecto, se actualiza el hash guardado.
    if (password_needs_rehash($usuario['password_hash'], PASSWORD_DEFAULT)) {
        $usuario['password_hash'] = password_hash($clave, PASSWORD_DEFAULT);
        $pdo->prepare("UPDATE usuarios SET password_hash = ? WHERE id_usuario = ?")
            ->execute([$usuario['password_hash'], $usuario['id_usuario']]);
    }
    $pdo->prepare("UPDATE usuarios SET fecha_ultima_conexion = NOW() WHERE id_usuario = ?")
        ->execute([$usuario['id_usuario']]);
    return ['usuario' => $usuario];
}

// ─────────────────────────────────────────────────────────
// Formularios HTML: token CSRF y mensajes de una sola vez
// ─────────────────────────────────────────────────────────

function tokenCsrf(): string {
    iniciarSesion();
    if (empty($_SESSION['csrf'])) {
        $_SESSION['csrf'] = bin2hex(random_bytes(32));
    }
    return $_SESSION['csrf'];
}

function csrfValido($token): bool {
    iniciarSesion();
    return is_string($token) && !empty($_SESSION['csrf']) && hash_equals($_SESSION['csrf'], $token);
}

/** Guarda (con $valor) o lee y borra (sin $valor) un dato para el próximo pedido. */
function flash(string $clave, $valor = null) {
    iniciarSesion();
    if (func_num_args() > 1) {
        $_SESSION['flash'][$clave] = $valor;
        return null;
    }
    $dato = $_SESSION['flash'][$clave] ?? null;
    unset($_SESSION['flash'][$clave]);
    return $dato;
}

<?php
// Base de las páginas HTML de web/ (portada, contacto, registro, ingreso,
// error y la aplicación). Usa la misma configuración y la misma sesión de
// PHP que la API, pero responde HTML en lugar de JSON.
require_once __DIR__ . '/../../php/config.php';
require_once __DIR__ . '/../../php/sesion.php';
require_once __DIR__ . '/plantilla.php';

// Un error inesperado muestra una página genérica (el detalle va al log).
set_exception_handler(function (Throwable $e) {
    error_log('Excepción en página: ' . $e);
    if (!headers_sent()) {
        http_response_code(500);
        header('Content-Type: text/html; charset=utf-8');
    }
    echo '<!DOCTYPE html><html lang="es"><meta charset="utf-8"><title>Error</title>'
       . '<p style="font-family:sans-serif;padding:2rem">Ocurrió un error interno. '
       . '<a href="index.php">Volver al inicio</a>.</p></html>';
});

/** Escapa texto para insertarlo en HTML. */
function e($texto): string {
    return htmlspecialchars((string)$texto, ENT_QUOTES, 'UTF-8');
}

function bd(): PDO {
    static $pdo = null;
    return $pdo ??= conectarBD();
}

/** Usuario logueado (validado contra la base) o null. La sesión queda abierta para la página. */
function usuarioActual(): ?array {
    static $usuario = false;
    if ($usuario === false) {
        $usuario = usuarioDeSesion(bd(), false);
    }
    return $usuario;
}

function redirigir(string $destino): void {
    header("Location: $destino", true, 303);
    exit;
}

/** Lleva a la página de error con el motivo (ver error.php). */
function irAError(string $codigo): void {
    redirigir('error.php?codigo=' . urlencode($codigo));
}

function ipCliente(): string {
    return substr((string)($_SERVER['REMOTE_ADDR'] ?? ''), 0, 45);
}

/**
 * Limita la frecuencia de un formulario por sesión (registro, contacto).
 * Devuelve los segundos que faltan, o 0 si se puede enviar.
 */
function esperaFormulario(string $clave, int $segundos): int {
    iniciarSesion();
    $ultimo = $_SESSION['ultimo_envio'][$clave] ?? 0;
    return max(0, $segundos - (time() - $ultimo));
}

function registrarEnvioFormulario(string $clave): void {
    iniciarSesion();
    $_SESSION['ultimo_envio'][$clave] = time();
}

<?php
// Configuración por defecto. Para cambiarla en un entorno concreto, copiar
// config.local.example.php como config.local.php (no se versiona) y
// sobrescribir solo las claves necesarias.
$config = [
    'db_host'       => '127.0.0.1',
    'db_user'       => 'root',
    'db_pass'       => '',
    'db_name'       => 'inventario_radios',
    'api_debug'     => false, // true = los errores de BD llegan al cliente
    'cors_origenes' => [],    // orígenes externos permitidos (el frontend web es del mismo origen)
];
if (is_file(__DIR__ . '/config.local.php')) {
    $config = array_merge($config, require __DIR__ . '/config.local.php');
}

// Configuración de la base de datos
define('DB_HOST', $config['db_host']);
define('DB_USER', $config['db_user']);
define('DB_PASS', $config['db_pass']);
define('DB_NAME', $config['db_name']);
define('DB_CHARSET', 'utf8mb4');
date_default_timezone_set("America/Argentina/Buenos_Aires");

// Configuración de la API
define('API_DEBUG', (bool)$config['api_debug']);
define('CORS_ORIGENES', $config['cors_origenes']);

// Headers comunes
header('Content-Type: application/json; charset=utf-8');

// CORS: solo para orígenes declarados. Sin Origin (cliente de escritorio)
// o con el mismo origen (frontend web) no hace falta ningún header.
$origen = $_SERVER['HTTP_ORIGIN'] ?? '';
if ($origen !== '' && in_array($origen, CORS_ORIGENES, true)) {
    header("Access-Control-Allow-Origin: $origen");
    header('Access-Control-Allow-Credentials: true');
    header('Access-Control-Allow-Methods: GET, POST, OPTIONS');
    header('Access-Control-Allow-Headers: Content-Type, Authorization, X-Requested-With');
    header('Vary: Origin');
}
if (($_SERVER['REQUEST_METHOD'] ?? '') === 'OPTIONS') {
    http_response_code(204);
    exit;
}

// Los errores de PHP nunca se imprimen: romperían el JSON de la respuesta.
// Se registran en logs/php_errores.log.
error_reporting(E_ALL);
ini_set('display_errors', '0');
ini_set('log_errors', '1');
ini_set('error_log', __DIR__ . '/logs/php_errores.log');

// Cualquier excepción no capturada o error fatal se responde como JSON.
function responderErrorInterno(string $detalle): void {
    if (!headers_sent()) {
        http_response_code(500);
        header('Content-Type: application/json; charset=utf-8');
    }
    echo json_encode(['error' => API_DEBUG ? $detalle : 'Error interno del servidor']);
}

set_exception_handler(function (Throwable $e) {
    error_log('Excepción no capturada: ' . $e);
    responderErrorInterno($e->getMessage());
});

register_shutdown_function(function () {
    $error = error_get_last();
    if ($error && in_array($error['type'], [E_ERROR, E_PARSE, E_CORE_ERROR, E_COMPILE_ERROR], true)) {
        responderErrorInterno($error['message']);
    }
});

<?php
// Configuración por defecto. Para cambiarla en un entorno concreto, copiar
// config.local.example.php como config.local.php (no se versiona) y
// sobrescribir solo las claves necesarias.
//
// Este archivo solo define constantes: no envía cabeceras ni imprime nada,
// así lo pueden usar tanto la API JSON (vía conexion.php) como las páginas
// HTML de web/ (vía web/inc/inicio.php).
$config = [
    'db_host'          => '127.0.0.1',
    'db_user'          => 'root',
    'db_pass'          => '',
    'db_name'          => 'inventario_radios',
    'api_debug'        => false, // true = los errores de BD llegan al cliente
    // Formulario de contacto: mail() envía la consulta a esta dirección
    // (simulada, como pide la consigna) y además se guarda en la tabla contactos.
    'contacto_destino' => 'consultas@inventario-radios.test',
    'mail_remitente'   => 'no-responder@inventario-radios.test',
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

define('API_DEBUG', (bool)$config['api_debug']);
define('CONTACTO_DESTINO', $config['contacto_destino']);
define('MAIL_REMITENTE', $config['mail_remitente']);

// Los errores de PHP nunca se imprimen (romperían el JSON o mostrarían
// rutas internas): se registran en logs/php_errores.log.
error_reporting(E_ALL);
ini_set('display_errors', '0');
ini_set('log_errors', '1');
ini_set('error_log', __DIR__ . '/logs/php_errores.log');

/** Conexión PDO. Lanza PDOException si falla: cada capa decide cómo informarlo. */
function conectarBD(): PDO {
    $dsn = "mysql:host=" . DB_HOST . ";dbname=" . DB_NAME . ";charset=" . DB_CHARSET;
    return new PDO($dsn, DB_USER, DB_PASS, [
        PDO::ATTR_ERRMODE            => PDO::ERRMODE_EXCEPTION,
        PDO::ATTR_DEFAULT_FETCH_MODE => PDO::FETCH_ASSOC,
        PDO::ATTR_EMULATE_PREPARES   => false,
    ]);
}

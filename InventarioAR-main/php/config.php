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
    // Formulario de contacto: la consulta se guarda en la tabla contactos y se
    // envía por correo a esta dirección (simulada por defecto, como pide la consigna).
    'contacto_destino' => 'consultas@inventario-radios.test',
    'mail_remitente'   => 'no-responder@inventario-radios.test',   // remitente de mail()
    // Correo por Brevo (php/correo.php): tiene prioridad sobre Resend. La API key
    // NO va acá (va en config.local.php / config.hosting.php). El remitente es una
    // dirección verificada en Brevo (panel > Senders); puede ser un Gmail.
    'brevo_api_key'           => '',
    'brevo_remitente'         => '',
    'brevo_remitente_nombre'  => 'Inventario de Radios',
    // Correo por Resend (php/correo.php). La API key NO va acá: se pone en
    // config.local.php (y en config.hosting.php para el hosting), que no se versionan.
    // Vacía (y sin Brevo) = se usa mail().
    'resend_api_key'    => '',
    // Sin dominio verificado en Resend hay que usar onboarding@resend.dev, que
    // solo puede enviar al email de la propia cuenta de Resend (contacto_destino).
    'resend_remitente'  => 'Inventario de Radios <onboarding@resend.dev>',
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
define('BREVO_API_KEY', trim((string)$config['brevo_api_key']));
define('BREVO_REMITENTE', trim((string)$config['brevo_remitente']));
define('BREVO_REMITENTE_NOMBRE', $config['brevo_remitente_nombre']);
define('RESEND_API_KEY', trim((string)$config['resend_api_key']));
define('RESEND_REMITENTE', $config['resend_remitente']);

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
        // Mismo comportamiento en cualquier servidor: el sql_mode con el que se
        // desarrolló y probó (el del hosting puede ser estricto) y la hora de
        // Argentina para NOW() y los DEFAULT current_timestamp() (el hosting
        // puede estar en otra zona). Argentina no tiene horario de verano.
        PDO::MYSQL_ATTR_INIT_COMMAND => "SET sql_mode = 'NO_ZERO_IN_DATE,NO_ZERO_DATE,NO_ENGINE_SUBSTITUTION', "
                                      . "time_zone = '-03:00'",
    ]);
}

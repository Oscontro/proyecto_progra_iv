<?php
// Configuración de la base de datos
define('DB_HOST', '127.0.0.1');
define('DB_USER', 'root');
define('DB_PASS', '');
define('DB_NAME', 'inventario_radios');
define('DB_CHARSET', 'utf8mb4');
date_default_timezone_set("America/Argentina/Buenos_Aires");

// Configuración de la API
define('API_DEBUG', true); // Cambiar a false en producción

// Headers comunes
header('Content-Type: application/json; charset=utf-8');
header('Access-Control-Allow-Origin: *');
header('Access-Control-Allow-Methods: GET, POST, PUT, DELETE');
header('Access-Control-Allow-Headers: Content-Type');

// Manejo de errores según ambiente
if (API_DEBUG) {
    error_reporting(E_ALL);
    ini_set('display_errors', 1);
} else {
    error_reporting(0);
    ini_set('display_errors', 0);
}
?>
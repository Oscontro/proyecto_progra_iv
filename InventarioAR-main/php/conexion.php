<?php
// Base de la API JSON: configuración, cabeceras y respuestas.
// Las páginas HTML de web/ NO incluyen este archivo (usan web/inc/inicio.php).
require_once 'config.php';

header('Content-Type: application/json; charset=utf-8');

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

function getConnection(): PDO {
    try {
        return conectarBD();
    } catch (PDOException $e) {
        error_log('Error de conexión: ' . $e->getMessage());
        sendError(API_DEBUG ? $e->getMessage() : "No se pudo conectar a la base de datos", 500);
    }
}

// Función auxiliar para respuestas de error
function sendError($message, $code = 500, array $extra = []) {
    http_response_code($code);
    echo json_encode(["error" => $message] + $extra);
    exit;
}

// Función auxiliar para respuestas exitosas
function sendSuccess($data, $message = null) {
    $response = ["success" => true];
    if ($message) {
        $response["message"] = $message;
    }
    $response["data"] = $data;
    echo json_encode($response);
    exit;
}

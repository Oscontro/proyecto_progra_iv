<?php
require_once 'config.php';

function getConnection() {
    try {
        $dsn = "mysql:host=" . DB_HOST . ";dbname=" . DB_NAME . ";charset=" . DB_CHARSET;
        $pdo = new PDO($dsn, DB_USER, DB_PASS);
        
        // Configurar PDO para lanzar excepciones
        $pdo->setAttribute(PDO::ATTR_ERRMODE, PDO::ERRMODE_EXCEPTION);
        
        // Devolver objetos asociativos por defecto
        $pdo->setAttribute(PDO::ATTR_DEFAULT_FETCH_MODE, PDO::FETCH_ASSOC);
        
        // Emular prepared statements desactivado (más seguro)
        $pdo->setAttribute(PDO::ATTR_EMULATE_PREPARES, false);
        
        return $pdo;
        
    } catch(PDOException $e) {
        http_response_code(500);
        echo json_encode([
            "error" => "Error de conexión",
            "message" => API_DEBUG ? $e->getMessage() : "No se pudo conectar a la base de datos"
        ]);
        exit;
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
?>
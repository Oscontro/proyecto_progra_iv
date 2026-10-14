<?php
require_once 'auth.php'; 
$user = requireAuth(); 

$archivo_log = __DIR__ . '/logs/errores_importacion.log';


try {
    $pdo = getConnection();
    // Configuraciones recomendadas para estabilidad y rendimiento
    $pdo->setAttribute(PDO::ATTR_ERRMODE, PDO::ERRMODE_EXCEPTION);
    $pdo->setAttribute(PDO::ATTR_DEFAULT_FETCH_MODE, PDO::FETCH_ASSOC);
    $datos = getJsonInput();
    $pdo->prepare("SET @usuario_actual = ?")->execute([$user['id']]);

    if (!$datos) {
        sendError("No se recibieron datos", 400);
        exit;
    }

    $identificacion = isset($datos['identificacion']) ? $datos['identificacion'] : null;
    
    $sql = "UPDATE vehiculos 
            SET radio_asignado = NULL
            WHERE identificacion = :identificacion";

    $stmt = $pdo->prepare($sql);
    $stmt->bindParam(":identificacion", $identificacion);
    $stmt->execute();

    sendSuccess(["success" => true, "message" => "Radio desasociada correctamente"]);
    
} catch(PDOException $e) {
    $error = date('Y-m-d H:i:s') . " | EXCEPCION | " . ($identificacion ?? 'N/A') . " | " . $e->getMessage();
    file_put_contents($archivo_log, $error . PHP_EOL, FILE_APPEND);
    sendError("Error: " . $e->getMessage(), 500);
    exit;
}
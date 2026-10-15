<?php
require_once 'auth.php';    // reemplaza a conexion.php, ya lo incluye adentro
$user = requireAuth(); 

$archivo_log = __DIR__ .  '/logs/errores_importacion.log';

try {

    $identificacion = $_GET['identificacion'] ?? null;

    if (!$identificacion) {
        sendError("No se recibieron datos", 400);
        exit;
    }

    $sql = "SELECT
                hv.fecha_evento,
                u.username as usuario_evento,
                hv.tipo_evento,
                hv.campo_modificado,
                hv.valor_anterior,
                hv.valor_nuevo,
                observaciones
            FROM historial_vehiculos hv
            JOIN vehiculos v ON v.id_vehiculo = hv.id_vehiculo
            LEFT JOIN usuarios u ON hv.usuario_evento = u.id_usuario
            WHERE v.identificacion = :identificacion
            ORDER BY hv.fecha_evento DESC";

    
    $pdo = getConnection();
    $pdo->setAttribute(PDO::ATTR_EMULATE_PREPARES, true);

    $stmt = $pdo->prepare($sql);
    $stmt->bindParam(":identificacion", $identificacion);
    $stmt->execute();
    
    $resultado = $stmt->fetchAll(PDO::FETCH_ASSOC);
    echo json_encode(["success" => true, "message" => "Consulta de historial existosa", "data" => $resultado]);
} catch(PDOException $e) {
    $error = date('Y-m-d H:i:s') . " | EXCEPCION | " . ($identificacion ?? 'N/A') . " | " . $e->getMessage();
    @file_put_contents($archivo_log, $error . PHP_EOL, FILE_APPEND);
    sendError(API_DEBUG ? $e->getMessage() : "Error al obtener el historial del vehículo", 500);
}

<?php
require_once 'auth.php';    // reemplaza a conexion.php, ya lo incluye adentro
$user = requireAuth(); 

$archivo_log = __DIR__ . '/logs/errores_importacion.log';

try {
    $id_equipo = $_GET['id_equipo'] ?? null;

    if (!$id_equipo) {
        sendError("No se recibieron datos", 400);
        exit;
    }
    
    $pdo = getConnection();
    $pdo->setAttribute(PDO::ATTR_EMULATE_PREPARES, true);

    $sql = "SELECT
                h.fecha_evento,
                u.username as usuario_evento,
                h.tipo_evento,
                h.campo_modificado,
                h.valor_anterior,
                h.valor_nuevo,
                h.observaciones
            FROM historial_equipos h
            LEFT JOIN usuarios u ON h.usuario_evento = u.id_usuario
            WHERE h.id_equipo = :id_equipo
            ORDER BY h.fecha_evento DESC";

    $stmt = $pdo->prepare($sql);
    $stmt->bindParam(":id_equipo", $id_equipo);
    $stmt->execute();
    
    $resultado = $stmt->fetchAll(PDO::FETCH_ASSOC);
    echo json_encode(["success" => true, "message" => "Consulta de historial existosa", "data" => $resultado]);
} catch(PDOException $e) {
    $error = date('Y-m-d H:i:s') . " | EXCEPCION | " . ($id_equipo ?? 'N/A') . " | " . $e->getMessage();
    @file_put_contents($archivo_log, $error . PHP_EOL, FILE_APPEND);
    sendError(API_DEBUG ? $e->getMessage() : "Error al obtener el historial del equipo", 500);
}

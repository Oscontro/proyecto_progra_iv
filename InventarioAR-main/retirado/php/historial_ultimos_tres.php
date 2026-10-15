<?php
require_once 'auth.php';    // reemplaza a conexion.php, ya lo incluye adentro
$user = requireAuth(); 

$archivo_log = __DIR__ . '/logs/errores_importacion.log';

$numero_serie = null;

try {
    $pdo = getConnection();
    $pdo->setAttribute(PDO::ATTR_ERRMODE, PDO::ERRMODE_EXCEPTION);
    
    $numero_serie = $_GET['numero_serie'] ?? null;

    $sql= "SELECT 
                h.fecha_evento,
                u.nombre,
                h.observaciones
            FROM historial_equipos h
            JOIN usuarios u ON h.usuario_evento = u.id_usuario
            WHERE (SELECT id_equipo FROM equipos WHERE numero_serie = :numero_serie) = h.id_equipo AND NOT h.tipo_evento = 'TEXTO AUTOMATICO'
            ORDER BY h.fecha_evento DESC LIMIT 3";
    
    $stmt = $pdo->prepare($sql);
    $stmt->bindParam(':numero_serie', $numero_serie, PDO::PARAM_STR);
    $stmt->execute();
    $data = $stmt->fetchAll(PDO::FETCH_ASSOC);
    if ($data) {
        sendSuccess(["success" => true, "message" => "Historial de los últimos 3 eventos del equipo", "data" => $data]);
    } else {
        sendError("No se encontraron eventos para el equipo con N° de Serie: $numero_serie", 404);
    }

} catch(PDOException $e) {
    $error = date('Y-m-d H:i:s') . " | EXCEPCION | " . ($numero_serie ?? 'N/A') . " | " . $e->getMessage();
    file_put_contents($archivo_log, $error . PHP_EOL, FILE_APPEND);
    sendError("Error al obtener el historial: " . $e->getMessage(), 500);
    exit;
}
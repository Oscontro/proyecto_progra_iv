<?php
require_once 'auth.php';    // reemplaza a conexion.php, ya lo incluye adentro
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
    }

    $numero_serie = isset($datos['numero_serie']) ? $datos['numero_serie'] : null;
    $identificacion = isset($datos['identificacion']) ? $datos['identificacion'] : null;

    $sql_check = "SELECT v.identificacion 
              FROM vehiculos v 
              INNER JOIN equipos e ON v.radio_asignado = e.id_equipo 
              WHERE e.numero_serie = :numero_serie";

    $stmt_check = $pdo->prepare($sql_check);
    $stmt_check->execute([':numero_serie' => $numero_serie]);

    if ($vehiculo_existente = $stmt_check->fetchColumn()) {
        sendError("La radio ya está asociada al interno " . $vehiculo_existente, 400);
        exit;
    }
    
    $sql = "UPDATE vehiculos 
            SET radio_asignado = (SELECT id_equipo FROM equipos WHERE numero_serie = :numero_serie)
            WHERE identificacion = :identificacion";

    $stmt = $pdo->prepare($sql);
    $stmt->bindParam(":numero_serie", $numero_serie);
    $stmt->bindParam(":identificacion", $identificacion);
    $stmt->execute();

    sendSuccess("Radio asociada correctamente");
    
} catch(PDOException $e) {
    $error = date('Y-m-d H:i:s') . " | EXCEPCION | " . ($numero_serie ?? 'N/A') . " | " . $e->getMessage();
    file_put_contents($archivo_log, $error . PHP_EOL, FILE_APPEND);
    sendError("Error: " . $e->getMessage(), 500);
    exit;
}
<?php
require_once 'auth.php';    // reemplaza a conexion.php, ya lo incluye adentro
$user = requireAuth(); 

$archivo_log = __DIR__ . '/logs/errores_importacion.log';

try {
    $pdo = getConnection();
    $pdo->setAttribute(PDO::ATTR_ERRMODE, PDO::ERRMODE_EXCEPTION);
    $pdo->setAttribute(PDO::ATTR_DEFAULT_FETCH_MODE, PDO::FETCH_ASSOC);
    $pdo->prepare("SET @usuario_actual = ?")->execute([$user['id']]);
    $datos = getJsonInput();

    if (!$datos) {
        sendError("No se recibieron datos", 400);
        exit;
    }

    $tipo = isset($datos['tipo']) ? $datos['tipo'] : null;
    $identificacion = isset($datos['identificacion']) ? $datos['identificacion'] : null;
    $escala = isset($datos['escala']) ? $datos['escala'] : null;

    $stmt_check = $pdo->prepare("SELECT COUNT(*) FROM vehiculos WHERE identificacion = :identificacion");
    $stmt_check->execute([':identificacion' => $identificacion]);
    if ($stmt_check->fetchColumn() > 0) {
        $error = date('Y-m-d H:i:s') . " | DUPLICADO | $identificacion | " . json_encode($datos, JSON_UNESCAPED_UNICODE);
        file_put_contents($archivo_log, $error . PHP_EOL, FILE_APPEND);
        sendError("El vehículo con identificación $identificacion ya existe", 400);
        exit;
    }
    
    $sql = "INSERT INTO vehiculos (tipo_vehiculo, identificacion, escala) 
            VALUES (:tipo, :identificacion, (SELECT id_escala FROM escalas WHERE escala = :escala))";

    $stmt = $pdo->prepare($sql);
    $stmt->bindParam(":tipo", $tipo);
    $stmt->bindParam(":identificacion", $identificacion);
    $stmt->bindParam(":escala", $escala);
    $stmt->execute();

    sendSuccess("Vehículo dado de alta correctamente");
    
} catch(PDOException $e) {
    $error = date('Y-m-d H:i:s') . " | EXCEPCION | " . ($identificacion ?? 'N/A') . " | " . $e->getMessage();
    file_put_contents($archivo_log, $error . PHP_EOL, FILE_APPEND);
    sendError("Error: " . $e->getMessage(), 500);
    exit;
}
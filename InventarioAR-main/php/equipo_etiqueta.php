<?php
require_once 'auth.php';    // reemplaza a conexion.php, ya lo incluye adentro
$user = requireAuth(); 

$archivo_log = __DIR__ . '/logs/errores_importacion.log';

$numero_serie = null;

try {
    $pdo = getConnection();

    $numero_serie = $_GET['numero_serie'] ?? null;

    if (!$numero_serie) {
        sendError("No se recibieron datos", 400);
        exit;
    }

    $sql = "SELECT * FROM vista_equipo_etiqueta WHERE numero_serie = :numero_serie";
    $stmt = $pdo->prepare($sql);
    $stmt->bindParam(':numero_serie', $numero_serie, PDO::PARAM_STR);
    $stmt->execute();

    $equipo = $stmt->fetch(PDO::FETCH_ASSOC);
    if ($equipo) {
        sendSuccess(["success" => true, "message" => "Equipo encontrado", "data" => $equipo]);
    } else {
        sendError("Equipo no encontrado", 404);
    }

} catch(PDOException $e) {
    $error = date('Y-m-d H:i:s') . " | EXCEPCION | " . ($numero_serie ?? 'N/A') . " | " . $e->getMessage();
    file_put_contents($archivo_log, $error . PHP_EOL, FILE_APPEND);
    sendError("Error: " . $e->getMessage(), 500);
    exit;
}
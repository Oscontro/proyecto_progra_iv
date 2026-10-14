<?php
require_once 'auth.php';
$user = requireAdmin();

$archivo_log = __DIR__ . '/logs/errores_importacion.log';

$origen = null;
$id_referencia = null;
$numero_serie = null;

try {
    $pdo = getConnection();
    $pdo->setAttribute(PDO::ATTR_EMULATE_PREPARES, false);
    $pdo->prepare("SET @usuario_actual = ?")->execute([$user['id']]);

    $datos = getJsonInput();
    if (!$datos) {
        sendError("No se recibieron datos", 400);
    }

    $origen         = $datos['origen'] ?? null;
    $id_referencia  = $datos['id_referencia'] ?? null;
    $numero_serie   = $datos['numero_serie'] ?? null;

    if (!$id_referencia) {
        sendError("Falta el id de la referencia", 400);
    }

    if ($origen == 'equipo'){
        $stmt = $pdo->prepare("SELECT id_equipo FROM equipos WHERE id_equipo = ? AND numero_serie = ?");
        $stmt->execute([$id_referencia, $numero_serie]);
        $equipo = $stmt->fetch(PDO::FETCH_ASSOC);
        if (!$equipo) {
            sendError("No se encontró el equipo con id y numero de serie proporcionados", 404);
            }
        $stmt = $pdo->prepare("DELETE FROM equipos WHERE id_equipo = ? AND numero_serie = ?");
        $stmt->execute([$id_referencia, $numero_serie]);
        sendSuccess(['dado_de_baja' => true], "Equipo eliminado correctamente");
    }
    else{
        $stmt = $pdo->prepare("SELECT id_vehiculo FROM vehiculos WHERE id_vehiculo = ? AND identificacion = ?");
        $stmt->execute([$id_referencia, $numero_serie]);
        $vehiculo = $stmt->fetch(PDO::FETCH_ASSOC);
        if (!$vehiculo) {
            sendError("No se encontró el vehículo con id y numero de serie proporcionados", 404);
            }
            $stmt = $pdo->prepare("DELETE FROM vehiculos WHERE id_vehiculo = ? AND identificacion = ?");
            $stmt->execute([$id_referencia, $numero_serie]);
            sendSuccess(['dado_de_baja' => true], "Vehiculo eliminado correctamente");
    }

} catch(PDOException $e) {
    $error = date('Y-m-d H:i:s') . " | EXCEPCION | " . ($id_referencia ?? 'N/A') . " | " . $e->getMessage();
    file_put_contents($archivo_log, $error . PHP_EOL, FILE_APPEND);
    sendError("Error: " . $e->getMessage(), 500);
    exit;
}
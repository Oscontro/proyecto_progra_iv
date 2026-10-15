<?php
require_once 'auth.php';    // reemplaza a conexion.php, ya lo incluye adentro
$user = requireAuth(); 

$archivo_log = __DIR__ . '/logs/errores_importacion.log';

$id_vehiculo = null;

try {
    $pdo = getConnection();
    $pdo->setAttribute(PDO::ATTR_EMULATE_PREPARES, true);
    $pdo->prepare("SET @usuario_actual = ?")->execute([$user['id']]);
    $datos = getJsonInput();

    if (!$datos) {
        sendError("No se recibieron datos", 400);
        exit;
    }

    $id_vehiculo = $datos['id_vehiculo'] ?? null;
    if (!$id_vehiculo) {
        sendError("Falta el id del vehículo", 400);
    }

    $stmt = $pdo->prepare("SELECT de_baja FROM vehiculos WHERE id_vehiculo = ?");
    $stmt->execute([$id_vehiculo]);
    $de_baja = $stmt->fetchColumn();
    if ($de_baja === false) {
        sendError("No existe el vehículo", 404);
    }
    if (!$de_baja) {
        sendError("El vehículo no está en la papelera", 409);
    }

    $pdo->beginTransaction();
    $stmt = $pdo->prepare("CALL sp_restaurar_vehiculo_papelera(?, ?)");
    $stmt->execute([$id_vehiculo,  $user["id"]]);
    $stmt->closeCursor();
    $pdo->commit();
    
    sendSuccess(["success" => true], "Se restauró vehículo correctamente");

} catch (Throwable $e) {
    // Solo hacemos rollback si efectivamente hay una transacción abierta.
    if (isset($pdo) && $pdo->inTransaction()) {
        $pdo->rollBack();
    }

    $linea = date('Y-m-d H:i:s') . " | usuario=" . $user['id']
           . " | restaurar_vehiculo_papelera | id_vehiculo=" . ($id_vehiculo ?? 'N/A')
           . " | " . $e->getMessage();
    @file_put_contents($archivo_log, $linea . PHP_EOL, FILE_APPEND);

    sendError("No se pudo restaurar vehículo, intente nuevamente.", 500);
}
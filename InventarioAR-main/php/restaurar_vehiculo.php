<?php
require_once 'historial_comun.php';    // trae auth.php
$user = requireAuth();

$archivo_log = __DIR__ . '/logs/errores_importacion.log';

$id_vehiculo = null;

try {
    $pdo = getConnection();
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

    // Antes era el procedimiento sp_restaurar_vehiculo_papelera (el hosting
    // no permite procedimientos).
    $pdo->beginTransaction();
    $pdo->prepare("UPDATE vehiculos SET de_baja = FALSE, usuario_modificacion = ? WHERE id_vehiculo = ?")
        ->execute([$user['id'], $id_vehiculo]);
    $pdo->prepare("UPDATE papelera_vehiculos SET puede_restaurar = FALSE WHERE id_vehiculo = ?")->execute([$id_vehiculo]);
    registrarHistorialVehiculo($pdo, (int)$id_vehiculo, $user['id'], 'ALTA DE VEHICULO', 'Vehiculo restaurado');
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
<?php
require_once 'auth.php';    // trae conexion.php y config.php; requireAuth y getJsonInput
$user = requireAuth();

$archivo_log = __DIR__ . '/logs/errores_importacion.log';

$id_vehiculo = null;

try {
    $datos = getJsonInput();
    if (!$datos) {
        sendError("No se recibieron datos", 400);
    }

    $id_vehiculo    = $datos['id_vehiculo'] ?? null;
    $motivo         = $datos['motivo'] ?? null;
    $identificacion = $datos['identificacion'] ?? null;

    if (!$id_vehiculo) {
        sendError("Falta el id del vehículo", 400);
    }

    $pdo = getConnection();
    $pdo->setAttribute(PDO::ATTR_EMULATE_PREPARES, true);  // para el SP

    // Variable de sesión para el trigger (si tu trigger la usa).
    $pdo->prepare("SET @usuario_actual = ?")->execute([$user['id']]);

    $pdo->beginTransaction(); 

    $stmt = $pdo->prepare("CALL sp_enviar_vehiculo_papelera(?, ?, ?, ?)");
    $stmt->execute([$id_vehiculo, $user['id'], $motivo, $identificacion]);  // usuario del token
    $stmt->closeCursor();

    $pdo->commit();

    sendSuccess(['dado_de_baja' => true], "Vehículo dado de baja correctamente");

} catch (Throwable $e) {
    // Solo hacemos rollback si efectivamente hay una transacción abierta.
    if (isset($pdo) && $pdo->inTransaction()) {
        $pdo->rollBack();
    }

    $linea = date('Y-m-d H:i:s') . " | usuario=" . $user['id']
           . " | enviar_vehiculo_papelera | id_vehiculo=" . ($id_vehiculo ?? 'N/A')
           . " | " . $e->getMessage();
    @file_put_contents($archivo_log, $linea . PHP_EOL, FILE_APPEND);

    sendError("No se pudo dar de baja el vehículo. Intente nuevamente.", 500);
}
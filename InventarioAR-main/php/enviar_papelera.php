<?php
require_once 'auth.php';    // trae conexion.php y config.php; requireAuth y getJsonInput
$user = requireAuth();

$archivo_log = __DIR__ . '/logs/errores_importacion.log';

$id_equipo = null;
$numero_serie = null;

try {
    $datos = getJsonInput();
    if (!$datos) {
        sendError("No se recibieron datos", 400);
        exit;
    }

    $id_equipo    = $datos['id_equipo'] ?? null;
    $motivo       = $datos['motivo'] ?? null;
    $numero_serie = $datos['numero_serie'] ?? null;

    if (!$id_equipo) {
        sendError("Falta el id del equipo", 400);
    }

    $pdo = getConnection();
    $pdo->setAttribute(PDO::ATTR_EMULATE_PREPARES, true);
    $pdo->prepare("SET @usuario_actual = ?")->execute([$user['id']]);

    $pdo->beginTransaction();

    // El usuario sale del token, no del cliente.
    $stmt = $pdo->prepare("CALL sp_enviar_a_papelera(?, ?, ?, ?)");
    $stmt->execute([$id_equipo, $user['id'], $motivo, $numero_serie]);
    $stmt->closeCursor();   // libera el cursor del SP antes de confirmar

    $pdo->commit();

    sendSuccess(['enviado' => true], 'Se envió el equipo a la papelera correctamente');

} catch (Throwable $e) {
    // Si la transacción quedó abierta, la deshacemos explícitamente.
    if (isset($pdo) && $pdo->inTransaction()) {
        $pdo->rollBack();
    }

    $linea = date('Y-m-d H:i:s') . " | usuario=" . $user['id']
           . " | enviar_papelera | serie=" . ($numero_serie ?? 'N/A')
           . " | " . $e->getMessage();
    @file_put_contents($archivo_log, $linea . PHP_EOL, FILE_APPEND);

    sendError("No se pudo enviar el equipo a la papelera. Intente nuevamente.", 500);
}
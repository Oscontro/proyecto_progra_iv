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
    }

    $id_equipo = filter_var($datos['id_equipo'] ?? null, FILTER_VALIDATE_INT);
    $motivo    = trim((string)($datos['motivo'] ?? ''));

    if (!$id_equipo) {
        sendError("Falta el id del equipo", 400);
    }

    $pdo = getConnection();
    $pdo->setAttribute(PDO::ATTR_EMULATE_PREPARES, true);

    // Solo se envía a la papelera un equipo del inventario activo. El número
    // de serie que queda registrado sale de la base, no del cliente.
    $stmt = $pdo->prepare("SELECT numero_serie, en_papelera, en_taller FROM equipos WHERE id_equipo = ?");
    $stmt->execute([$id_equipo]);
    $equipo = $stmt->fetch(PDO::FETCH_ASSOC);
    if (!$equipo) {
        sendError("No se encontró el equipo", 404);
    }
    if ($equipo['en_papelera']) {
        sendError("El equipo ya está en la papelera", 409);
    }
    if ($equipo['en_taller']) {
        sendError("El equipo está en taller: no se puede enviar a la papelera", 409);
    }
    $numero_serie = $equipo['numero_serie'];

    $pdo->prepare("SET @usuario_actual = ?")->execute([$user['id']]);

    $pdo->beginTransaction();

    // El usuario sale del token, no del cliente.
    $stmt = $pdo->prepare("CALL sp_enviar_a_papelera(?, ?, ?, ?)");
    $stmt->execute([$id_equipo, $user['id'], $motivo === '' ? null : $motivo, $numero_serie]);
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

    sendError(API_DEBUG ? $e->getMessage() : "No se pudo enviar el equipo a la papelera. Intente nuevamente.", 500);
}

<?php
require_once 'auth.php';    // trae conexion.php y config.php; define requireAuth y getJsonInput
$user = requireAuth();      // ← la identidad sale de acá, verificada contra el token

// Nota: NO repetimos header('Content-Type: application/json').
// Ya lo pone config.php al incluirse. Repetirlo no rompe, pero es ruido.

$archivo_log = __DIR__ . '/logs/errores_importacion.log';

// Declaramos afuera del try para que el catch pueda loguear el id aunque
// la excepción ocurra antes de asignarlo.
$id_equipo = null;

try {
    $datos = getJsonInput();   // el helper ya hace el json_decode y valida que sea array

    if (!$datos) {
        sendError('No se recibieron datos válidos', 400);
    }

    $id_equipo     = $datos['id_equipo'] ?? null;
    $id_taller     = $datos['id_taller'] ?? null;
    $observaciones = $datos['observaciones'] ?? null;
    // id_usuario YA NO se lee del cliente: viene del token ($user['id']).

    if (!$id_equipo || !$id_taller) {
        sendError('Faltan parámetros obligatorios', 400);
    }

    $pdo = getConnection();
    $pdo->setAttribute(PDO::ATTR_EMULATE_PREPARES, true); // necesario para el SP
    $pdo->prepare("SET @usuario_actual = ?")->execute([$user['id']]);

    // ── Transacción: las dos escrituras son una sola operación lógica ──
    // Si el INSERT del estado falla, el CALL del SP no debe quedar aplicado.
    $pdo->beginTransaction();

    // Stored procedure. El usuario sale del token, no del JSON.
    $stmt = $pdo->prepare("CALL sp_enviar_equipo_taller_v4(?, ?, ?, ?)");
    $stmt->execute([(int)$id_equipo, (int)$id_taller, (int)$user['id'], $observaciones]);
    $stmt->closeCursor();

    // Registrar el nuevo estado del equipo (7 = "en taller").
    $estado = 7;
    $pdo->prepare("INSERT INTO equipo_estado (id_equipo, id_estado) VALUES (?, ?)")
        ->execute([(int)$id_equipo, $estado]);

    $pdo->commit();   // ← recién acá se confirman ambas escrituras

    sendSuccess(['enviado' => true], 'Se envió el equipo a taller correctamente');

} catch (PDOException $e) {
    // Si había una transacción abierta, la deshacemos.
    if (isset($pdo) && $pdo->inTransaction()) {
        $pdo->rollBack();
    }

    // El detalle real va al log, para vos. Al cliente le llega algo genérico.
    $linea = date('Y-m-d H:i:s') . " | id_equipo=" . ($id_equipo ?? 'N/A')
           . " | usuario=" . $user['id_usuario'] . " | " . $e->getMessage();
    @file_put_contents($archivo_log, $linea . PHP_EOL, FILE_APPEND);

    sendError('No se pudo enviar el equipo a taller. Intente nuevamente.', 500);
}